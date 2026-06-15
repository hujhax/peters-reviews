import requests
import os
import time
import json
import re
from bs4 import BeautifulSoup
import hashlib

PAGES_DIR = "pages"
HISTORICAL_LINKS_FILE = "unreachable review links.txt"
BASE_TAG_URL = "https://hujhax.livejournal.com/?skip={skip}&tag=media%20update&style=mine"

def get_id_from_url(url):
    # Extract numbers from URL: https://hujhax.livejournal.com/297087.html -> 297087
    match = re.search(r'/(\d+)\.html', url)
    if match:
        return match.group(1)
    # Handle user/hujhax/164406.html
    match = re.search(r'/(\d+)\.html', url)
    # Actually just hash it if it's weird
    return hashlib.md5(url.encode()).hexdigest()[:10]

def download_url(url, filepath):
    print(f"Downloading {url} to {filepath}...")
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(response.text)
            return True
        else:
            print(f"  Failed with status code {response.status_code}")
    except Exception as e:
        print(f"  Error: {e}")
    return False

def refresh_historical():
    print("--- Refreshing Historical Pages ---")
    if not os.path.exists(HISTORICAL_LINKS_FILE):
        print(f"File {HISTORICAL_LINKS_FILE} not found.")
        return

    with open(HISTORICAL_LINKS_FILE, 'r') as f:
        urls = [line.strip() for line in f if line.strip().startswith('http')]

    for url in urls:
        post_id = get_id_from_url(url)
        filepath = os.path.join(PAGES_DIR, f"historical_{post_id}.html")
        if not os.path.exists(filepath):
            download_url(url, filepath)
            time.sleep(0.5)
        else:
            print(f"  Skipping {url} (already exists)")

def refresh_standard():
    print("--- Refreshing Standard Tag Pages ---")
    skip = 0
    seen_post_ids = set()
    
    while True:
        url = BASE_TAG_URL.format(skip=skip)
        filepath = os.path.join(PAGES_DIR, f"tag_skip_{skip}.html")
        
        # We always download the latest tag pages to check for new content
        # or at least the first few.
        success = download_url(url, filepath)
        if not success:
            break
            
        # Check for repetition to know when to stop
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            blocks = soup.find_all('div', class_='H3Holder')
            
            if not blocks:
                print("  No blocks found. Stopping.")
                break
                
            current_page_post_ids = []
            for block in blocks:
                ljcut = block.find('b', class_='ljcut-link')
                if ljcut and ljcut.has_attr('data-widget-options'):
                    try:
                        opts = json.loads(ljcut['data-widget-options'].replace('&quot;', '"'))
                        if 'ditemid' in opts:
                            current_page_post_ids.append(opts['ditemid'])
                    except: pass
            
            if current_page_post_ids and all(pid in seen_post_ids for pid in current_page_post_ids):
                print("  Repetition detected. Finished refreshing tag pages.")
                break
                
            for pid in current_page_post_ids:
                seen_post_ids.add(pid)
        
        skip += 30
        time.sleep(0.5)

if __name__ == "__main__":
    os.makedirs(PAGES_DIR, exist_ok=True)
    refresh_historical()
    refresh_standard()
    print("Refresh complete.")
