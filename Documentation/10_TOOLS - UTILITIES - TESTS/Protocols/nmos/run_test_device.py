#!/usr/bin/env python3
import os
import subprocess
import sys
import shutil

def run_cmd(cmd, **kwargs):
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True, **kwargs)

def check_system_deps():
    missing = []
    if not shutil.which("cmake"):
        missing.append("cmake")
    if not shutil.which("g++") and not shutil.which("clang") and not shutil.which("cl"):
        missing.append("a C++ compiler (g++, clang, or MSVC)")
    if os.name != 'nt' and not os.path.exists("/usr/include/dns_sd.h"):
        missing.append("libavahi-compat-libdnssd-dev (Avahi mDNS header)")
    
    if missing:
        print(f"❌ Missing system dependencies: {', '.join(missing)}")
        print("Please install them using your system package manager.")
        print("For Ubuntu/Debian: sudo apt-get install build-essential cmake libavahi-compat-libdnssd-dev")
        sys.exit(1)

def main():
    check_system_deps()
    repo_root = os.path.dirname(os.path.abspath(__file__))
    dev_dir = os.path.join(repo_root, "nmos-cpp-master", "Development")
    build_dir = os.path.join(dev_dir, "build")
    os.makedirs(build_dir, exist_ok=True)
    
    # 1. Install Conan if missing
    conan_exec = shutil.which("conan")
    if not conan_exec:
        print("📦 Conan not found globally. Forcing global install...")
        run_cmd([sys.executable, "-m", "pip", "install", "conan", "--break-system-packages"])
        conan_exec = shutil.which("conan")
        if not conan_exec:
            conan_exec = f"{sys.executable} -m conans.conan" if sys.version_info < (3, 0) else f"{sys.executable} -m conan"
        os.system(f"{conan_exec} profile detect --force")
    else:
        conan_exec = "conan"

    print("\n📦 Resolving C++ dependencies with Conan...")
    # Conan install inside the build directory
    os.system(f"{conan_exec} install {dev_dir} -of {build_dir} --build=missing -g CMakeToolchain")
    
    print("\n🛠️  Configuring CMake for NMOS Mock Device (Node)...")
    cmake_args = [
        "cmake", "-B", build_dir, "-S", dev_dir, 
        "-DCMAKE_BUILD_TYPE=Release",
        f"-DCMAKE_PREFIX_PATH={build_dir}",
        "-DBoost_NO_SYSTEM_PATHS=ON"
    ]
    
    toolchain = os.path.join(build_dir, "conan_toolchain.cmake")
    if os.path.exists(toolchain):
        cmake_args.append(f"-DCMAKE_TOOLCHAIN_FILE={toolchain}")
        
    run_cmd(cmake_args)
    
    print("\n🔨 Building NMOS Mock Device (nmos-cpp-node)...")
    run_cmd(["cmake", "--build", build_dir, "--target", "nmos-cpp-node", "-j", str(os.cpu_count() or 4)])
    
    # Locate binary
    binary_path = os.path.join(build_dir, "nmos-cpp-node")
    if not os.path.exists(binary_path):
        binary_path = os.path.join(build_dir, "Release", "nmos-cpp-node")
        
    if not os.path.exists(binary_path):
        print(f"❌ Could not find compiled binary at {binary_path}")
        sys.exit(1)
    
    print(f"\n🚀 Starting NMOS Mock Device...")
    try:
        run_cmd([binary_path] + sys.argv[1:])
    except KeyboardInterrupt:
        print("\n🛑 Mock Device stopped by user.")

if __name__ == "__main__":
    main()
