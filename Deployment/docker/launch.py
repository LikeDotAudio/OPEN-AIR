#!/usr/bin/env python3
"""Launch OPEN-AIR in Docker — the one-command startup path.

    python3 Deployment/docker/launch.py             # build if needed, start, wait, open browser
    python3 Deployment/docker/launch.py up --logs   # start and tail logs in the foreground
    python3 Deployment/docker/launch.py down        # stop
    python3 Deployment/docker/launch.py status      # what is running, and is it healthy
    python3 Deployment/docker/launch.py logs        # tail
    python3 Deployment/docker/launch.py rebuild     # force a clean image rebuild
    python3 Deployment/docker/launch.py reset       # stop AND delete the retained-state volume

Works from any directory: paths resolve against this file, not your shell.

This wraps `docker compose` rather than replacing it. The value it adds over
typing `docker compose up` is the preflight: it checks that Docker is actually
usable and that the files compose references exist, and it fails with an
instruction instead of a stack trace. A startup path that dies confusingly on a
stranger's machine is the problem this whole script exists to solve.

Stdlib only — no pip install before you can start the thing.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

DOCKER_DIR = Path(__file__).resolve().parent          # Deployment/docker/
# Two levels up, not one: this lives in Deployment/docker/, and REPO_ROOT is the
# build context and the cwd every compose command runs from. Getting it wrong
# points the build at Deployment/ — where FrontEnd/, BackEnd/ and contracts/ do
# not exist — and the preflight then reports the repo's own files as missing.
REPO_ROOT = DOCKER_DIR.parent.parent
COMPOSE_FILE = DOCKER_DIR / "docker-compose.yml"
HOST_NET_FILE = DOCKER_DIR / "docker-compose.host.yml"
HARDWARE_FILE = DOCKER_DIR / "docker-compose.hardware.yml"
UI_URL = "http://localhost:8000"

# Files docker-compose.yml references. Checking them here turns a confusing
# mid-build failure into a one-line message naming the missing file.
REQUIRED = [
    COMPOSE_FILE,
    DOCKER_DIR / "Dockerfile",
    DOCKER_DIR / "mosquitto.conf",
    REPO_ROOT / "Deployment" / "requirements.txt",
    REPO_ROOT / "FrontEnd",
]


# ─────────────────────────── output helpers ───────────────────────────

class C:
    """ANSI colours, disabled when not writing to a terminal."""
    _tty = sys.stdout.isatty()
    GREEN = "\033[32m" if _tty else ""
    RED = "\033[31m" if _tty else ""
    YELLOW = "\033[33m" if _tty else ""
    DIM = "\033[2m" if _tty else ""
    BOLD = "\033[1m" if _tty else ""
    OFF = "\033[0m" if _tty else ""


def ok(msg: str) -> None:
    print(f"  {C.GREEN}✓{C.OFF} {msg}", flush=True)


def fail(msg: str, hint: str = "") -> None:
    # Flush stdout first: without this, buffered stdout and unbuffered stderr
    # interleave and the report reads out of order when piped to a file.
    sys.stdout.flush()
    print(f"  {C.RED}✗{C.OFF} {msg}", file=sys.stderr, flush=True)
    if hint:
        print(f"    {C.DIM}{hint}{C.OFF}", file=sys.stderr, flush=True)


def warn(msg: str) -> None:
    print(f"  {C.YELLOW}!{C.OFF} {msg}", flush=True)


def step(msg: str) -> None:
    print(f"\n{C.BOLD}{msg}{C.OFF}", flush=True)


# ─────────────────────────── docker plumbing ───────────────────────────

# Host networking is the DEFAULT, and `--bridge-net` opts out.
#
# It was opt-in, and that was the wrong default: discovery is what this system
# is for, and none of it works across a docker bridge.
#
#   * mDNS/DNS-SD is multicast (224.0.0.251) — does not cross the bridge, and
#     resolves whatever it does find to the bridge gateway.
#   * SAP is multicast (239.255.255.255) — same.
#   * gPTP and AVDECC are Layer 2, EtherType 0x88F7 / 0x22F0 — the container
#     sees only its own veth, so no amount of CAP_NET_RAW helps. Verified: the
#     bridged container's /sys/class/net contains exactly `eth0` and `lo`.
#
# Every one of those fails *quietly* — an agent that hears nothing looks
# identical to a network with nothing on it. Defaulting to the mode where
# discovery actually works, and requiring a flag to break it, is the honest way
# round.
#
# Security is unchanged: the host overlay binds the broker and the HTTP API to
# 127.0.0.1 explicitly, which replaces the port-mapping confinement the bridge
# setup relied on. See docker-compose.host.yml.
USE_HOST_NET = True
# Set by main() from --hardware. Exposes /dev/snd and /dev/bus/usb so MIDI and
# USB instruments are visible; without it they silently enumerate as zero.
USE_HARDWARE = False


# ─────────────────────────── host diagnostic tools ───────────────────────────
#
# The containerised agents need no host privileges: compose grants the container
# NET_RAW/NET_ADMIN/NET_BIND_SERVICE and the Dockerfile setcaps the binary, so
# PTP and AVB work with no password at all.
#
# These standalone CLIs are different. They run ON the host, outside any
# container, so the kernel needs file capabilities on each binary — and only
# root can set those. That is the one thing in the whole launch that genuinely
# requires elevation, which is why it is asked for explicitly, once, with the
# exact commands shown first.
#
# Declining is fine and non-fatal: the system runs, the tabs populate, you just
# do not get the packet-level views.
HOST_TOOLS = [
    # (crate directory, binary, capabilities, what it is for)
    ("openair-ptp", "ptp-monitor", "cap_net_raw,cap_net_bind_service",
     "live PTPv1/PTPv2/gPTP packet view"),
    ("openair-AVB-Milan", "avdecc-probe", "cap_net_raw,cap_net_admin",
     "find AVB/Milan entities"),
    ("openair-AVB-Milan", "avdecc-identify", "cap_net_raw,cap_net_admin",
     "blink an AVB device's LED"),
]
TOOL_BIN_DIR = Path.home() / ".local" / "bin"

# Inbound UDP the discovery agents must be able to RECEIVE.
#
# Every one of these is multicast listening, not a service we expose. They are
# needed because a host firewall with a default-deny INPUT policy drops them
# silently — and "silently" is the whole problem: an agent that receives
# nothing is indistinguishable from a network with nothing on it.
#
# This bench lost an hour to exactly that. ufw was dropping UDP 319/320, so
# PTPv1 and PTPv2 were invisible while gPTP worked perfectly, because raw
# AF_PACKET capture sits BELOW netfilter and UDP does not. tcpdump (also below
# netfilter) saw the traffic the sockets never got.
#
# NOTE: gPTP and AVDECC need NO rule here for that same reason — they are
# Layer 2 and never reach the IP firewall. Only the UDP-carried protocols do.
DISCOVERY_UDP_PORTS = [
    (319, "PTP event messages (Sync, Delay_Req)"),
    (320, "PTP general messages (Follow_Up, Announce)"),
    (5353, "mDNS/DNS-SD — RAVENNA, Dante, NMOS, Cast, AirPlay, printers"),
    (9875, "SAP — Dante in AES67 mode"),
]
FIREWALL_MARKER = Path.home() / ".cache" / "openair" / "firewall-applied"


def ufw_is_active() -> bool:
    """True when ufw is installed and running.

    Checked without sudo on purpose: `ufw status` needs root, and prompting for
    a password just to discover there is nothing to do is exactly the friction
    this whole path exists to remove.
    """
    if not shutil.which("ufw"):
        return False
    r = subprocess.run(["systemctl", "is-active", "ufw"], capture_output=True, text=True)
    return r.stdout.strip() == "active"


def offer_firewall_fix(assume_yes: bool = False) -> None:
    """Open the discovery ports — asked for ONLY when they are demonstrably shut.

    ufw's rule files are root-only and `sudo -n` needs cached credentials, so
    there is no way to READ the current rules without a password. Bookkeeping
    (a marker file recording what we applied) is not the same thing: it misses
    rules added by hand and goes stale the moment ufw is reset.

    So the check is empirical instead. The PTP agent publishes what it actually
    received, split by transport, and `udp_blocked` is true only when UDP
    sockets opened, Layer 2 traffic IS flowing, and UDP received nothing — the
    unmistakable signature of a firewall, since raw capture sits below netfilter
    and UDP does not.

    Rules present and working -> no prompt, ever. Rules missing -> we can prove
    it before asking.
    """
    if not ufw_is_active():
        return
    ifaces = capture_interfaces()
    if not ifaces:
        return
    ports = ",".join(str(p) for p, _ in DISCOVERY_UDP_PORTS)

    warn("discovery traffic is being dropped by the firewall")
    print("    The PTP agent has Layer 2 traffic flowing but received ZERO UDP.")
    print("    Raw capture sits below netfilter; UDP does not — so this is ufw,")
    print("    not an empty network. Affected: PTPv1/PTPv2, mDNS discovery, SAP.")
    print("    Proposed (inbound UDP only, scoped per interface):")
    for iface in ifaces:
        print(f"      {C.DIM}sudo ufw allow in on {iface} to any port {ports} proto udp{C.OFF}")
    print()

    if not assume_yes:
        try:
            answer = input("  Open these ports now? [Y/n] ").strip().lower()
        except EOFError:
            answer = "n"
        if answer not in ("", "y", "yes"):
            warn("skipped — discovery will stay partial until those ports are open")
            return

    for iface in ifaces:
        r = subprocess.run(
            ["sudo", "ufw", "allow", "in", "on", iface,
             "to", "any", "port", ports, "proto", "udp"],
            capture_output=True, text=True,
        )
        if r.returncode != 0:
            warn(f"ufw rule failed on {iface}: {r.stderr.strip()}")
            return
    ok(f"discovery ports opened on {', '.join(ifaces)} — restart to pick them up")


def capture_interfaces() -> list[str]:
    """Physical interfaces the agents listen on — the ones worth scoping to."""
    out = []
    net = Path("/sys/class/net")
    if not net.is_dir():
        return out
    for iface in sorted(p.name for p in net.iterdir()):
        if iface == "lo" or iface.startswith(("br-", "docker", "veth", "virbr")):
            continue
        try:
            if (net / iface / "operstate").read_text().strip() == "up":
                out.append(iface)
        except OSError:
            continue
    return out


def tool_needs_caps(path: Path, wanted: str) -> bool:
    """True when the binary is missing its capabilities (so sudo is warranted)."""
    if not path.exists():
        return True
    try:
        out = subprocess.run(["getcap", str(path)], capture_output=True, text=True).stdout
    except FileNotFoundError:
        return True   # no getcap: assume it needs doing rather than skip silently
    return not all(cap in out for cap in wanted.split(","))


def install_host_tools(assume_yes: bool = False) -> None:
    """Build the diagnostic CLIs and grant them capabilities, asking once.

    Ordering matters: everything that does NOT need a password happens first, so
    the prompt appears only if there is genuinely something to elevate for.
    """
    protocols = REPO_ROOT / "BackEnd" / "ComProtocols"
    if not shutil.which("cargo"):
        return  # No Rust toolchain: the container path still works.

    pending = []
    for crate, binary, caps, purpose in HOST_TOOLS:
        if (protocols / crate).is_dir():
            pending.append((crate, binary, caps, purpose))
    if not pending:
        return

    step("Host diagnostic tools")
    print("  Optional CLIs that read raw packets directly on this machine:")
    for _, binary, _, purpose in pending:
        print(f"    {C.BOLD}{binary}{C.OFF} — {purpose}")
    print(f"  {C.DIM}The containerised agents do NOT need this; it is for the packet views.{C.OFF}")

    TOOL_BIN_DIR.mkdir(parents=True, exist_ok=True)
    built = []
    for crate, binary, caps, _ in pending:
        dest = TOOL_BIN_DIR / binary
        if not tool_needs_caps(dest, caps):
            continue
        r = subprocess.run(
            ["cargo", "build", "--release", "--bin", binary],
            cwd=protocols / crate, capture_output=True, text=True,
        )
        if r.returncode != 0:
            warn(f"could not build {binary} — skipping")
            continue
        src = protocols / crate / "target" / "release" / binary
        if not src.exists():
            src = protocols / "target" / "release" / binary
        if not src.exists():
            warn(f"built {binary} but cannot find the binary — skipping")
            continue
        shutil.copy2(src, dest)
        built.append((dest, caps))

    if not built:
        ok(f"diagnostic tools already installed in {TOOL_BIN_DIR}")
        return

    # THE one elevation in the whole launch. Both jobs go through it together,
    # so there is never a second prompt.
    print()
    print(f"  {C.BOLD}Administrator password needed — once.{C.OFF}")
    print("  Raw packet capture and binding ports 319/320 are privileged. Granting")
    print("  each binary its own file capability avoids running the tools as root.")
    print("  Exactly these commands will run:")
    for dest, caps in built:
        print(f"    {C.DIM}sudo setcap {caps}+eip {dest}{C.OFF}")
    print(f"  {C.DIM}Skip with: --skip-tools (everything else still works){C.OFF}")
    print()

    if not assume_yes:
        try:
            answer = input("  Grant capabilities now? [Y/n] ").strip().lower()
        except EOFError:
            answer = "n"
        if answer not in ("", "y", "yes"):
            warn("skipped — run the setcap commands above yourself when you want them")
            return

    for dest, caps in built:
        r = subprocess.run(["sudo", "setcap", f"{caps}+eip", str(dest)])
        if r.returncode != 0:
            warn(f"setcap failed for {dest.name}; run it manually when convenient")
            return

    ok(f"diagnostic tools ready in {TOOL_BIN_DIR}")
    if str(TOOL_BIN_DIR) not in os.environ.get("PATH", ""):
        print(f"  {C.DIM}Add to PATH: export PATH=\"$HOME/.local/bin:$PATH\"{C.OFF}")


# ─────────────────────────── image staleness ───────────────────────────
#
# `up` reuses whatever image already exists. That is fast and almost always
# right — but it means editing the Dockerfile or any Rust source and re-running
# launch gives you the OLD binary, with no indication anything was skipped.
#
# This is not hypothetical: adding cap_net_bind_service to the Dockerfile and
# re-launching produced a container whose bounding set had the capability and
# whose binary did not, so the PTP agent kept reporting "permission denied" on
# ports 319/320 while AVB (which needed only the older cap_net_raw) worked fine.
# A half-working system with no error is the worst failure mode there is.
#
# So: compare the image's creation time against everything baked into it, and
# rebuild automatically when it is behind.
IMAGE_NAME = "openair-orchestrator"
BUILD_INPUT_SUFFIXES = (".rs",)
BUILD_INPUT_NAMES = {"Cargo.toml", "Cargo.lock", "Dockerfile", "docker-compose.yml"}


def newest_build_input() -> tuple[float, Path | None]:
    """Newest mtime among the sources compiled into the image."""
    newest_t, newest_p = 0.0, None
    for path in (DOCKER_DIR / "Dockerfile", COMPOSE_FILE):
        if path.exists() and path.stat().st_mtime > newest_t:
            newest_t, newest_p = path.stat().st_mtime, path
    for base in (REPO_ROOT / "BackEnd", REPO_ROOT / "contracts"):
        if not base.is_dir():
            continue
        for root, dirs, files in os.walk(base):
            # Pruning `target` matters for speed AND correctness: build output
            # is always newer than its sources and would make every image look
            # stale forever.
            dirs[:] = [d for d in dirs if d not in ("target", "node_modules", ".git")]
            for name in files:
                if name.endswith(BUILD_INPUT_SUFFIXES) or name in BUILD_INPUT_NAMES:
                    fp = Path(root) / name
                    try:
                        t = fp.stat().st_mtime
                    except OSError:
                        continue
                    if t > newest_t:
                        newest_t, newest_p = t, fp
    return newest_t, newest_p


def image_created_epoch() -> float | None:
    """When the orchestrator image was built, or None if it does not exist."""
    r = subprocess.run(
        ["docker", "image", "inspect", IMAGE_NAME, "--format", "{{.Created}}"],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        return None
    raw = r.stdout.strip()
    # Docker emits nanosecond precision; fromisoformat wants microseconds.
    if "." in raw:
        head, _, tail = raw.partition(".")
        digits = "".join(c for c in tail if c.isdigit())[:6]
        rest = tail[len(tail) - len(tail.lstrip("0123456789")):]
        raw = f"{head}.{digits}{rest}"
    try:
        from datetime import datetime
        return datetime.fromisoformat(raw).timestamp()
    except ValueError:
        return None


def needs_rebuild() -> tuple[bool, str]:
    """(should rebuild, why)."""
    created = image_created_epoch()
    if created is None:
        return True, "no image yet — first build"
    newest_t, newest_p = newest_build_input()
    if newest_t > created:
        rel = newest_p.relative_to(REPO_ROOT) if newest_p else "sources"
        age = time.strftime("%H:%M:%S", time.localtime(newest_t))
        img = time.strftime("%H:%M:%S", time.localtime(created))
        return True, f"{rel} changed at {age}, image built {img}"
    return False, ""


def compose_cmd() -> list[str] | None:
    """Return the working compose invocation, or None.

    Prefers the v2 plugin (`docker compose`); falls back to standalone
    `docker-compose` for older installs. Always carries an explicit `-f`, since
    the compose file lives in docker/ rather than the directory commands run from.
    """
    base = None
    if shutil.which("docker"):
        r = subprocess.run(["docker", "compose", "version"],
                           capture_output=True, text=True)
        if r.returncode == 0:
            base = ["docker", "compose"]
    if base is None and shutil.which("docker-compose"):
        base = ["docker-compose"]
    if base is None:
        return None
    files = ["-f", str(COMPOSE_FILE)]
    if USE_HOST_NET:
        files += ["-f", str(HOST_NET_FILE)]
    if USE_HARDWARE:
        files += ["-f", str(HARDWARE_FILE)]
    return base + files


def preflight() -> list[str] | None:
    """Verify Docker is usable and compose's inputs exist.

    Returns the compose command on success, or None on failure (having already
    explained what is wrong). main() turns that into an exit code — see
    check_ports() for why nothing here calls sys.exit() directly.
    """
    step("Preflight")

    if not shutil.which("docker"):
        fail("docker is not installed",
             "Install Docker Desktop, or on Debian/Ubuntu: sudo apt install docker.io docker-compose-v2")
        return None
    ok("docker found")

    # A stopped daemon is the single most common failure, and its native error
    # message ("Cannot connect to the Docker daemon") does not tell you what to do.
    probe = subprocess.run(["docker", "info"], capture_output=True, text=True)
    if probe.returncode != 0:
        detail = (probe.stderr or "").strip().splitlines()
        hint = "Start Docker Desktop, or: sudo systemctl start docker"
        if "permission denied" in (probe.stderr or "").lower():
            hint = ("Your user cannot reach the Docker socket. Either run with sudo, or:\n"
                    "      sudo usermod -aG docker $USER   # then log out and back in")
        fail("the Docker daemon is not reachable", hint)
        if detail:
            print(f"    {C.DIM}{detail[0]}{C.OFF}", file=sys.stderr)
        return None
    ok("docker daemon is running")

    cc = compose_cmd()
    if cc is None:
        fail("docker compose is not available",
             "Install the plugin: sudo apt install docker-compose-v2")
        return None
    ok(f"compose: {' '.join(cc)}")

    missing = [p for p in REQUIRED if not p.exists()]
    if missing:
        fail("files referenced by docker-compose.yml are missing")
        for p in missing:
            print(f"      {p.relative_to(REPO_ROOT)}", file=sys.stderr)
        print("    Are you running this from a complete checkout?", file=sys.stderr)
        return None
    ok(f"{len(REQUIRED)} required paths present")

    if not check_ports(cc):
        return None

    # Catch a malformed compose file before spending minutes on a build.
    r = run(cc + ["config"], capture=True)
    if r.returncode != 0:
        fail("docker-compose.yml is not valid")
        print((r.stderr or "").strip(), file=sys.stderr)
        return None
    ok("docker-compose.yml validates")

    return cc


# Ports compose publishes on the host. A conflict here surfaces from the daemon
# as "failed to bind host port … address already in use", which does not say what
# is holding it or what to do — so check first and name the culprit.
PORTS = [(1883, "MQTT broker"), (9001, "MQTT over WebSockets"), (8000, "orchestrator / UI")]


def port_in_use(port: int) -> bool:
    """True if something is already listening on this port on loopback."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def port_holder(port: int) -> str:
    """Best-effort name of the process holding a port.

    Returns "" when it cannot be determined — which is the *normal* case for a
    process owned by another user: `ss -ltnp` silently omits the `users:((...))`
    field without root, and lsof is often not installed. Never guess from column
    position; the ss State column ("LISTEN") is not a process name.
    """
    if shutil.which("ss"):
        r = subprocess.run(["ss", "-ltnp"], capture_output=True, text=True)
        for line in (r.stdout or "").splitlines():
            if f":{port} " in line and "users:((" in line:
                try:
                    return line.split('users:((')[1].split('"')[1]
                except IndexError:
                    pass
    if shutil.which("lsof"):
        r = subprocess.run(["lsof", "-nP", f"-i:{port}", "-sTCP:LISTEN"],
                           capture_output=True, text=True)
        for line in (r.stdout or "").splitlines()[1:]:
            parts = line.split()
            if parts:
                return parts[0]
    return ""


