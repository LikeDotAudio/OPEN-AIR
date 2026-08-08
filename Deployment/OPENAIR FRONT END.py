# ==========================================
# Header: OPENAIR FRONT END.py
# Purpose: Open the site again, fast — no rebuild, no bench rescan.
# Description: The everyday launcher. 'OPEN AIR CORE.py' is the cold start that
#              builds the Rust core and hunts the bench; this one assumes that
#              has already happened and just brings the front end back up.
#
# Version: 26.08.07.1
# Change Log:
# - 2026-08-07: Split out of the core launcher.
# ==========================================

#!/usr/bin/env python3
"""Bring the OPEN-AIR site back up without rebuilding or rescanning.

WHAT THIS SKIPS, AND WHY IT IS SAFE

  * cargo builds — `--no-build`. If the Rust sources changed, this launcher
    will happily run the previous binary, which is the one thing to remember
    about it. Use OPEN AIR CORE.py after editing Rust.

  * the VISA scan — `--no-scan`. A scan is a subnet gateway hunt plus an *IDN?
    probe per candidate: slow, noisy, and pure waste when the bench has not
    moved. The instruments come from the retained tree instead, which is where
    the last scan left them. A rescan is still one press away in the
    Discovered tab.

Everything else is identical: the broker check, the port-8000 cleanup, yak, and
the orchestrator serving the site.
"""
import os
import subprocess
import sys

# The core launcher owns the shared logic — broker startup, Docker handling,
# port cleanup. Importing it rather than copying keeps one definition of each.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
core = __import__("OPEN AIR CORE")


# Inline comment: Logic for main
def main():
    print("==================================================")
    print(f"🌍 OPEN-AIR FRONT END ON IP: {core.get_local_ip()}")
    print("   (no rebuild, no rescan — use 'OPEN AIR CORE.py' for a cold start)")
    print("==================================================", flush=True)

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Same containers-vs-bare-metal rule as the cold start: a container holding
    # port 8000 cannot be reached by the cleanup below, so the orchestrator
    # would boot its agents and then die on bind.
    if "--ignore-docker" not in sys.argv[1:]:
        containers = core.running_openair_containers()
        if not containers or core.stop_openair_containers(containers):
            core.start_host_broker(root)

    binary = os.path.join(root, "BackEnd", "Core", "target",
                          "release" if "--release" in sys.argv else "debug",
                          "open-air-orchestrator")
    if not os.path.exists(binary):
        print(f"❌ [FRONT END] No orchestrator binary at {binary}\n"
              f"   Nothing has been built yet — run 'OPEN AIR CORE.py' once first.",
              file=sys.stderr)
        sys.exit(1)

    # ATTACH to a backend that is already serving.
    #
    # OPEN AIR CORE.py leaves the orchestrator running detached, and the site it
    # serves IS the front end. Killing it here to start our own would take the
    # bench down every time someone reopened the page — the opposite of
    # decoupling. If :8000 already answers, there is nothing to launch.
    if core.port_is_listening("127.0.0.1", 8000, timeout=0.5):
        print("✅ [FRONT END] Backend already serving http://localhost:8000 — attaching.", flush=True)
        if "--no-browser" not in sys.argv[1:]:
            try:
                import webbrowser
                webbrowser.open("http://localhost:8000")
            except Exception:
                pass
        print("   Nothing to start. The backend keeps running independently of this process.",
              flush=True)
        return

    print("🧹 [FRONT END] Cleaning up any ghost orchestrator processes...", flush=True)
    subprocess.run(["pkill", "-f", "open-air-orchestrator"], check=False)
    print("🥊 [FRONT END] Bullying port 8000 to guarantee it's free...", flush=True)
    subprocess.run("fuser -k -9 8000/tcp", shell=True,
                   stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)

    # yak translates panel presses into SCPI; without it every control is inert.
    yak_dir = os.path.join(root, "BackEnd", "openair-yak")
    yak_binary = os.path.join(yak_dir, "target",
                              "release" if "--release" in sys.argv else "debug",
                              "openair-yak")
    if os.path.exists(yak_binary):
        print("🚀 [FRONT END] Starting openair-yak agent...", flush=True)
        subprocess.run(["pkill", "-f", "openair-yak"], check=False)
        subprocess.Popen([yak_binary], cwd=yak_dir)
    else:
        print(f"⚠️ [FRONT END] YAK binary not found at {yak_binary} — controls will not drive anything",
              file=sys.stderr)

    # --ignore-docker is consumed here; the Rust clap parser rejects unknowns.
    passthrough = [a for a in sys.argv[1:] if a != "--ignore-docker"]
    for flag in ("--no-build", "--no-scan"):
        if flag not in passthrough:
            passthrough.append(flag)

    print("🚀 [FRONT END] Handing over to Rust orchestrator (no scan)...", flush=True)
    os.execv(binary, [binary] + passthrough)


if __name__ == "__main__":
    main()
