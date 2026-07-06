import os, ftplib

env_vars = {}
with open("FrontEnd/.env", "r") as f:
    for line in f:
        if "=" in line:
            k, v = line.strip().split("=", 1)
            env_vars[k] = v

host = env_vars.get('FTP_HOST')
user = env_vars.get('FTP_USER')
passwd = env_vars.get('FTP_PASS')

ftp = ftplib.FTP(host)
ftp.login(user, passwd)

files = [
    "FrontEnd/Gui_Frames/5_Samples/2_Metering/6_EQ/EQ.json",
    "FrontEnd/Gui_Frames/5_Samples/2_Metering/7_Dynamics/Dynamics.json"
]

for f in files:
    with open(f, 'rb') as file:
        print(f"Uploading {f}")
        try:
            ftp.storbinary(f"STOR /{f}", file)
            print("Done")
        except Exception as e:
            print(f"Failed {f}: {e}")

ftp.quit()
