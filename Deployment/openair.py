# ==========================================
# Header: openair.py
# Purpose: openair.py implementation.
# Description: Logic and implementation for openair.py implementation.
# 
# Version: 26.07.05.1
# Change Log:
# - 2026-07-05: Initial annotation and documentation added.
# ==========================================

#!/usr/bin/env python3
"""Tiny launcher for OPEN-AIR that defers entirely to the Rust orchestrator."""
import os
import subprocess
import sys

import socket

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

# Inline comment: Logic for main
def main():
    print("==================================================")
    print(f"🌍 OPEN-AIR IS RUNNING ON IP: {get_local_ip()}")
    print("==================================================", flush=True)
    
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    core_dir = os.path.join(root, "BackEnd", "Core")
    manifest = os.path.join(core_dir, "Cargo.toml")
    
    args = sys.argv[1:]
    release = "--release" in args
    
    if "--no-build" not in args:
        print("🦀 [LAUNCHER] Building Rust core and orchestrator...", flush=True)
        build_args = ["cargo", "build", "--manifest-path", manifest]
        if release:
            build_args.append("--release")
            
        subprocess.run(build_args + ["-p", "oaRustCore"], check=True)
        subprocess.run(build_args + ["-p", "open-air-orchestrator"], check=True)
        
        print("🦀 [LAUNCHER] Building openair-yak agent...", flush=True)
        yak_manifest = os.path.join(root, "BackEnd", "ComProtocols", "openair-yak", "Cargo.toml")
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
    yak_dir = os.path.join(root, "BackEnd", "ComProtocols", "openair-yak")
    yak_binary_path = os.path.join(root, "BackEnd", "ComProtocols", "target", "release" if release else "debug", "openair-yak")
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
        
    print("🚀 [LAUNCHER] Handing over to Rust orchestrator...", flush=True)
    os.execv(binary_path, [binary_path] + args)

if __name__ == "__main__":
    main()
