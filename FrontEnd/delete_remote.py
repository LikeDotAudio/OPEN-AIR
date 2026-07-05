# ==========================================
# Header: delete_remote.py
# Purpose: delete_remote.py implementation.
# Description: Logic and implementation for delete_remote.py implementation.
# 
# Version: 26.07.05.1
# Change Log:
# - 2026-07-05: Initial annotation and documentation added.
# ==========================================

import ftplib
import os
import sys

# Read .env file manually
env_vars = {}
script_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(script_dir, '.env')
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                key, val = line.split('=', 1)
                env_vars[key.strip()] = val.strip()

host = env_vars.get('FTP_HOST')
user = env_vars.get('FTP_USER')
passwd = env_vars.get('FTP_PASS')
remote_base_dir = env_vars.get('REMOTE_DIR', '/')

# Inline comment: Logic for remove_ftp_dir
def remove_ftp_dir(ftp, path):
    try:
        # Try to list directory contents
        for item in ftp.nlst(path):
            # Try to delete file
            try:
                ftp.delete(item)
            except ftplib.error_perm:
                # If it's a directory, recursively delete it
                remove_ftp_dir(ftp, item)
        # Remove the now empty directory
        ftp.rmd(path)
        print(f"✅ Deleted remote directory: {path}")
    except ftplib.error_temp as e:
        print(f"⚠️ Warning (temp error): {path} - {e}")
    except ftplib.error_perm as e:
        print(f"⚠️ Warning (perm error): {path} - {e}")
    except Exception as e:
        print(f"⚠️ Note: {path} already removed or not found.")

# Inline comment: Logic for main
def main():
    if not host:
        print("No FTP host configured.")
        return
        
    print(f"📡 Connecting to FTP server {host}...")
    try:
        ftp = ftplib.FTP(host)
        ftp.login(user, passwd)
        
        target1 = remote_base_dir.rstrip('/') + '/Gui_Frames/Window_1/right_50/top_10'
        target2 = remote_base_dir.rstrip('/') + '/Gui_Frames/Window_1/right_50/bottom_90'
        
        print(f"🗑️ Deleting {target1}...")
        remove_ftp_dir(ftp, target1)
        
        print(f"🗑️ Deleting {target2}...")
        remove_ftp_dir(ftp, target2)
        
        ftp.quit()
        print("🎉 Cleanup complete!")
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    main()
