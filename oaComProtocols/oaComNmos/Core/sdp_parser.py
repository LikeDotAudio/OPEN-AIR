# FolderName/FileName.py
# Author: Gemini (Collaborator)
# Version: 20260405.1315.4

def parse_sdp(sdp):
    """
    Parses an SDP string to extract relevant information for NMOS integration.

    Args:
        sdp (str): The SDP content as a string.

    Returns:
        dict: A dictionary containing parsed SDP attributes like name, IP, port,
              bit depth, and sample rate.
    """
    data = {}

    for line in sdp.splitlines():
        if line.startswith("s="):
            data["name"] = line[2:].strip()
        elif line.startswith("o="):
            parts = line.split()
            if len(parts) >= 6:
                data["src_ip"] = parts[5]
        elif line.startswith("c=IN IP4"):
            data["ip"] = line.split()[2].split("/")[0]
        elif line.startswith("m=audio"):
            try:
                data["port"] = int(line.split()[1])
            except (IndexError, ValueError):
                pass # Ignore if port is not parseable
        elif "rtpmap" in line and "L" in line:
            try:
                # Example format: a=rtpmap:96 L24/48000/2
                # We are interested in bit depth, sample rate, and channels
                parts = line.split("L")[1].split("/")
                if len(parts) >= 2:
                    data["bit"] = int(parts[0])
                    data["rate"] = int(parts[1])
                    if len(parts) > 2:
                        data["ch"] = int(parts[2])
            except (IndexError, ValueError):
                pass # Ignore if rtpmap values are not parseable

    return data

def build_match_key(parsed_sdp_data):
    """
    Builds a unique key from parsed SDP data for matching senders.
    The key is typically a combination of IP address and source IP.

    Args:
        parsed_sdp_data (dict): The dictionary returned by parse_sdp.

    Returns:
        str: A string key in the format "ip|src_ip" or None if IP is missing.
    """
    ip = parsed_sdp_data.get("ip")
    src_ip = parsed_sdp_data.get("src_ip")

    if not ip:
        return None

    return f"{ip}|{src_ip or 'any'}"
