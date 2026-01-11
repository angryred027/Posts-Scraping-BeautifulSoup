import asyncio
import aiohttp
import re
from bs4 import BeautifulSoup
from typing import List, Dict
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
        timeout: int = 15,
        max_retries: int = 3,
        delay: float = 1.2
    ):
        self.headers = headers
        self.base_url = base_url.rstrip("/")
        self.categories = categories
        self.from_days_ago = from_days_ago
        self.max_posts_per_run = max_posts_per_run
        self.timeout = timeout
        self.max_retries = max_retries
        self.delay = delay

    async def _fetch(self, session: aiohttp.ClientSession, url: str) -> str:
        for attempt in range(self.max_retries):
            try:
                async with session.get(url, timeout=self.timeout) as resp:
                    if resp.status == 200:
                        return await resp.text()
            except Exception:
                await asyncio.sleep(self.delay * (attempt + 1))
        return ""

    def _get_last_page_number(self, soup: BeautifulSoup) -> int:
        pages = []
        for a in soup.select("nav.pageNavWrapper a"):
            t = a.get_text(strip=True)
            if t.isdigit():
                pages.append(int(t))
        return max(pages) if pages else 1

    async def _scrape_thread(self, session: aiohttp.ClientSession, url: str) -> Dict:
        html = await self._fetch(session, url)
        if not html:
            return {}

        soup = BeautifulSoup(html, "html.parser")

        message = soup.select_one("article.message--post")
        if not message:
            return {}

        body = message.select_one("div.bbWrapper")
        content_html = str(body) if body else ""

        return {
            "content": content_html,
        }

    async def scrape_posts(self) -> List[Dict]:
        posts: List[Dict] = []
        from_date = datetime.utcnow() - timedelta(days=self.from_days_ago)

        timeout = aiohttp.ClientTimeout(total=self.timeout)
        connector = aiohttp.TCPConnector(limit=4)

        async with aiohttp.ClientSession(
            headers=self.headers,
            timeout=timeout,
            connector=connector
        ) as session:

            for category in self.categories:
                base_url = category["url"].rstrip("/")

                html = await self._fetch(session, base_url)
                if not html:
                    continue

                soup = BeautifulSoup(html, "html.parser")
                last_page = self._get_last_page_number(soup)

                for page in range(1, last_page + 1):
                    page_url = base_url if page == 1 else f"{base_url}/page-{page}"
                    html = await self._fetch(session, page_url)
                    if not html:
                        break

                    soup = BeautifulSoup(html, "html.parser")
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
                        author_tag = item.select_one("ul.structItem-parts a.username")
                        author = author_tag.get_text(strip=True) if author_tag else ""
                        replies = 0
                        views = 0

                        for pair in item.select("div.structItem-cell--meta dl.pairs"):
                            dt = pair.select_one("dt")
                            dd = pair.select_one("dd")
                            if not dt or not dd:
                                continue

                            label = dt.get_text(strip=True).lower()
                            value = int(re.sub(r"[^\d]", "", dd.get_text()) or 0)

                            if label == "replies":
                                replies = value
                            elif label == "views":
                                views = value

                        time_tag = item.select_one("time.structItem-latestDate")
                        if time_tag and time_tag.has_attr("datetime"):
                            published_at = datetime.fromisoformat(time_tag["datetime"])
                        else:
                            published_at = datetime.utcnow()

                        if published_at.date() < from_date.date():
                            stop = True
                            break



                        # thread = await self._scrape_thread(session, post_url)
                        # if not thread:
                        #     continue

                        posts.append({
                            "platform": "elitetrader",
                            "external_id": external_id,
                            "url": post_url,
                            "title": title,
                            "content": "",
                            "author": author,
                            "replies": replies,
                            "views": views,
                            "published_at": published_at
                        })

                        if len(posts) >= self.max_posts_per_run:
                            stop = True
                            break

                        await asyncio.sleep(self.delay)

                    if stop:
                        break

        log_debug(f"✅ Scraped {len(posts)} full EliteTrader posts")
        return posts
