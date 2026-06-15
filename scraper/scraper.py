import os
from bs4 import BeautifulSoup
import csv
import datetime
import pytz
from dateutil import parser as date_parser
import re
import json
import glob
from urllib.parse import urljoin

PAGES_DIR = "pages"
CSV_FILE = "peter_reviews_data.csv"
MEDIA_TYPES = ["book", "movie", "TV", "course", "video game"]
HISTORICAL_LINKS_FILE = "unreachable review links.txt"

def get_timezone(dt):
    if dt < datetime.datetime(2021, 8, 1):
        return pytz.timezone("US/Central")
    else:
        return pytz.timezone("US/Eastern")

def parse_date(date_str):
    if not date_str: return None
    try:
        date_str = date_str.replace('Sept', 'Sep').replace('Sepember', 'September')
        match = re.search(r'\((.*?)\)\s*(.*)', date_str)
        if match:
            date_part = match.group(1)
            time_part = match.group(2)
            naive_dt = date_parser.parse(f"{date_part} {time_part}")
        else:
            naive_dt = date_parser.parse(date_str, fuzzy=True)

        tz = get_timezone(naive_dt)
        naive = naive_dt.replace(tzinfo=None)
        localized = tz.localize(naive)
        return localized.astimezone(pytz.UTC).isoformat().replace('+00:00', 'Z')
    except Exception as e:
        print(f"Error parsing date '{date_str}': {e}")
        return None

def split_title_and_parenthetical(raw_text):
    parentheticals = []
    current_text = raw_text.strip()
    while True:
        match = re.search(r'\s*(\(([^)]+)\)|\[([^\]]+)\])$', current_text)
        if not match: break
        content = match.group(2) if match.group(2) else match.group(3)
        parentheticals.insert(0, content.strip())
        current_text = current_text[:match.start()].strip()
    return current_text, ", ".join(parentheticals)

def extract_standard_reviews(block, page_url):
    reviews = []
    h3_span = block.find('h3').find('span') if block.find('h3') else None
    if not h3_span: return reviews
    
    post_date_raw = h3_span.get_text(strip=True).split('-')[0].strip()
    post_date = parse_date(post_date_raw)
    if not post_date: return reviews

    p_tag = block.find('p')
    if not p_tag: return reviews

    content_html = str(p_tag)
    if '<b data-widget="ljcut"' in content_html.lower():
        content_html = content_html.split('<b data-widget="ljcut"')[0]
    
    lines = re.split(r'<br\s*/?>', content_html, flags=re.IGNORECASE)
    current_media_type = None
    
    for line in lines:
        line_soup = BeautifulSoup(line, 'html.parser')
        text = line_soup.get_text(separator=' ').strip()
        if not text: continue

        found_mt = False
        for mt in MEDIA_TYPES:
            pattern = re.compile(rf'^{re.escape(mt)}s?:', re.IGNORECASE)
            match = pattern.match(text)
            if match:
                current_media_type, found_mt = mt, True
                break
        if not found_mt and text.lower().startswith("other:"):
            current_media_type = "other"
        # Extract items from links
        links = line_soup.find_all('a')
        for a in links:
            raw_a_text = a.get_text(separator=' ', strip=True)
            link_url = a.get('href', '')
            if 'cutid' in link_url.lower() or 'details behind the cut' in raw_a_text.lower() or raw_a_text.lower() == 'collapse':
                continue

            # If the link goes to wikipedia instead of livejournal, use the livejournal link to the page itself instead
            if 'wikipedia.org' in link_url.lower():
                link_url = page_url
            else:
                link_url = urljoin(page_url, link_url)

            i_tag = a.find('i')
            if i_tag:
                title_italic = i_tag.get_text(separator=' ', strip=True)
                if raw_a_text != title_italic:
                    title, parenthetical = split_title_and_parenthetical(raw_a_text)
                    if not parenthetical: title = title_italic
                else:
                    title, parenthetical = title_italic, ""
            else:
                title, parenthetical = split_title_and_parenthetical(raw_a_text)

            if title.strip() == '[spoilers]': continue
            if current_media_type is None: continue
            reviews.append({"title": title, "link": link_url, "media_type": current_media_type, "post_date": post_date, "parenthetical": parenthetical})
    return reviews

