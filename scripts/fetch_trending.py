"""Fetch trending YouTube videos from multiple countries using YouTube Data API v3."""

import argparse
import json
import os
import sys
import re

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import config


def parse_duration(duration_str):
    """Convert ISO 8601 duration (PT1H2M3S) to total seconds."""
    match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration_str or "")
    if not match:
        return 0
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds


def fetch_categories(youtube, region_code="US"):
    """Fetch video category names from the API."""
    try:
        response = youtube.videoCategories().list(
            part="snippet", regionCode=region_code
        ).execute()
        return {
            item["id"]: item["snippet"]["title"]
            for item in response.get("items", [])
        }
    except HttpError:
        return config.CATEGORY_FALLBACK


def fetch_trending_videos(youtube, region_code, categories, max_results=50):
    """Fetch trending videos for a given country."""
    videos = []
    next_page_token = None
    fetched = 0

    while fetched < max_results:
        per_page = min(50, max_results - fetched)
        try:
            response = youtube.videos().list(
                part="snippet,statistics,contentDetails",
                chart="mostPopular",
                regionCode=region_code,
                maxResults=per_page,
                pageToken=next_page_token,
            ).execute()
        except HttpError as e:
            print(f"  Error fetching {region_code}: {e}")
            break

        for item in response.get("items", []):
            snippet = item["snippet"]
            stats = item.get("statistics", {})
            content = item.get("contentDetails", {})
            category_id = snippet.get("categoryId", "")

            videos.append({
                "video_id": item["id"],
                "title": snippet.get("title", ""),
                "channel_title": snippet.get("channelTitle", ""),
                "channel_id": snippet.get("channelId", ""),
                "category_id": category_id,
                "category_name": categories.get(category_id, "Unknown"),
                "published_at": snippet.get("publishedAt", ""),
                "tags": "|".join(snippet.get("tags", [])),
                "view_count": int(stats.get("viewCount", 0)),
                "like_count": int(stats.get("likeCount", 0)),
                "comment_count": int(stats.get("commentCount", 0)),
                "duration_seconds": parse_duration(content.get("duration", "")),
                "country": region_code,
            })

        fetched += len(response.get("items", []))
        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    return videos


def save_json(videos, filepath):
    """Save video list to JSON."""
    if not videos:
        return
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(videos, f, indent=2, ensure_ascii=False)


def parse_args():
    parser = argparse.ArgumentParser(description="Fetch YouTube trending videos")
    parser.add_argument(
        "--month", default=config.RUN_MONTH,
        help="Target month folder name, e.g. --month 2026-03 (default: %(default)s)",
    )
    parser.add_argument(
        "--countries", nargs="+", default=list(config.COUNTRIES.keys()),
        help="Country codes to fetch, e.g. --countries US IN GB (default: %(default)s)",
    )
    parser.add_argument(
        "--max-results", type=int, default=config.MAX_RESULTS_PER_COUNTRY,
        help="Max trending videos per country, e.g. --max-results 20 (default: %(default)s)",
    )
    parser.add_argument(
        "--output-dir", default=None,
        help="Override output directory, e.g. --output-dir ./my_data (default: data/raw/<month>)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    args.month = args.month or config.RUN_MONTH

    api_key = config.API_KEY
    if not api_key:
        print("ERROR: No API key provided.")
        print("Set YOUTUBE_API_KEY env var")
        sys.exit(1)

    youtube = build("youtube", "v3", developerKey=api_key)
    categories = fetch_categories(youtube)

    output_dir = args.output_dir or os.path.join(config.DATA_RAW_DIR, args.month)
    countries = {c: config.COUNTRIES.get(c, c) for c in args.countries}
    all_videos = []

    for code, name in countries.items():
        print(f"Fetching trending videos for {name} ({code})...")
        videos = fetch_trending_videos(
            youtube, code, categories, args.max_results
        )
        print(f"  Got {len(videos)} videos")

        filepath = os.path.join(output_dir, f"trending_{code}.json")
        save_json(videos, filepath)
        all_videos.extend(videos)

    # Save combined file
    combined_path = os.path.join(output_dir, "trending_all.json")
    save_json(all_videos, combined_path)
    print(f"\nTotal: {len(all_videos)} videos saved to {output_dir}")


if __name__ == "__main__":
    main()