def check_ports(cc: list[str]) -> bool:
    """Fail early and specifically when a published port is already taken.

    Returns False rather than exiting: a helper that calls sys.exit() is
    untestable and shows up as a trapped SystemExit under a debugger. Exit codes
    are decided once, in main().
    """
    if USE_HOST_NET:
        # No port mapping exists in host mode, so a busy port is not a compose
        # conflict — it is just something already bound, which the broker or
        # orchestrator will report itself if it matters.
        ok("host networking — no published ports to conflict")
        return True

    busy = [(p, what) for p, what in PORTS if port_in_use(p)]
    if not busy:
        ok(f"ports free: {', '.join(str(p) for p, _ in PORTS)}")
        return True

    # OUR OWN containers hold these ports when the stack is already up. That is
    # not a conflict — `compose up` is idempotent — so do not block on it. Without
    # this, running the launcher twice reports a bogus port clash and tells you to
    # kill a mosquitto that is your own container.
    running = [c for c in container_status(cc)
               if (c.get("State") or "").lower() == "running"]
    if running:
        ok(f"ports held by this project's own containers "
           f"({', '.join(c.get('Service') or c.get('Name') or '?' for c in running)}) — already up")
        return True

    fail("ports already in use — compose cannot publish them")
    for p, what in busy:
        holder = port_holder(p)
        who = f" (held by: {holder})" if holder else ""
        print(f"      {p}  {what}{who}", file=sys.stderr)

    names = {port_holder(p) for p, _ in busy}
    busy_ports = {p for p, _ in busy}
    print("", file=sys.stderr)
    # Key the hint off the PORTS, not the process name: the name is usually
    # unavailable without root, and 1883/9001 are mosquitto's by convention.
    known = {n for n in names if n}
    # Only reach for the mosquitto advice when we could NOT identify the holder,
    # or when it really is mosquitto. Naming the wrong culprit is worse than
    # saying nothing — it sends people to kill a service that is not the problem.
    if any("mosquitto" in n for n in known) or (not known and busy_ports & {1883, 9001}):
        print("    1883/9001 are the broker's ports — a mosquitto is almost certainly"
              "\n    already running on this host, and the container broker cannot bind"
              "\n    the same ports. Stop the host one:", file=sys.stderr)
        print(f"      {C.BOLD}sudo systemctl stop mosquitto{C.OFF}"
              "        # if installed as a service", file=sys.stderr)
        print("      pkill mosquitto                      # if started by hand",
              file=sys.stderr)
        print("\n    Note: a mosquitto installed as a system service reads"
              " /etc/mosquitto/mosquitto.conf,\n    NOT this repo's broker/mosquitto.conf — so"
              " restarting it will not pick up\n    our loopback binding. Stop it and let the"
              " container broker take over, or\n    edit the system config directly.",
              file=sys.stderr)
    else:
        who = ", ".join(sorted(known)) if known else "the process above"
        print(f"    Held by {who} — not this project. Stop it, or change the published"
              "\n    ports in Deployment/docker/docker-compose.yml.", file=sys.stderr)
    return False


