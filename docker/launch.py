#!/usr/bin/env python3
"""Launch OPEN-AIR in Docker — the one-command startup path.

    python3 docker/launch.py             # build if needed, start, wait, open browser
    python3 docker/launch.py up --logs   # start and tail logs in the foreground
    python3 docker/launch.py down        # stop
    python3 docker/launch.py status      # what is running, and is it healthy
    python3 docker/launch.py logs        # tail
    python3 docker/launch.py rebuild     # force a clean image rebuild
    python3 docker/launch.py reset       # stop AND delete the retained-state volume

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
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

DOCKER_DIR = Path(__file__).resolve().parent          # docker/
REPO_ROOT = DOCKER_DIR.parent
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

# Set by main() from --host-net. Host networking is required for mDNS/DNS-SD
# discovery to see the LAN: multicast does not cross a docker bridge.
USE_HOST_NET = False
# Set by main() from --hardware. Exposes /dev/snd and /dev/bus/usb so MIDI and
# USB instruments are visible; without it they silently enumerate as zero.
USE_HARDWARE = False


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
              "\n    ports in docker/docker-compose.yml.", file=sys.stderr)
    return False


def run(cmd: list[str], capture: bool = False, check: bool = False):
    """Run a command from the repo root."""
    return subprocess.run(
        cmd, cwd=REPO_ROOT, text=True, check=check,
        capture_output=capture,
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

def cmd_up(args, cc: list[str]) -> int:
    step("Starting OPEN-AIR")
    up = cc + ["up", "-d"]
    if args.rebuild:
        up.append("--build")
    if run(up).returncode != 0:
        fail("docker compose up failed", "Re-run with `logs` to see why.")
        return 1

    step("Containers")
    print_status(cc)

    healthy = wait_until_up(args.timeout)

    if healthy:
        step("Ready")
        print(f"  {C.BOLD}{UI_URL}{C.OFF}")
        print(f"  {C.DIM}Bus:   mosquitto_sub -h localhost -t 'OpenAir/#' -v{C.OFF}")
        print(f"  {C.DIM}Alive: mosquitto_sub -h localhost -t 'OpenAir/System/Agents/#' -v{C.OFF}")
        print(f"  {C.DIM}Stop:  python3 docker/launch.py down{C.OFF}")
        if not args.no_browser:
            try:
                webbrowser.open(UI_URL)
            except Exception:
                pass
    else:
        warn("containers are up but the orchestrator has not answered yet")
        print(f"    {C.DIM}It may still be starting. Check with:{C.OFF}")
        print(f"    {C.DIM}  python3 docker/launch.py logs{C.OFF}")

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
        sp.add_argument("--host-net", action="store_true",
                        help="share the host network stack. REQUIRED for mDNS/DNS-SD "
                             "discovery to see LAN devices — multicast does not cross "
                             "the docker bridge. Everything stays bound to loopback.")
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
    USE_HOST_NET = bool(getattr(args, "host_net", False))
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
        step("Host networking enabled")
        print("  Containers share the host network stack, so mDNS/DNS-SD sees the")
        print("  real LAN. Broker and HTTP API stay bound to 127.0.0.1.")

    cc = preflight()
    if cc is None:
        return 1

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
