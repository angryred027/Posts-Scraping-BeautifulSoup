import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import re
from datetime import datetime, timedelta

from utils.log_debug import log_debug

class EliteTraderScraper:
    def __init__(
        self,
        headers: Dict[str, str],
        base_url: str,
        categories: List[Dict],
        max_posts_per_run: int,
        from_days_ago: int = 1,
        timeout: int = 10
    ):
        self.headers = headers
        self.base_url = base_url.rstrip("/")
        self.categories = categories
        self.from_days_ago = from_days_ago
        self.max_posts_per_run = max_posts_per_run
        self.timeout = timeout

    def _get_last_page_number(self, soup: BeautifulSoup) -> int:
        page_numbers = []

        for a in soup.select("nav.pageNavWrapper a"):
            text = a.get_text(strip=True)
            if text.isdigit():
                page_numbers.append(int(text))

        return max(page_numbers) if page_numbers else 1

    def scrape_posts(self) -> List[Dict]:
        posts: List[Dict] = []
        from_date = datetime.now() - timedelta(days=self.from_days_ago)

        for category in self.categories:
            base_url = category["url"].rstrip("/")

            # ---- page 1 ----
            response = requests.get(base_url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            last_page = self._get_last_page_number(soup)
            log_debug(f"Pagination detected: {last_page} pages")

            for page in range(1, last_page + 1):
                if page == 1:
                    page_url = base_url
                else:
                    page_url = f"{base_url}/page-{page}"

                response = requests.get(page_url, headers=self.headers, timeout=self.timeout)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")

                items = soup.select("div.structItem.structItem--thread")
                if not items:
                    break

                stop = False

                for item in items:
                    link = item.select_one("div.structItem-title a[href*='/threads/']")
                    if not link:
                        continue

                    title = link.get_text(strip=True)
                    href = link.get("href", "")

                    match = re.search(r"\.(\d+)/?$", href)
                    if not match:
                        continue

                    external_id = match.group(1)
                    post_url = href if href.startswith("http") else f"{self.base_url}{href}"

                    time_tag = item.select_one("time.structItem-latestDate")
                    if time_tag and time_tag.has_attr("datetime"):
                        published_at = datetime.fromisoformat(time_tag["datetime"])
                    else:
                        published_at = datetime.now()

                    if published_at.date() < from_date.date():
                        stop = True
                        break

                    posts.append({
                        "platform": "elitetrader",
                        "external_id": external_id,
                        "url": post_url,
                        "title": title,
                        "content": "",
                        "author": "",
                        "published_at": published_at,
                    })

                    if len(posts) >= self.max_posts_per_run:
                        stop = True
                        break

                if stop:
                    break

        log_debug(f"✅ Scraped {len(posts)} posts from EliteTrader")
        return posts