def compose_env() -> dict:
    """Environment for compose: the host uid/gid the container should run as.

    Without this the container runs as root and every file it writes through the
    bind mount (discovered panels, editor saves) lands root-owned in the working
    tree — breaking git and any host-side tooling.
    """
    env = dict(os.environ)
    env.setdefault("OPENAIR_UID", str(os.getuid()))
    env.setdefault("OPENAIR_GID", str(os.getgid()))
    return env


def run(cmd: list[str], capture: bool = False, check: bool = False):
    """Run a command from the repo root."""
    return subprocess.run(
        cmd, cwd=REPO_ROOT, text=True, check=check,
        capture_output=capture, env=compose_env(),
    )


# ─────────────────────────── health ───────────────────────────

def http_ok(url: str, timeout: float = 2.0) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return 200 <= r.status < 400
    except (urllib.error.URLError, OSError):
        return False


def wait_until_up(seconds: int) -> bool:
    """Poll the health endpoint until the orchestrator answers."""
    step(f"Waiting for the orchestrator (up to {seconds}s)")
    health = f"{UI_URL}/api/health"
    deadline = time.time() + seconds
    spinner = "|/-\\"
    i = 0
    while time.time() < deadline:
        if http_ok(health):
            print(f"\r  {C.GREEN}✓{C.OFF} orchestrator is answering on {UI_URL}      ")
            return True
        if sys.stdout.isatty():
            left = int(deadline - time.time())
            print(f"\r  {spinner[i % 4]} starting… {left}s left ", end="", flush=True)
        i += 1
        time.sleep(1)
    print(f"\r  {C.YELLOW}!{C.OFF} no response from {health} yet            ")
    return False


