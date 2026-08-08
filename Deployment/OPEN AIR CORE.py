# ==========================================
# Header: OPEN AIR CORE.py
# Purpose: Full cold start — builds the Rust core, brings up the broker and every agent.
# Description: THE kick-off. Use 'OPENAIR FRONT END.py' to open the site
#              again without rebuilding or rescanning the bench.
# 
# Version: 26.08.07.2
# Change Log:
# - 2026-07-05: Initial annotation and documentation added.
# - 2026-08-07: Stop running OPEN-AIR containers and start a host mosquitto in their
#               place, so a bare-metal run always owns the whole stack
#               (--ignore-docker leaves containers alone).
# ==========================================

#!/usr/bin/env python3
"""Full cold start for OPEN-AIR — builds everything, then hands over to Rust.

This is the launcher that owns the dependencies: cargo builds, the MQTT broker,
yak, and the orchestrator (which scans the bench). For the common case of just
wanting the site back, use `OPENAIR FRONT END.py`, which skips both the build
and the scan.
"""
import os
import shutil
import subprocess
import sys
import time

import socket

# The broker the orchestrator, yak and every agent connect to. Loopback-only:
# see broker/mosquitto.conf and the SECURITY note in docker-compose.host.yml.
BROKER_HOST = "127.0.0.1"
BROKER_PORT = 1883

# Inline comment: Logic for get_local_ip
def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        return s.getsockname()[0]
    except Exception:
        return '127.0.0.1'
    finally:
        s.close()

# Inline comment: Logic for running_openair_containers
def running_openair_containers():
    """Names+status of running OPEN-AIR containers, or [] if Docker is absent.

    The launcher's cleanup (pkill / fuser / lsof) cannot touch container
    processes — they live in another namespace, so pkill returns EPERM and the
    port stays held. Without this check the boot gets all the way to
    TcpListener::bind before failing with EADDRINUSE, by which point every
    agent has already connected to the broker the container is also using.
    """
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=openair", "--format", "{{.Names}}\t{{.Status}}"],
            capture_output=True, text=True, timeout=10,
        )
    except (FileNotFoundError, OSError, subprocess.SubprocessError):
        return []  # No docker installed / daemon down — bare-metal run is fine.
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]

# Inline comment: Logic for stop_openair_containers
def stop_openair_containers(entries):
    """docker stop every OPEN-AIR container. Returns True if all of them went down.

    `docker stop` rather than `compose down`: the running set is discovered from
    `docker ps`, so this works no matter which overlay combination started them
    (host / dev / hardware), and it leaves the containers and the broker-data
    volume intact for a later `docker compose up`.
    """
    names = [entry.partition("\t")[0] for entry in entries]
    print("🐳 [LAUNCHER] Stopping conflicting containers...", flush=True)
    result = subprocess.run(
        ["docker", "stop"] + names, capture_output=True, text=True, timeout=90,
    )
    if result.returncode != 0:
        print(f"   ❌ docker stop failed: {result.stderr.strip()}", file=sys.stderr)
        return False
    for name in names:
        print(f"   ⏹  {name}  (stopped)", flush=True)
    return True

# Inline comment: Logic for port_is_listening
def port_is_listening(host, port, timeout=0.5):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        return s.connect_ex((host, port)) == 0

# Inline comment: Logic for host_broker_config
def host_broker_config(root):
    """Write a runtime mosquitto.conf derived from the repo's bare-metal config.

    broker/mosquitto.conf is the source of truth for the listeners and the
    anonymous/ACL posture — it must not be duplicated here, or a future security
    change made there would silently not apply to host runs. The one line that
    cannot survive is persistence_location: it points at /var/lib/mosquitto/,
    which is owned by the `mosquitto` user, so a broker running as the invoking
    user cannot write its retained-state database there. Retained state matters
    (protocol configs and agent heartbeats are all retained), so it is redirected
    to a per-user state dir that persists across runs rather than disabled.
    """
    source = os.path.join(root, "broker", "mosquitto.conf")
    if not os.path.exists(source):
        return None, None

    state_home = os.environ.get("XDG_STATE_HOME") or os.path.expanduser("~/.local/state")
    data_dir = os.path.join(state_home, "openair", "broker")
    os.makedirs(data_dir, exist_ok=True)

    with open(source) as fh:
        lines = fh.readlines()
    rewritten = [
        f"persistence_location {data_dir}/\n" if line.strip().startswith("persistence_location") else line
        for line in lines
    ]

    conf_path = os.path.join(data_dir, "mosquitto.conf")
    with open(conf_path, "w") as fh:
        fh.write("# GENERATED by Deployment/'OPEN AIR CORE.py' — edit broker/mosquitto.conf instead.\n")
        fh.writelines(rewritten)
    return conf_path, data_dir

