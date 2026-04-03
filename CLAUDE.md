# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

YD_data_center is a zero-cost automation pipeline that fetches YouTube trending video data monthly, analyzes content trends, and generates insight reports. The goal is to identify what types of content are most viewed and trending on YouTube.

## Tech Stack

- **Python 3.x** — data fetching, processing, and analysis
- **YouTube Data API v3** — trending video data (free tier: 10,000 quota units/day)
- **GitHub Actions** — monthly cron-based automation (free tier)
- **pandas** — data analysis and categorization
- **CSV/JSON** — data storage (committed to repo)
- **Jinja2 + Chart.js** — HTML dashboard generation

## Architecture

- `config.py` — central configuration (countries, paths, API settings)
- `scripts/fetch_trending.py` — fetches trending videos via YouTube API → `data/raw/YYYY-MM/`
- `scripts/analyze_trends.py` — pandas analysis → `data/processed/YYYY-MM/insights.json`
- `scripts/generate_dashboard.py` — renders Jinja2 template → `reports/YYYY-MM/dashboard.html`
- `templates/dashboard.html` — Jinja2 + Chart.js HTML template
- `.github/workflows/monthly_trending.yml` — monthly cron + manual trigger

## Commands

```bash
pip install -r requirements.txt
export YOUTUBE_API_KEY='your-key'
python scripts/fetch_trending.py          # fetch data
python scripts/analyze_trends.py          # analyze
python scripts/generate_dashboard.py      # generate HTML dashboard
```

Pipeline: fetch → analyze → generate_dashboard (must run in order).

## Key Design Decisions

- All data is stored as flat files (CSV/JSON) in the repo to avoid database costs
- GitHub Actions runs on a monthly cron schedule to stay within free tier limits
- YouTube API key is stored as a GitHub Actions secret (`YOUTUBE_API_KEY`)
- Reports are auto-committed back to the repo after each run