def container_status(cc: list[str]) -> list[dict]:
    """Structured `compose ps`. Tolerates older formats that emit one JSON object per line."""
    r = run(cc + ["ps", "--format", "json"], capture=True)
    if r.returncode != 0 or not (r.stdout or "").strip():
        return []
    out = r.stdout.strip()
    try:
        data = json.loads(out)
        return data if isinstance(data, list) else [data]
    except json.JSONDecodeError:
        rows = []
        for line in out.splitlines():
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return rows


def print_status(cc: list[str]) -> None:
    rows = container_status(cc)
    if not rows:
        warn("no containers running")
        return
    for c in rows:
        name = c.get("Name") or c.get("Service") or "?"
        state = (c.get("State") or "?").lower()
        health = c.get("Health") or ""
        mark = C.GREEN + "✓" + C.OFF if state == "running" else C.YELLOW + "!" + C.OFF
        suffix = f" ({health})" if health else ""
        print(f"  {mark} {name}: {state}{suffix}")


# ─────────────────────────── commands ───────────────────────────

def clear_name_conflicts(cc: list[str]) -> None:
    """Remove orphaned containers holding our `container_name:` values.

    A failed `up` (a port clash, a bad build) can leave a container behind that
    still owns the name. Compose then cannot reuse it and silently creates
    `<hash>_openair-orchestrator` instead — the stack works but every `docker
    exec openair-orchestrator` fails, and the mangled name is easy to miss in
    the output. Reaping them first keeps the names stable.
    """
    wanted = {"openair-orchestrator", "openair-broker"}
    live = {c.get("Name") for c in container_status(cc)
            if (c.get("State") or "").lower() == "running"}
    r = subprocess.run(
        ["docker", "ps", "-a", "--format", "{{.Names}}"],
        capture_output=True, text=True, env=compose_env(),
    )
    stale = [
        n for n in (r.stdout or "").split()
        # e.g. "e7d014f9165b_openair-orchestrator" — compose's fallback name
        if any(n.endswith(f"_{w}") for w in wanted) and n not in live
    ]
    if stale:
        warn(f"removing {len(stale)} orphaned container(s) holding our names")
        for n in stale:
            print(f"    {n}")
        subprocess.run(["docker", "rm", "-f", *stale],
                       capture_output=True, text=True, env=compose_env())


