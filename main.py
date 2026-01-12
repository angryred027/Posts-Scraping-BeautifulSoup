import asyncio
import yaml
from pathlib import Path
from rich.console import Console
from rich.status import Status
from typing import List, Dict
from datetime import timezone
import json
from dotenv import load_dotenv
import os

from helper.database import check_db_connection, create_tables
from helper.post_repo import PostsRepository
from utils.log_debug import log_debug
from scrape.ninjatrader import NinjaTraderScraper
from scrape.elitetrader import EliteTraderScraper
from score.intent import IntentScorer
from smtp.send import EmailSender

# -----------------------------
# Load .env and YAML config helper
# -----------------------------

env = os.getenv("APP_ENV", "local")
load_dotenv(f".env.{env}")
smtp_password = str(os.getenv("SMTP_APP_PASSWORD"))

def load_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

console = Console()


# -----------------------------
# Main execution
# -----------------------------
async def main():
    app_config = load_yaml("config/app.yaml")
    email_config = load_yaml("config/email.yaml")
    sources_config = load_yaml("config/sources.yaml")
    keywords_config = load_yaml("config/keywords.yaml")
    scoring_config = load_yaml("config/scoring.yaml")

    if not app_config or not sources_config or not keywords_config or not scoring_config:
        log_debug("❌ Missing configuration files. Exiting.")
        return

    log_debug("✅ Configs loaded")

    if not await check_db_connection():
        log_debug("❌ DB not reachable. Exiting.")
        return

    log_debug("✅ Database connection OK")
    await create_tables()
    log_debug("✅ Database tables ready")

    posts = []
    scraper = EliteTraderScraper(
        headers = {
            "User-Agent": app_config['app']['user_agent']
        },
        base_url=sources_config['elitetrader']['base_url'],
        categories=sources_config['elitetrader']['categories'],
        max_posts_per_run=sources_config['elitetrader']['max_posts_per_run'],
        from_days_ago=app_config['app']['run_interval_days']
    )
    scraped_posts = await run_scraper(scraper)

    repo = PostsRepository()
    external_ids = [p["external_id"] for p in posts]
    existing_ids = await repo.get_existing_external_ids(
        platform="elitetrader",
        external_ids=external_ids,
    )
    new_posts = [
        p for p in scraped_posts
        if p["external_id"] not in existing_ids
    ]

    scorer = IntentScorer(
        scoring_config=scoring_config,
        keywords_config=keywords_config
    )

    with console.status(
        "[bold cyan]Scoring posts and sorting...[/bold cyan]",
        spinner="dots"
    ):
        scored_posts = scorer.score_posts(new_posts)
        filtered_posts = [
            p for p in new_posts
            if p["intent_score"] and p["intent_score"] >= scoring_config['thresholds']['minimum_score']
        ]
        filtered_posts.sort(key=lambda x: x.get("intent_score", 0), reverse=True)
        posts = filtered_posts.copy()

    sender = EmailSender(
        host=email_config["smtp"]["host"],
        port=email_config["smtp"]["port"],
        username=email_config["smtp"]["username"],
        password=smtp_password,
        sender=email_config["smtp"]["sender"],
        recipients=email_config["smtp"]["recipients"],
    )   
    if posts and len(posts) > 0:
        email_body = sender._build_html(posts)
        sender.send_email(
            subject=f"({email_config['subject']}) - ({len(filtered_posts)}) posts",
            posts=filtered_posts
        )
        normalized_posts = normalize_engagement(posts)
        await repo.insert_posts(normalized_posts)

        posts_file = Path("debug/elitetrader_posts.yaml")
        email_file = Path("debug/posts_email.html")
        posts_file.parent.mkdir(parents=True, exist_ok=True)
        email_file.parent.mkdir(parents=True, exist_ok=True)

        with open(posts_file, "w", encoding="utf-8") as f:
            yaml.dump(posts, f, allow_unicode=True)
        with open(email_file, "w", encoding="utf-8") as f:
            f.write(email_body)

        log_debug(f"Saved {len(posts)} posts to {posts_file}")
    else: 
        log_debug("No new posts to save.")

async def run_scraper(scraper):
    with console.status("[bold green]Scraping EliteTrader...[/bold green]", spinner="dots"):
        posts = await scraper.scrape_posts()
    return posts

def normalize_engagement(posts: List[Dict]) -> List[Dict]:
    for post in posts:
        post["engagement"] = json.dumps({
            "views": int(post.get("views", 0)),
            "replies": int(post.get("replies", 0)),
        })
        post["published_at"] = normalize_datetime(post.get("published_at"))
    return posts

def normalize_datetime(dt):
    if dt is None:
        return None
    if dt.tzinfo:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt

if __name__ == "__main__":
    asyncio.run(main())