def extract_historical_reviews(soup, url):
    post_date = None
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string and 'Site.entry =' in script.string:
            try:
                match = re.search(r'Site\.entry\s*=\s*({.*?});', script.string)
                if match:
                    entry_json = json.loads(match.group(1))
                    if 'eventtime' in entry_json:
                        dt = datetime.datetime.fromtimestamp(entry_json['eventtime'], tz=pytz.UTC)
                        tz = get_timezone(dt.replace(tzinfo=None))
                        naive = dt.replace(tzinfo=None)
                        localized = tz.localize(naive)
                        post_date = localized.astimezone(pytz.UTC).isoformat().replace('+00:00', 'Z')
                        break
            except: pass

    if not post_date:
        date_meta = soup.find('span', class_='datetime') or soup.find('p', class_='aentry-head__date') or soup.find('time') or soup.find('td', class_='caption')
        post_date = parse_date(date_meta.get_text(strip=True)) if date_meta else None
    
    if not post_date: return []

    entry_content = soup.find('div', class_='entry-content') or \
                    soup.find('div', class_='asset-body') or \
                    soup.find('div', class_='aentry-post__text') or \
                    soup.find('td', class_='entry')
    if not entry_content: return []

    content_html = ""
    for child in entry_content.children:
        child_str = str(child).lower()
        if '<a name="cutid1"' in child_str or '<hr' in child_str or 'data-widget="ljcut"' in child_str:
            break
        content_html += str(child)
    
    if not content_html: return []
    
    lines = re.split(r'<br\s*/?>', content_html, flags=re.IGNORECASE)
    current_media_type, reviews = None, []

    for line in lines:
        line_soup = BeautifulSoup(line, 'html.parser')
        text = line_soup.get_text(separator=' ').strip()
        if not text: continue

        found_mt = False
        for mt in MEDIA_TYPES:
            pattern = re.compile(rf'^{re.escape(mt)}s?:', re.IGNORECASE)
            match = pattern.match(text)
            if match:
                current_media_type, found_mt = mt, True
                break
        if not found_mt and text.lower().startswith("other:"):
            current_media_type = "other"

        items = []
        links = line_soup.find_all('a')
        if links:
            for a in links:
                if 'ljcut' in str(a): continue
                items.append(a)
        else:
            italics = line_soup.find_all('i')
            items.extend(italics)

        for item in items:
            title_raw = item.get_text(separator=' ', strip=True)
            if not title_raw: continue
            
            parentheticals = []
            curr = item.next_sibling
            while curr:
                if isinstance(curr, str):
                    txt = curr.lstrip()
                    if not txt:
                        curr = curr.next_sibling
                        continue
                    m = re.match(r'^(\(([^)]+)\)|\[([^\]]+)\])', txt)
                    if m:
                        content = m.group(2) if m.group(2) else m.group(3)
                        parentheticals.append(content.strip())
                        curr_str = txt[m.end():].lstrip()
                        while True:
                            m2 = re.match(r'^(\(([^)]+)\)|\[([^\]]+)\])', curr_str)
                            if m2:
                                c2 = m2.group(2) if m2.group(2) else m2.group(3)
                                parentheticals.append(c2.strip())
                                curr_str = curr_str[m2.end():].lstrip()
                            else: break
                        break
                    else: break
                else: break
            
            if item.name == 'a':
                full_text = item.get_text(separator=' ', strip=True)
                i_tag = item.find('i')
                if i_tag:
                    title_italic = i_tag.get_text(separator=' ', strip=True)
                    if full_text != title_italic:
                        t, p = split_title_and_parenthetical(full_text)
                        if p:
                            title_raw = t
                            if p not in parentheticals: parentheticals.insert(0, p)
                        else: title_raw = title_italic

            parenthetical = ", ".join(parentheticals)
            link_url = url
            if item.name == 'a' and item.get('href'):
                candidate_url = item['href']
                if 'wikipedia.org' in candidate_url.lower():
                    link_url = url
                else:
                    link_url = urljoin(url, candidate_url)
            elif item.find_parent('a') and item.find_parent('a').get('href'):
                candidate_url = item.find_parent('a')['href']
                if 'wikipedia.org' in candidate_url.lower():
                    link_url = url
                else:
                    link_url = urljoin(url, candidate_url)

            if title_raw.strip() == '[spoilers]': continue
            if current_media_type is None: continue
            reviews.append({"title": title_raw, "link": link_url, "media_type": current_media_type, "post_date": post_date, "parenthetical": parenthetical})
    return reviews

def scrape():
    all_reviews = []
    
    # Map post IDs back to URLs from unreachable review links.txt
    historical_url_map = {}
    if os.path.exists(HISTORICAL_LINKS_FILE):
        with open(HISTORICAL_LINKS_FILE, 'r') as f:
            for line in f:
                url = line.strip()
                if not url.startswith('http'): continue
                match = re.search(r'/(\d+)\.html', url)
                if match: historical_url_map[match.group(1)] = url

    # 1. Historical Mode (Local)
    print("Processing local historical pages...")
    for filepath in glob.glob(os.path.join(PAGES_DIR, "historical_*.html")):
        post_id = re.search(r'historical_(.*?)\.html', filepath).group(1)
        url = historical_url_map.get(post_id, f"https://hujhax.livejournal.com/{post_id}.html")
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            all_reviews.extend(extract_historical_reviews(soup, url))

    # 2. Standard Mode (Local)
    print("Processing local standard tag pages...")
    for filepath in glob.glob(os.path.join(PAGES_DIR, "tag_skip_*.html")):
        skip = re.search(r'tag_skip_(\d+)\.html', filepath).group(1)
        url = f"https://hujhax.livejournal.com/?skip={skip}&tag=media%20update&style=mine"
        with open(filepath, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            blocks = soup.find_all('div', class_='H3Holder')
            for block in blocks:
                all_reviews.extend(extract_standard_reviews(block, url))

    seen, final = set(), []
    for r in all_reviews:
        k = (r['title'].lower(), r['link'], r['post_date'])
        if k not in seen:
            seen.add(k)
            final.append(r)
            
    final.sort(key=lambda x: x['post_date'] or '', reverse=True)
    with open(CSV_FILE, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=["title", "link", "media_type", "post_date", "parenthetical"])
        writer.writeheader()
        writer.writerows(final)
    print(f"Success! {len(final)} unique reviews saved to {CSV_FILE}")

if __name__ == "__main__":
    scrape()