# Inline comment: Logic for start_host_broker
def start_host_broker(root):
    """Bring up mosquitto on the host, replacing the broker the container served."""
    if port_is_listening(BROKER_HOST, BROKER_PORT):
        print(f"🦟 [LAUNCHER] Broker already serving {BROKER_HOST}:{BROKER_PORT} — reusing it.", flush=True)
        return True

    # /usr/sbin is off PATH for non-root shells on Debian/Ubuntu.
    binary = shutil.which("mosquitto") or next(
        (p for p in ("/usr/sbin/mosquitto", "/usr/local/sbin/mosquitto") if os.path.exists(p)), None
    )
    if not binary:
        print(
            "⚠️  [LAUNCHER] mosquitto not found on the host — no MQTT broker.\n"
            "     Install it (sudo apt install mosquitto) or restart the containers;\n"
            "     without a broker every agent will fail to connect.",
            file=sys.stderr,
        )
        return False

    conf_path, data_dir = host_broker_config(root)
    if not conf_path:
        print("⚠️  [LAUNCHER] broker/mosquitto.conf missing — cannot start host broker.", file=sys.stderr)
        return False

    print(f"🦟 [LAUNCHER] Starting host mosquitto on {BROKER_HOST}:{BROKER_PORT}...", flush=True)
    subprocess.Popen(
        [binary, "-c", conf_path],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        start_new_session=True,  # survives the execv into the orchestrator
    )

    # Same reason compose gave the broker a healthcheck: agents connect at boot,
    # and starting them first produces a confusing cascade of retries.
    for _ in range(40):
        if port_is_listening(BROKER_HOST, BROKER_PORT):
            print(f"   ✅ Broker up (retained state in {data_dir})", flush=True)
            return True
        time.sleep(0.25)

    print("⚠️  [LAUNCHER] mosquitto did not accept connections within 10s.", file=sys.stderr)
    return False

