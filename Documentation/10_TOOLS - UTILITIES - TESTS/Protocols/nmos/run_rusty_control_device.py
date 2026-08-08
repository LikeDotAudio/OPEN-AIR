#!/usr/bin/env python3
import os
import subprocess
import sys
import shutil

def check_system_deps():
    if not shutil.which("cargo"):
        print("❌ Missing system dependency: cargo (Rust)")
        print("Please install Rust using: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh")
        sys.exit(1)

def main():
    check_system_deps()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    rust_dir = os.path.join(script_dir, "nmos-control-rusty-device-master")
    
    if not os.path.exists(rust_dir):
        print(f"❌ Error: Rust project not found at {rust_dir}")
        sys.exit(1)
        
    print(f"\n📦 Building and running Rusty Control Device...")
    print(f"Directory: {rust_dir}")
    
    cargo_cmd = ["cargo", "run", "--release"]
    
    # Pass any additional CLI arguments to the Rust executable
    if len(sys.argv) > 1:
        cargo_cmd.append("--")
        cargo_cmd.extend(sys.argv[1:])
        
    try:
        subprocess.run(cargo_cmd, cwd=rust_dir)
    except KeyboardInterrupt:
        print("\n🛑 Rusty Control Device stopped by user.")

if __name__ == "__main__":
    main()
