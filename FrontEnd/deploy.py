#!/usr/bin/env python3
import os
import subprocess
import ftplib
import sys
import json
import datetime

# Change to the directory containing this script (FrontEnd)
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

def generate_api_tree():
    """Generate the static /api/tree JSON file from the Gui_Frames folder"""
    print("🌳 Generating static /api/tree JSON from Gui_Frames...")
    gui_frames_path = os.path.join(script_dir, "Gui_Frames")
    
    def get_directory_tree(path, base_path):
        name = os.path.basename(path)
        children = []
        if os.path.isdir(path):
            entries = sorted(os.listdir(path))
            for entry in entries:
                if entry.startswith('.') or entry.startswith('__'):
                    continue
                full_path = os.path.join(path, entry)
                if os.path.isdir(full_path):
                    children.append(get_directory_tree(full_path, base_path))
                elif entry.endswith('.json'):
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = json.load(f)
                    except Exception as e:
                        content = {"error": f"Could not parse JSON: {e}"}
                    
                    rel_path = os.path.relpath(full_path, base_path)
                    rel_path_str = "/" + rel_path.replace("\\", "/")
                    children.append({
                        "name": entry,
                        "type": "file",
                        "content": content,
                        "path": rel_path_str
                    })
        return {
            "name": name,
            "type": "directory",
            "children": children
        }
    
    if os.path.exists(gui_frames_path):
        tree = get_directory_tree(gui_frames_path, gui_frames_path)
        api_dir = os.path.join(script_dir, "api")
        os.makedirs(api_dir, exist_ok=True)
        with open(os.path.join(api_dir, "tree"), 'w', encoding='utf-8') as f:
            json.dump(tree, f)
        print("✅ Static /api/tree generated successfully.")
    else:
        print("⚠️ Gui_Frames directory not found in FrontEnd, skipping tree generation.")

# 1. At the front end of the deploy, generate the JSON tree!
generate_api_tree()

# Read .env file manually
env_vars = {}
env_path = os.path.join(script_dir, '.env')
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, val = line.split('=', 1)
                env_vars[key.strip()] = val.strip()
else:
    print("❌ .env file not found.")
    sys.exit(1)

host = env_vars.get('FTP_HOST')
user = env_vars.get('FTP_USER')
passwd = env_vars.get('FTP_PASS')
remote_base_dir = env_vars.get('REMOTE_DIR', '/')

if not all([host, user, passwd]):
    print("❌ Missing FTP credentials in .env file.")
    sys.exit(1)

print("\n🔍 Finding uncommitted changed files in FrontEnd...")

repo_root = os.path.dirname(script_dir)
os.chdir(repo_root)

# Check for uncommitted files via git
result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
files_to_upload = []

if result.returncode == 0 and result.stdout.strip():
    for line in result.stdout.splitlines():
        status = line[:2]
        if 'D' in status:
            continue
        filepath = line[3:].strip('"')
        
        # If Git lists an entire untracked directory, we need to walk it and add all files
        full_local = os.path.join(repo_root, filepath)
        if os.path.isdir(full_local):
            for root, _, files in os.walk(full_local):
                for f in files:
                    full_f = os.path.join(root, f)
                    rel_f = os.path.relpath(full_f, repo_root)
                    if rel_f.startswith("FrontEnd/"):
                        files_to_upload.append(rel_f.replace("\\", "/"))
        else:
            if filepath.startswith("FrontEnd/"):
                files_to_upload.append(filepath.replace("\\", "/"))

# Deduplicate
files_to_upload = list(set(files_to_upload))
sync_all = False

if not files_to_upload:
    print("ℹ️ No uncommitted changes found. Falling back to FTP timestamp sync for all files...")
    sync_all = True

print(f"\n📡 Connecting to FTP server {host}...")
try:
    ftp = ftplib.FTP(host)
    ftp.login(user, passwd)
    print("✅ Connected and logged in.")
except Exception as e:
    print(f"❌ Failed to connect to FTP: {e}")
    sys.exit(1)

def ensure_remote_dir(ftp_conn, remote_path):
    dirs = [d for d in remote_path.split('/') if d]
    current = "/" if remote_path.startswith("/") else ""
    if current == "/":
        ftp_conn.cwd("/")
    for d in dirs:
        try:
            ftp_conn.cwd(d)
        except ftplib.error_perm:
            try:
                ftp_conn.mkd(d)
                ftp_conn.cwd(d)
            except Exception as e:
                pass

def get_remote_mtime(ftp_conn, remote_file):
    try:
        res = ftp_conn.sendcmd(f"MDTM {remote_file}")
        if res.startswith("213"):
            dt_str = res[4:].strip()
            # FTP returns time in UTC: YYYYMMDDHHMMSS
            dt = datetime.datetime.strptime(dt_str, "%Y%m%d%H%M%S")
            dt = dt.replace(tzinfo=datetime.timezone.utc)
            return dt.timestamp()
    except Exception:
        pass
    return 0

# If we are doing a full sync, compare dates
if sync_all:
    os.chdir(script_dir)
    print("⏳ Comparing local and remote file dates. This might take a moment...")
    for root, dirs, files in os.walk("."):
        for f in files:
            if f in [".env", ".gitignore", "deploy.py"]:
                continue
            
            local_full = os.path.join(root, f)
            local_rel = os.path.relpath(local_full, ".")
            
            # Avoid hidden directories completely
            if "/." in "/" + local_rel.replace("\\", "/"):
                continue
                
            local_mtime = os.path.getmtime(local_full) # epoch seconds
            remote_filepath = remote_base_dir.rstrip('/') + '/' + local_rel.replace("\\", "/")
            remote_mtime = get_remote_mtime(ftp, remote_filepath)
            
            # Upload if local is newer than remote (with 2 seconds buffer for slight clock drift)
            if local_mtime > remote_mtime + 2:
                files_to_upload.append("FrontEnd/" + local_rel.replace("\\", "/"))

files_to_upload = list(set(files_to_upload))

if not files_to_upload:
    print("✅ All files are up to date! Nothing to upload.")
    ftp.quit()
    sys.exit(0)

print(f"\n🚀 Found {len(files_to_upload)} files to deploy.")
for f in files_to_upload:
    print(f"   - {f}")

for filepath in files_to_upload:
    local_path = os.path.join(repo_root, filepath)
    if not os.path.isfile(local_path):
        continue
        
    rel_path = filepath[len("FrontEnd/"):]
    remote_filepath = remote_base_dir.rstrip('/') + '/' + rel_path.lstrip('/')
    remote_filepath = remote_filepath.replace("\\", "/")
    
    remote_folder = os.path.dirname(remote_filepath)
    filename = os.path.basename(remote_filepath)
    
    print(f"📤 Uploading {rel_path}...")
    
    try:
        ftp.cwd("/")
        ensure_remote_dir(ftp, remote_folder)
        ftp.cwd("/")
        ftp.cwd(remote_folder)
        with open(local_path, 'rb') as f:
            ftp.storbinary(f"STOR {filename}", f)
    except Exception as e:
        print(f"❌ Failed to upload {rel_path}: {e}")

ftp.quit()
print("\n🎉 Deployment complete!")