# Inline comment: Logic for main
def main():
    print("==================================================")
    print(f"🌍 OPEN-AIR IS RUNNING ON IP: {get_local_ip()}")
    print("==================================================", flush=True)

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # A bare-metal run owns the whole stack. Containers are cleared FIRST — before
    # the cargo build, so the broker is warm by the time the orchestrator boots,
    # and because pkill/fuser below cannot reach a container's processes: they
    # return EPERM and the port stays held until bind() fails with EADDRINUSE.
    if "--ignore-docker" not in sys.argv[1:]:
        containers = running_openair_containers()
        if not containers or stop_openair_containers(containers):
            # openair-broker was the MQTT broker on :1883 — replace it, or every
            # agent would have nothing to connect to. No-ops when :1883 is already
            # served, so this also covers a bare-metal box that never had Docker.
            start_host_broker(root)

    
    core_dir = os.path.join(root, "BackEnd", "Core")
    manifest = os.path.join(core_dir, "Cargo.toml")
    
    # --ignore-docker is consumed here; the Rust clap parser rejects unknowns.
    args = [a for a in sys.argv[1:] if a not in ("--ignore-docker",)]
    release = "--release" in args
    
    if "--no-build" not in args:
        print("🦀 [LAUNCHER] Building Rust core and orchestrator...", flush=True)
        build_args = ["cargo", "build", "--manifest-path", manifest]
        if release:
            build_args.append("--release")
            
        subprocess.run(build_args + ["-p", "oaRustCore"], check=True)
        subprocess.run(build_args + ["-p", "open-air-orchestrator"], check=True)
        
        print("🦀 [LAUNCHER] Building openair-yak agent...", flush=True)
        yak_manifest = os.path.join(root, "BackEnd", "openair-yak", "Cargo.toml")
        yak_build_args = ["cargo", "build", "--manifest-path", yak_manifest]
        if release:
            yak_build_args.append("--release")
        subprocess.run(yak_build_args, check=True)
        
        # Symlink the library so python helpers can use it
        built_lib = os.path.join(core_dir, "target", "release" if release else "debug", "liboaRustCore.so")
        link = os.path.join(core_dir, "oaRustCore.so")
        if os.path.exists(built_lib):
            try:
                if os.path.islink(link) or os.path.exists(link):
                    os.remove(link)
                os.symlink(os.path.relpath(built_lib, core_dir), link)
            except OSError:
                pass

    if "--no-rust" in args or "--no-orchestrator" in args:
        print("⏭️  [LAUNCHER] Rust execution skipped.", flush=True)
        return

    print("🧹 [LAUNCHER] Cleaning up any ghost orchestrator processes...", flush=True)
    subprocess.run(["pkill", "-f", "open-air-orchestrator"], check=False)
    
    print("🥊 [LAUNCHER] Bullying port 8000 to guarantee it's free...", flush=True)
    subprocess.run("fuser -k -9 8000/tcp", shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
    subprocess.run("kill -9 $(lsof -t -i:8000)", shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

    # Start openair-yak in the background
    # Its own workspace now, so its target/ is under the crate — NOT the shared
    # BackEnd/ComProtocols/target/ the agent used to build into.
    yak_dir = os.path.join(root, "BackEnd", "openair-yak")
    yak_binary_path = os.path.join(yak_dir, "target", "release" if release else "debug", "openair-yak")
    if os.path.exists(yak_binary_path):
        print("🚀 [LAUNCHER] Starting openair-yak agent...", flush=True)
        subprocess.run(["pkill", "-f", "openair-yak"], check=False)
        subprocess.Popen([yak_binary_path], cwd=yak_dir)
    else:
        print(f"⚠️ [LAUNCHER] YAK Binary not found at {yak_binary_path}", file=sys.stderr)

    # Exec into the rust binary
    binary_path = os.path.join(core_dir, "target", "release" if release else "debug", "open-air-orchestrator")
    
    if not os.path.exists(binary_path):
        print(f"❌ [LAUNCHER] Binary not found at {binary_path}", file=sys.stderr)
        sys.exit(1)
        
    # DETACH, do not become it.
    #
    # This used to `os.execv`, so the launcher WAS the orchestrator: the core
    # could never finish, and killing the terminal killed the bench. Starting it
    # in its own session decouples the two — the backend keeps running whatever
    # happens to this process or the front end.
    print("🚀 [CORE] Starting the Rust orchestrator (detached)...", flush=True)
    # The front end opens the browser, so the backend must not — but only add
    # the flag if it is not already there: clap rejects a repeated flag with a
    # parse error, and the backend then dies before it ever serves.
    backend_args = list(args)
    if "--no-browser" not in backend_args:
        backend_args.append("--no-browser")
    backend = subprocess.Popen([binary_path] + backend_args, start_new_session=True)

    # Wait for it to actually serve before handing over, rather than assuming.
    # The front end has nothing to attach to until the API answers.
    ready = False
    for _ in range(120):
        if port_is_listening("127.0.0.1", 8000, timeout=0.25):
            ready = True
            break
        if backend.poll() is not None:
            print(f"❌ [CORE] Orchestrator exited during startup (code {backend.returncode})",
                  file=sys.stderr)
            sys.exit(1)
        time.sleep(0.5)
    if not ready:
        print("⚠️  [CORE] Orchestrator did not answer on :8000 within 60s — "
              "leaving it running and continuing anyway.", file=sys.stderr)

    print(f"✅ [CORE] Backend up (pid {backend.pid}). The core's work is done.", flush=True)

    # And that is the whole job.
    #
    # The core brings up the BACK END — broker, yak, the orchestrator and its
    # bench search — and then gets out of the way. It deliberately does not
    # start the site: opening the front end is a separate act with its own
    # lifetime, so the bench keeps running whether anyone is looking at it or
    # not. Run 'OPENAIR FRONT END.py' when you want the page.
    print("   The backend keeps running. Open the site with 'OPENAIR FRONT END.py'.", flush=True)

if __name__ == "__main__":
    main()
