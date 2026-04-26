# FolderName/FileName.py
# Author: Gemini (Collaborator)
# Version: 20260405.1315.6

import time

import requests

from oaComProtocols.oaComNmos.Core.sdp_parser import build_match_key, parse_sdp

# --- Global State for Sender Cache ---
# These variables will be managed and potentially initialized by an orchestrator.
SENDER_CACHE = []
SENDER_KEY_CACHE = {}
CACHE_TS = 0
CACHE_TTL = 10 # Cache validity in seconds

# ---------------------------------------------------------------------
# Sender Cache Management
# ---------------------------------------------------------------------

def fetch_all_senders(registrar_url):
    """
    Fetches all senders from the NMOS registry's query API with pagination.

    Args:
        registrar_url (str): The base URL of the NMOS registration API.

    Returns:
        list: A list of sender resource objects.
    """
    all_senders = []
    query_url = registrar_url.replace("registration", "query")

    limit = 100
    until = None

    while True:
        url = f"{query_url}/senders?paging.limit={limit}&paging.order=update"

        if until:
            url += f"&paging.until={until}"

        print(f"[SenderCache] Fetching senders: GET {url}")

        try:
            r = requests.get(url, timeout=2)
            if r.status_code != 200:
                print(f"[SenderCache] ERROR fetching senders: {r.status_code} - {r.text}")
                break

            data = r.json()
            print(f"[SenderCache] Received {len(data)} senders in this page.")

            if not data:
                break

            all_senders.extend(data)

            link_header = r.headers.get("Link")
            if not link_header:
                break

            # Parse Link header for next page
            next_link_parts = [part.strip() for part in link_header.split(',')]
            next_url_info = None
            for part in next_link_parts:
                if 'rel="next"' in part:
                    next_url_info = part.split(';')[0].strip('<>')
                    break

            if next_url_info and "paging.until=" in next_url_info:
                until = next_url_info.split("paging.until=")[1]
            else:
                break # No next page found or invalid format

        except requests.exceptions.RequestException as e:
            print(f"[SenderCache] Network error during sender fetch: {e}")
            break
        except Exception as e:
            print(f"[SenderCache] Unexpected error during sender fetch: {e}")
            break

    print(f"[SenderCache] Total senders fetched: {len(all_senders)}")
    return all_senders


def rebuild_sender_key_cache(registrar_url):
    """
    Fetches all senders, parses their manifest SDPs, and builds a cache
    mapping SDP-derived keys to sender resources.

    Args:
        registrar_url (str): The base URL of the NMOS registration API.
    """
    global SENDER_CACHE, SENDER_KEY_CACHE, CACHE_TS

    print("[SenderCache] Rebuilding sender key cache...")

    SENDER_CACHE = fetch_all_senders(registrar_url)
    SENDER_KEY_CACHE = {}

    for sender_resource in SENDER_CACHE:
        sender_id = sender_resource.get("id")
        manifest_url = sender_resource.get("manifest_href")

        if not sender_id or not manifest_url:
            continue

        try:
            # Fetch manifest (SDP)
            response = requests.get(manifest_url, timeout=2)
            if response.status_code != 200:
                print(f"[SenderCache] Failed to fetch manifest for sender {sender_id}: {response.status_code}")
                continue

            sdp_content = response.text
            parsed_sdp_data = parse_sdp(sdp_content)
            match_key = build_match_key(parsed_sdp_data)

            if match_key:
                SENDER_KEY_CACHE[match_key] = sender_resource
                print(f"[SenderCache] Mapped sender '{sender_id}' to key '{match_key}'")
            else:
                print(f"[SenderCache] Could not generate match key for sender '{sender_id}' from manifest.")

        except requests.exceptions.RequestException as e:
            print(f"[SenderCache] Network error fetching manifest for sender {sender_id}: {e}")
        except Exception as e:
            print(f"[SenderCache] Error processing manifest for sender {sender_id}: {e}")

    CACHE_TS = time.time()
    print(f"[SenderCache] Sender key cache rebuilt with {len(SENDER_KEY_CACHE)} entries.")


def get_existing_senders_map(registrar_url):
    """
    Retrieves the sender cache, rebuilding it if it's expired.

    Args:
        registrar_url (str): The base URL of the NMOS registration API.

    Returns:
        dict: The map of sender keys to sender resources.
    """
    global CACHE_TS

    current_time = time.time()
    if current_time - CACHE_TS > CACHE_TTL:
        print("[SenderCache] Cache expired, rebuilding...")
        rebuild_sender_key_cache(registrar_url)
    else:
        print("[SenderCache] Using existing cached sender map.")

    return SENDER_KEY_CACHE


def find_existing_sender(sdp_content, registrar_url):
    """
    Finds an existing NMOS sender resource that matches the provided SDP content.

    Args:
        sdp_content (str): The SDP content of the incoming stream.
        registrar_url (str): The base URL of the NMOS registration API.

    Returns:
        dict or None: The sender resource if found, otherwise None.
    """
    parsed_sdp_data = parse_sdp(sdp_content)
    match_key = build_match_key(parsed_sdp_data)

    if not match_key:
        print("[SenderCache] Could not generate match key for SDP.")
        return None

    print(f"[SenderCache] Attempting to match SDP with key: '{match_key}'")
    sender_map = get_existing_senders_map(registrar_url)

    sender_resource = sender_map.get(match_key)

    if sender_resource:
        print(f"[SenderCache] FOUND existing sender: {sender_resource.get('id')}")
    else:
        print("[SenderCache] No existing sender found matching the SDP.")

    return sender_resource
