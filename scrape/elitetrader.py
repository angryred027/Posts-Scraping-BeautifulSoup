import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import re
from datetime import datetime, timedelta

from utils.log_debug import log_debug

# -----------------------------
# EliteTrader Forum Scraper
# -----------------------------
class EliteTraderScraper:
    def __init__(self, headers: Dict[str, str], base_url: str, categories: List[str], max_posts_per_run, timeout: int = 10):
        self.headers = headers
        self.base_url = base_url
        self.categories = categories
        self.max_posts_per_run = max_posts_per_run
        self.timeout = timeout
    
    def scrape_posts(self) -> List[Dict]:
        yesterday = datetime.now() - timedelta(days=1)
        response = requests.get(
            self.categories[0]['url'],
            headers = self.headers,
            timeout = self.timeout
        )

        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        posts: List[Dict] = []

        # for link in soup.select("a[href*='/forum/']"): # Adjusted selector to match NinjaTrader forum links
        for link in soup.select("a[href*='/threads/']"): # Adjusted selector to match EliteTrader forum links
            title = link.get_text(strip=True)
            href = link.get("href", "")

            if not title or not href:
                continue
            
            # match = re.search(r"/(\d+)-", href) # Adjusted regex to match NinjaTrader Post URLs
            match = re.search(r"\.(\d+)/?$", href) # Adjusted regex to match EliteTrader Post URLs
            if not match:
                continue

            external_id = match.group(1)
            url = href if href.startswith("http") else f"{self.base_url}{href}"

            posts.append({
                "platform": "elitetrader",
                "external_id": external_id,
                "url": url,
                "title": title,
                "content": "",  
                "author": "",   
                "published_at": datetime.now(),  
            })

            if len(posts) >= self.max_posts_per_run:
                break

        log_debug(f"✅ Scraped {len(posts)} posts from EliteTrader")
        return posts