# ==========================================
# Header: deploy_FTP_to_like_dot_audio.py
# Purpose: deploy_FTP_to_like_dot_audio.py implementation.
# Description: Logic and implementation for deploy_FTP_to_like_dot_audio.py implementation.
# 
# Version: 26.07.05.1
# Change Log:
# - 2026-07-05: Initial annotation and documentation added.
# ==========================================

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

# Inline comment: Logic for generate_api_tree
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
        with open(os.path.join(api_dir, "tree.json"), 'w', encoding='utf-8') as f:
            json.dump(tree, f, separators=(',', ':'))
        print("✅ Static /api/tree.json generated successfully.")
    else:
        print("⚠️ Gui_Frames directory not found in FrontEnd, skipping tree generation.")

# 1. At the front end of the deploy, generate the JSON tree!
generate_api_tree()

# Inline comment: Logic for generate_api_grabbag
def generate_api_grabbag():
    import urllib.request
    print("🎒 Generating static /api/grabbag JSON from local backend...")
    try:
        req = urllib.request.Request("http://localhost:8000/api/grabbag")
        with urllib.request.urlopen(req) as response:
            data = response.read()
            api_dir = os.path.join(script_dir, "api")
            os.makedirs(api_dir, exist_ok=True)
            with open(os.path.join(api_dir, "grabbag"), "wb") as f:
                f.write(data)
        print("✅ Static /api/grabbag generated successfully.")
    except Exception as e:
        print(f"⚠️ Could not fetch /api/grabbag: {e}")

generate_api_grabbag()

# Load credentials. In CI these come from OS environment (GitHub Environment
# secrets); locally they fall back to the gitignored .env file. OS env always
# wins so the same script serves both a laptop and the pipeline.
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
    print("ℹ️ No .env file found; relying on OS environment for credentials.")

def cred(name, default=None):
    return os.environ.get(name) or env_vars.get(name) or default

host = cred('FTP_HOST')
user = cred('FTP_USER')
passwd = cred('FTP_PASS')
remote_base_dir = cred('REMOTE_DIR', '/')

if not all([host, user, passwd]):
    print("❌ Missing FTP credentials (FTP_HOST / FTP_USER / FTP_PASS).")
    print("   Set them in FrontEnd/.env locally, or as GitHub Environment secrets in CI.")
    sys.exit(1)

repo_root = os.path.dirname(script_dir)
os.chdir(repo_root)

files_to_upload = []
sync_all = False

# ---- File selection strategy -------------------------------------------------
# CI (commit-range):  DEPLOY_DIFF_BASE / DEPLOY_DIFF_HEAD are set by the workflow
#                     from github.event.before / github.sha -> upload only the
#                     FrontEnd files that changed in that push range.
# Full sync:          DEPLOY_FULL_SYNC=1, or a first push (null base) -> compare
#                     every local file against the server by mtime/size.
# Local (default):    no env set -> upload uncommitted working-tree changes.
diff_base = os.environ.get('DEPLOY_DIFF_BASE', '').strip()
diff_head = (os.environ.get('DEPLOY_DIFF_HEAD', '').strip() or 'HEAD')
force_full = os.environ.get('DEPLOY_FULL_SYNC') == '1'

def _is_null_ref(ref):
    # git's "no previous commit" sentinel is all zeros
    return (not ref) or set(ref) == {'0'}

if force_full:
    print("\n🧹 DEPLOY_FULL_SYNC=1 -> full timestamp sync of all files.")
    sync_all = True
elif diff_base != '':
    # CI commit-range mode
    if _is_null_ref(diff_base):
        print("\n🌱 No previous commit for this ref (first deploy) -> full timestamp sync.")
        sync_all = True
    else:
        print(f"\n🔍 Commit-range deploy: {diff_base[:8]}..{diff_head[:8]}")
        rng = subprocess.run(['git', 'diff', '--name-only', diff_base, diff_head],
                             capture_output=True, text=True)
        if rng.returncode != 0:
            print(f"⚠️ git diff failed ({rng.stderr.strip()}); falling back to full sync.")
            sync_all = True
        else:
            for filepath in rng.stdout.splitlines():
                filepath = filepath.strip()
                if filepath.startswith("FrontEnd/") and not filepath.endswith('.py'):
                    if os.path.isfile(os.path.join(repo_root, filepath)):
                        files_to_upload.append(filepath.replace("\\", "/"))
            print(f"   {len(files_to_upload)} changed FrontEnd file(s) in range.")
else:
    # Local mode: uncommitted working-tree changes
    print("\n🔍 Finding uncommitted changed files in FrontEnd...")
    result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
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
                        if f.endswith('.py'):
                            continue
                        full_f = os.path.join(root, f)
                        rel_f = os.path.relpath(full_f, repo_root)
                        if rel_f.startswith("FrontEnd/"):
                            files_to_upload.append(rel_f.replace("\\", "/"))
            else:
                if filepath.startswith("FrontEnd/") and not filepath.endswith('.py'):
                    files_to_upload.append(filepath.replace("\\", "/"))

    files_to_upload = list(set(files_to_upload))
    if not files_to_upload:
        print("ℹ️ No uncommitted changes found. Falling back to FTP timestamp sync for all files...")
        sync_all = True

