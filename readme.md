# EliteTrader Post Scraper

This project scrapes posts from EliteTrader forum categories, scores them, and sends a digest email via SMTP.

---

## Requirements

- Python **3.12+**
- PostgreSQL database
- SMTP email account with app password

---

## Setup

1. **Create and activate a virtual environment**

   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS / Linux
   source venv/bin/activate
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure application settings**

   - `app.yaml` → `run_interval_days`: Number of days back to scrape posts
   - `email.yaml` → SMTP settings (server, port, username, password/app password)
   - `scoring.yaml` → `minimum_score` threshold for posts
   - `sources.yaml` → `max_posts_per_run` (max posts to scrape per run)

4. **Environment variables**

   - Create `.env.local` and set any required secrets (DB URL, email credentials, etc.)

5. **Set up PostgreSQL database**

   - Create the database

6. **Set up SMTP app password**

   - For Gmail, generate an app password to use in `email.yaml`

---

## Running the scraper

- On Windows, simply run:

  ```cmd
  run.cmd
  ```

- Linux / macOS:

  ```bash
  python3 main.py
  ```

- The script will:

  1. Scrape posts from EliteTrader
  2. Score posts based on thresholds
  3. Send a digest email via SMTP

---

## Notes

- `max_posts_per_run` limits the number of posts scraped per run.
- `run_interval_days` determines how far back posts are collected.
- Make sure your SMTP account allows app passwords or less-secure access if required.

---