def report_agent_health(timeout: float = 6.0) -> bool:
    """Ask the agents on the bus whether they can actually see the network.

    The orchestrator answering on :8000 only proves the HTTP server is up. It
    says nothing about whether the discovery agents can hear anything — and the
    failure modes that matter here (missing capability, firewall drop, bridged
    network) all produce a perfectly healthy-looking orchestrator serving an
    empty Discovered tab.

    Agents that can self-assess publish `.../Agent/state`; this surfaces any
    that are not fully listening, with the detail they reported.

    Returns True when the PTP agent reports its UDP is firewall-blocked.
    """
    try:
        import paho.mqtt.client as mqtt   # optional: never block a launch on it
    except ImportError:
        return False

    states: dict[str, str] = {}
    details: dict[str, str] = {}

    def on_connect(c, u, f, rc, properties=None):
        c.subscribe("OpenAir/System/Protocols/+/Agent/#")

    def on_message(c, u, msg):
        parts = msg.topic.split("/")
        proto, leaf = parts[3], parts[-1]
        payload = msg.payload.decode(errors="replace").strip()
        if leaf == "state":
            states[proto] = payload
        elif leaf == "udp_blocked" and proto == "ptp":
            details["__ptp_udp_blocked__"] = payload
        elif leaf == "detail":
            details[proto] = payload

    try:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    except Exception:
        client = mqtt.Client()
    client.on_connect, client.on_message = on_connect, on_message
    try:
        client.connect("127.0.0.1", 1883, 5)
    except Exception:
        return False
    client.loop_start()
    time.sleep(timeout)
    client.loop_stop()

    if not states:
        return False

    degraded = {p: st for p, st in states.items() if st != "listening"}
    if degraded:
        warn("some discovery agents are not fully listening")
        for proto, state in sorted(degraded.items()):
            print(f"    {C.BOLD}{proto}{C.OFF}: {state}")
            detail = details.get(proto, "")
            if detail:
                print(f"      {C.DIM}{detail.splitlines()[0][:120]}{C.OFF}")
    else:
        ok(f"discovery agents listening: {', '.join(sorted(states))}")

    # The firewall verdict, computed by the agent that can actually see the
    # split. Absent means it has not flushed yet — say nothing rather than
    # guess, since a wrong accusation here costs a needless password prompt.
    return details.get("__ptp_udp_blocked__") == "true"


