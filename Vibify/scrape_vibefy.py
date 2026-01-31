import requests
import os
from urllib.parse import urljoin, urlparse
import re

BASE_URL = "https://vibefy.ctf.pascalctf.it"
START_URL = "https://vibefy.ctf.pascalctf.it/home"
OUTPUT_DIR = "html_scraped"

def save_file(url, content):
    parsed = urlparse(url)
    path = parsed.path
    if path.startswith('/'):
        path = path[1:]
    if not path or path.endswith('/'):
        path += 'index.html'
    
    filepath = os.path.join(OUTPUT_DIR, path)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    with open(filepath, 'wb') as f:
        f.write(content)
    print(f"Saved: {filepath}")

def scrape():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    session = requests.Session()
    
    # 1. Fetch Home Page
    print(f"Fetching {START_URL}...")
    try:
        response = session.get(START_URL)
        response.raise_for_status()
        save_file(START_URL, response.content)
        html = response.text
    except Exception as e:
        print(f"Failed to fetch {START_URL}: {e}")
        return

    # 2. Extract Assets (Simple Regex for now, can use BS4 if installed)
    # Look for src="..." and href="..."
    
    # CSS
    css_links = re.findall(r'<link[^>]+href=["\'](.*?)["\']', html)
    # JS
    js_links = re.findall(r'<script[^>]+src=["\'](.*?)["\']', html)
    # Images
    img_links = re.findall(r'<img[^>]+src=["\'](.*?)["\']', html)
    
    all_assets = set(css_links + js_links + img_links)
    
    for link in all_assets:
        if link.startswith('data:'):
            continue
            
        full_url = urljoin(START_URL, link)
        if BASE_URL not in full_url:
            print(f"Skipping external link: {full_url}")
            continue
            
        print(f"Fetching asset: {full_url}")
        try:
            res = session.get(full_url)
            if res.status_code == 200:
                save_file(full_url, res.content)
            else:
                print(f"Failed to fetch {full_url}: Status {res.status_code}")
        except Exception as e:
            print(f"Error fetching {full_url}: {e}")

    # 3. Conduct a Search
    # We need to guess the search endpoint. Usually /search?q=...
    # Let's inspect the HTML form in the next step, but for now let's try a common one
    # Or just search for "flag" or "test"
    
    search_query = "PasalCTF"
    search_url = urljoin(BASE_URL, f"/search?q={search_query}")
    print(f"Attempting search: {search_url}")
    
    try:
        res = session.get(search_url)
        if res.status_code == 200:
            save_file(search_url + ".html", res.content) 
            print("Search successful, saved result.")
        else:
            print(f"Search endpoint might be different. Status: {res.status_code}")
    except Exception as e:
        print(f"Search failed: {e}")

    # 4. Fetch Songs Data
    songs_url = urljoin(BASE_URL, "/public/songs.json")
    print(f"Fetching songs data: {songs_url}")
    try:
        res = session.get(songs_url)
        if res.status_code == 200:
            save_file(songs_url, res.content)
            songs_data = res.json()
            
            # Download referenced assets in songs.json
            for song in songs_data:
                # Download Audio
                if 'url' in song:
                    song_url = urljoin(BASE_URL, song['url'])
                    print(f"Fetching song audio: {song_url}")
                    try:
                        s_res = session.get(song_url)
                        if s_res.status_code == 200:
                            save_file(song_url, s_res.content)
                    except Exception as e:
                        print(f"Failed to fetch audio {song_url}: {e}")

                # Download Lyrics
                if 'lyrics' in song:
                    lyrics_url = urljoin(BASE_URL, song['lyrics'])
                    print(f"Fetching lyrics: {lyrics_url}")
                    try:
                        l_res = session.get(lyrics_url)
                        if l_res.status_code == 200:
                            save_file(lyrics_url, l_res.content)
                    except Exception as e:
                        print(f"Failed to fetch lyrics {lyrics_url}: {e}")
        else:
            print(f"Failed to fetch songs.json: {res.status_code}")
    except Exception as e:
        print(f"Error fetching songs.json: {e}")

if __name__ == "__main__":
    scrape()
