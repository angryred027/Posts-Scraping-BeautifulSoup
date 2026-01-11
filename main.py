import asyncio
import yaml
from pathlib import Path

from helper.database import check_db_connection, create_tables
from utils.log_debug import log_debug
from scrape.ninjatrader import NinjaTraderScraper
from scrape.elitetrader import EliteTraderScraper

# -----------------------------
# Load YAML config helper
# -----------------------------
def load_yaml(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

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

    # 3) (Next steps)
    # - scrape posts
    scraper = EliteTraderScraper(
        headers = {
            "User-Agent": app_config['app']['user_agent']
        },
        base_url=sources_config['elitetrader']['base_url'],
        categories=sources_config['elitetrader']['categories'],
        max_posts_per_run=sources_config['elitetrader']['max_posts_per_run'],
        from_days_ago=app_config['app']['run_interval_days']
    )
    posts = scraper.scrape_posts()

    if posts and len(posts) > 0:
        with open("debug/elitetrader_posts.yaml", "w", encoding="utf-8") as f:
            yaml.dump(posts, f, allow_unicode=True)
        
        log_debug(f"✅ Saved {len(posts)} scraped posts to debug/elitetrader_posts.yaml")

    # - score posts
    # - build digest
    # - send email


if __name__ == "__main__":
    asyncio.run(main())