def cmd_up(args, cc: list[str]) -> int:
    clear_name_conflicts(cc)
    step("Starting OPEN-AIR")
    up = cc + ["up", "-d"]
    rebuild = bool(args.rebuild)
    if not rebuild and not getattr(args, "no_auto_rebuild", False):
        stale, why = needs_rebuild()
        if stale:
            warn(f"image is out of date — rebuilding ({why})")
            print("    Reusing it would run the previous binary against the new")
            print("    config, which fails silently rather than loudly.")
            print(f"    {C.DIM}Skip with --no-auto-rebuild if you know it does not matter.{C.OFF}")
            rebuild = True
    if rebuild:
        up.append("--build")
    if run(up).returncode != 0:
        fail("docker compose up failed", "Re-run with `logs` to see why.")
        return 1

    step("Containers")
    print_status(cc)

    healthy = wait_until_up(args.timeout)

    if healthy:
        step("Discovery health")
        # 12s: the PTP agent's first flush lands at 10s, and its reception
        # counters are what make the firewall check evidence-based.
        if report_agent_health(timeout=12.0) and not getattr(args, "skip_tools", False):
            offer_firewall_fix(assume_yes=bool(getattr(args, "yes", False)))

        step("Ready")
        print(f"  {C.BOLD}{UI_URL}{C.OFF}")
        print(f"  {C.DIM}Bus:   mosquitto_sub -h localhost -t 'OpenAir/#' -v{C.OFF}")
        print(f"  {C.DIM}Alive: mosquitto_sub -h localhost -t 'OpenAir/System/Agents/#' -v{C.OFF}")
        print(f"  {C.DIM}Stop:  python3 Deployment/docker/launch.py down{C.OFF}")
        if not args.no_browser:
            try:
                webbrowser.open(UI_URL)
            except Exception:
                pass
    else:
        warn("containers are up but the orchestrator has not answered yet")
        print(f"    {C.DIM}It may still be starting. Check with:{C.OFF}")
        print(f"    {C.DIM}  python3 Deployment/docker/launch.py logs{C.OFF}")

    if args.logs:
        step("Logs (Ctrl-C to stop tailing; containers keep running)")
        try:
            run(cc + ["logs", "-f", "--tail", "50"])
        except KeyboardInterrupt:
            print("\n  (containers still running)")
    return 0 if healthy else 1