# Generated API artifacts are never in a git diff range, but the live site must
# always get the freshest tree/grabbag and entry HTML. Force them in.
if not sync_all:
    for artifact in ("FrontEnd/api/tree.json", "FrontEnd/api/grabbag", "FrontEnd/index.html"):
        if os.path.isfile(os.path.join(repo_root, artifact)):
            files_to_upload.append(artifact)

files_to_upload = list(set(files_to_upload))

# Prefer explicit FTPS (encrypted control + data channel). Fall back to plain
# FTP unless DEPLOY_FTP_REQUIRE_TLS=1. Force plain with DEPLOY_FTP_PLAIN=1.
force_plain = os.environ.get('DEPLOY_FTP_PLAIN') == '1'
require_tls = os.environ.get('DEPLOY_FTP_REQUIRE_TLS') == '1'
ftp = None

if not force_plain:
    try:
        print(f"\n🔒 Connecting to {host} over explicit FTPS...")
        ftp = ftplib.FTP_TLS(host, timeout=30)
        ftp.login(user, passwd)
        ftp.prot_p()  # encrypt the data channel too
        print("✅ Connected and logged in over FTPS (TLS).")
    except Exception as e:
        print(f"⚠️ FTPS unavailable: {e}")
        if require_tls:
            print("❌ DEPLOY_FTP_REQUIRE_TLS=1 but FTPS failed. Aborting.")
            sys.exit(1)
        ftp = None

if ftp is None:
    try:
        print(f"\n📡 Connecting to {host} over plain FTP...")
        ftp = ftplib.FTP(host, timeout=30)
        ftp.login(user, passwd)
        print("✅ Connected and logged in (plain FTP).")
    except Exception as e:
        print(f"❌ Failed to connect to FTP: {e}")
        sys.exit(1)

# Inline comment: Logic for ensure_remote_dir
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

# Inline comment: Logic for get_remote_mtime
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

# Inline comment: Logic for get_remote_size
def get_remote_size(ftp_conn, remote_file):
    try:
        res = ftp_conn.sendcmd(f"SIZE {remote_file}")
        if res.startswith("213"):
            return int(res[4:].strip())
    except Exception:
        pass
    return -1

# If we are doing a full sync, compare dates
if sync_all:
    os.chdir(script_dir)
    print("⏳ Comparing local and remote file dates. This might take a moment...")
    for root, dirs, files in os.walk("."):
        for f in files:
            if f.endswith('.py') or f in [".env", ".gitignore"]:
                continue
            
            local_full = os.path.join(root, f)
            local_rel = os.path.relpath(local_full, ".")
            
            # Avoid hidden directories completely
            if "/." in "/" + local_rel.replace("\\", "/"):
                continue
                
            local_mtime = os.path.getmtime(local_full) # epoch seconds
            local_size = os.path.getsize(local_full)
            
            remote_filepath = remote_base_dir.rstrip('/') + '/' + local_rel.replace("\\", "/")
            remote_mtime = get_remote_mtime(ftp, remote_filepath)
            remote_size = get_remote_size(ftp, remote_filepath)
            
            # Upload if local is newer than remote (with 2 seconds buffer for slight clock drift)
            # OR if the file size is completely different
            if (local_mtime > remote_mtime + 2) or (local_size != remote_size):
                files_to_upload.append("FrontEnd/" + local_rel.replace("\\", "/"))

files_to_upload = list(set(files_to_upload))

if not files_to_upload:
    print("✅ All files are up to date! Nothing to upload.")
    ftp.quit()
    sys.exit(0)

# Upload the entry HTML LAST so the live page never points at assets that
# haven't finished uploading yet (near-atomic cutover).
def sort_priority(filepath):
    base = os.path.basename(filepath).lower()
    if base in ['index.html', 'index.htm']:
        return 1
    return 0

files_to_upload.sort(key=sort_priority)

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


# ---- Post-deploy build stamp (observability) --------------------------------
# Best-effort: publish the deployed commit + timestamp to MQTT so clients and
# dashboards can see which build is live. No-op unless MQTT_HOST is configured.
def publish_build_stamp():
    mqtt_host = cred('MQTT_HOST')
    if not mqtt_host:
        return
    try:
        import paho.mqtt.publish as publish
    except ImportError:
        print("⚠️ paho-mqtt not installed; skipping build stamp.")
        return

    sha = os.environ.get('DEPLOY_DIFF_HEAD')
    if not sha or sha == 'HEAD':
        rev = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True)
        sha = rev.stdout.strip() if rev.returncode == 0 else 'unknown'

    payload = json.dumps({
        "environment": os.environ.get('DEPLOY_ENV', 'local'),
        "commit": sha,
        "deployed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "files": len(files_to_upload),
    })
    topic = cred('MQTT_TOPIC', 'OpenAir/Deploy/stamp')
    port = int(cred('MQTT_PORT', '1883'))
    auth = None
    if cred('MQTT_USER'):
        auth = {'username': cred('MQTT_USER'), 'password': cred('MQTT_PASS', '')}

    try:
        publish.single(topic, payload, hostname=mqtt_host, port=port, auth=auth)
        print(f"📣 Build stamp published to {mqtt_host}:{port} [{topic}]")
    except Exception as e:
        print(f"⚠️ Build stamp publish failed: {e}")


publish_build_stamp()
