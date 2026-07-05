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
    
    root = os.path.dirname(os.path.abspath(__file__))
    
    # Launch GUI Splash Screen in the background
    splash_path = os.path.join(root, "splash.py")
    if os.path.exists(splash_path):
        subprocess.Popen([sys.executable, splash_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
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

    # Exec into the rust binary
    binary_path = os.path.join(core_dir, "target", "release" if release else "debug", "open-air-orchestrator")
    
    if not os.path.exists(binary_path):
        print(f"❌ [LAUNCHER] Binary not found at {binary_path}", file=sys.stderr)
        sys.exit(1)
        
    print("🚀 [LAUNCHER] Handing over to Rust orchestrator...", flush=True)
    os.execv(binary_path, [binary_path] + args)

if __name__ == "__main__":
    main()