def cmd_down(args, cc: list[str]) -> int:
    step("Stopping OPEN-AIR")
    cmd = cc + ["down"]
    if args.volumes:
        # Retained MQTT topics are the system's state store, so dropping the
        # volume is a real data loss, not a cache clear. Hence the separate flag.
        cmd.append("-v")
        warn("also deleting the broker volume — retained state will be lost")
    rc = run(cmd).returncode
    ok("stopped" if rc == 0 else "docker compose down returned an error")
    return rc


def cmd_logs(args, cc: list[str]) -> int:
    try:
        return run(cc + ["logs", "-f", "--tail", str(args.tail)]).returncode
    except KeyboardInterrupt:
        return 0


def cmd_status(args, cc: list[str]) -> int:
    step("Containers")
    print_status(cc)
    step("Endpoints")
    for label, url in (("UI", UI_URL), ("health", f"{UI_URL}/api/health")):
        if http_ok(url):
            ok(f"{label}: {url}")
        else:
            fail(f"{label}: {url} not answering")
    return 0


def cmd_rebuild(args, cc: list[str]) -> int:
    step("Rebuilding images (no cache)")
    if run(cc + ["build", "--no-cache"]).returncode != 0:
        fail("build failed")
        return 1
    ok("images rebuilt")
    args.rebuild = False
    return cmd_up(args, cc)


