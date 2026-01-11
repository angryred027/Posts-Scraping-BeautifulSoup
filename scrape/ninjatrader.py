import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import re
from datetime import datetime

from utils.log_debug import log_debug

# -----------------------------
# NinjaTrader Forum Scraper
# -----------------------------
class NinjaTraderScraper:
    def __init__(self, headers: Dict[str, str], base_url: str, categories: List[str], max_posts_per_run, timeout: int = 10):
        self.headers = headers
        self.base_url = base_url
        self.categories = categories
        self.max_posts_per_run = max_posts_per_run
        self.timeout = timeout
    
    def scrape_posts(self) -> List[Dict]:
        response = requests.get(
            self.categories[0],
            headers = self.headers,
            timeout = self.timeout
        )

        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        posts: List[Dict] = []

        for link in soup.select("a[href*='/forum/']"):
            title = link.get_text(strip=True)
            href = link.get("href", "")

            if not title or not href:
                continue
            
            match = re.search(r"/(\d+)-", href)
            if not match:
                continue

            external_id = match.group(1)
            url = href if href.startswith("http") else f"{self.base_url}{href}"

            posts.append({
                "platform": "ninjatrader",
                "source": self.categories[0],
                "external_id": external_id,
                "url": url,
                "title": title,
                "content": "",  
                "author": "",   
                "published_at": datetime.now(),  
            })

            if len(posts) >= self.max_posts_per_run:
                break
        
        log_debug(f"✅ Scraped {len(posts)} posts from NinjaTrader")
        return posts