def main() -> int:
    p = argparse.ArgumentParser(
        prog="launch.py",
        description="Launch OPEN-AIR in Docker.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("\n\n", 1)[1],
    )
    sub = p.add_subparsers(dest="command")

    def add_up_flags(sp):
        sp.add_argument("--logs", action="store_true", help="tail logs after starting")
        sp.add_argument("--no-browser", action="store_true", help="do not open a browser")
        sp.add_argument("--rebuild", action="store_true", help="pass --build to compose up")
        sp.add_argument("--hardware", action="store_true",
                        help="expose /dev/snd and /dev/bus/usb so MIDI and USB (USBTMC) "
                             "instruments are visible. Without it they enumerate as zero, "
                             "which looks identical to nothing being plugged in.")
        # Kept as an accepted no-op: it is in the README, in shell history, and
        # in muscle memory. Silently doing nothing is right — it asks for the
        # behaviour that is now default.
        sp.add_argument("--host-net", action="store_true",
                        help="(default; kept for compatibility) share the host network stack")
        sp.add_argument("--bridge-net", action="store_true",
                        help="opt OUT of host networking, back onto the docker bridge. "
                             "Outbound TCP still works, so VISA/SCPI is fine — but mDNS, "
                             "SAP, gPTP and AVDECC discovery all go silent.")
        sp.add_argument("--no-auto-rebuild", action="store_true",
                        help="do not rebuild even when sources are newer than the image")
        sp.add_argument("--skip-tools", action="store_true",
                        help="do not build/setcap the host diagnostic CLIs "
                             "(skips the one password prompt)")
        sp.add_argument("--yes", "-y", action="store_true",
                        help="assume yes for the capability prompt")
        sp.add_argument("--timeout", type=int, default=120,
                        help="seconds to wait for the orchestrator (default 120; a cold "
                             "Rust build inside the image can take a while)")

    add_up_flags(sub.add_parser("up", help="start (default)"))

    sp_down = sub.add_parser("down", help="stop")
    sp_down.add_argument("-v", "--volumes", action="store_true",
                         help="also delete the broker volume (loses retained state)")

    sub.add_parser("status", help="show container and endpoint health")

    sp_logs = sub.add_parser("logs", help="tail logs")
    sp_logs.add_argument("--tail", type=int, default=100)

    add_up_flags(sub.add_parser("rebuild", help="rebuild images from scratch, then start"))

    sp_reset = sub.add_parser("reset", help="stop and delete the broker volume")
    sp_reset.set_defaults(volumes=True)

    args = p.parse_args()

    # Bare invocation means "start it" — the common case should need no argument.
    if args.command is None:
        args = p.parse_args(["up"])

    global USE_HOST_NET, USE_HARDWARE
    USE_HOST_NET = not bool(getattr(args, "bridge_net", False))
    USE_HARDWARE = bool(getattr(args, "hardware", False))
    if USE_HARDWARE:
        if not HARDWARE_FILE.exists():
            fail(f"missing {HARDWARE_FILE.name}")
            return 1
        step("Local hardware enabled")
        print("  /dev/snd (MIDI) and /dev/bus/usb (USBTMC) exposed to the container.")
    if USE_HOST_NET:
        if not HOST_NET_FILE.exists():
            fail(f"missing {HOST_NET_FILE.name}")
            return 1
        step("Host networking (default)")
        print("  Containers share the host network stack, so mDNS/SAP multicast and")
        print("  Layer 2 discovery (gPTP, AVDECC) see the real LAN.")
        print(f"  {C.DIM}Broker and HTTP API stay bound to 127.0.0.1. Opt out: --bridge-net{C.OFF}")
    else:
        warn("bridge networking — discovery will not see the LAN")
        print("    mDNS/DNS-SD, SAP, gPTP and AVDECC all go silent on the bridge;")
        print("    each fails quietly, looking like an empty network. VISA/SCPI is")
        print("    unaffected. Drop --bridge-net to restore discovery.")

    cc = preflight()
    if cc is None:
        return 1

    # After preflight (so a broken docker fails first) and before starting, so
    # the tools are ready by the time there is traffic to point them at.
    if args.command in ("up", "rebuild") and not getattr(args, "skip_tools", False):
        try:
            install_host_tools(assume_yes=bool(getattr(args, "yes", False)))
        except KeyboardInterrupt:
            warn("skipped host tools")

    handlers = {
        "up": cmd_up,
        "down": cmd_down,
        "logs": cmd_logs,
        "status": cmd_status,
        "rebuild": cmd_rebuild,
        "reset": cmd_down,
    }
    return handlers[args.command](args, cc)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\ninterrupted")
        raise SystemExit(130)
