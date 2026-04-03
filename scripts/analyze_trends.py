"""Analyze trending video data and generate insights."""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import config


def load_data(month=None):
    """Load the combined trending JSON for a given month."""
    month = month or config.RUN_MONTH
    filepath = os.path.join(config.DATA_RAW_DIR, month, "trending_all.json")
    if not os.path.exists(filepath):
        print(f"No data found at {filepath}")
        sys.exit(1)
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return pd.DataFrame(data)


def duration_bucket(seconds):
    """Categorize video duration into buckets."""
    if seconds < 60:
        return "< 1 min (Shorts)"
    elif seconds < 300:
        return "1-5 min"
    elif seconds < 600:
        return "5-10 min"
    elif seconds < 1200:
        return "10-20 min"
    else:
        return "20+ min"


def analyze(data):
    """Generate all trend insights from the dataframe."""
    insights = {}

    # --- Global category breakdown ---
    cat_global = (
        data.groupby("category_name").agg(
            video_count=("video_id", "count"),
            total_views=("view_count", "sum"),
            avg_views=("view_count", "mean"),
            avg_likes=("like_count", "mean"),
            avg_comments=("comment_count", "mean"),
        )
        .sort_values("video_count", ascending=False)
        .round(0)
    )
    insights["category_global"] = cat_global.reset_index().to_dict(orient="records")

    # --- Category × Country matrix (video count) ---
    cat_country = (
        data.groupby(["country", "category_name"])["video_id"]
        .count()
        .unstack(fill_value=0)
    )
    insights["category_country_matrix"] = {
        "countries": cat_country.index.tolist(),
        "categories": cat_country.columns.tolist(),
        "data": cat_country.values.tolist(),
    }

    # --- Top channels ---
    top_channels = (
        data.groupby(["channel_title", "channel_id"])
        .agg(
            appearances=("video_id", "count"),
            total_views=("view_count", "sum"),
        )
        .sort_values("appearances", ascending=False)
        .head(20)
        .reset_index()
    )
    insights["top_channels"] = top_channels.to_dict(orient="records")

    # --- Duration distribution ---
    data["duration_bucket"] = data["duration_seconds"].apply(duration_bucket)
    duration_dist = (
        data["duration_bucket"]
        .value_counts()
        .reindex(["< 1 min (Shorts)", "1-5 min", "5-10 min", "10-20 min", "20+ min"])
        .fillna(0)
        .astype(int)
    )
    insights["duration_distribution"] = duration_dist.to_dict()

    # --- Cross-country trends (categories trending in 4+ countries) ---
    cat_per_country = data.groupby("category_name")["country"].nunique()
    global_trends = cat_per_country[cat_per_country >= 4].index.tolist()
    insights["global_trending_categories"] = global_trends

    local_only = cat_per_country[cat_per_country == 1]
    local_details = {}
    for cat in local_only.index:
        country = data[data["category_name"] == cat]["country"].iloc[0]
        local_details[cat] = country
    insights["local_only_categories"] = local_details

    # --- Key takeaways (auto-generated text) ---
    takeaways = []
    top_cat = cat_global.index[0]
    top_cat_count = int(cat_global.iloc[0]["video_count"])
    takeaways.append(
        f"**{top_cat}** dominates trending with {top_cat_count} videos across all countries."
    )

    highest_avg_views_cat = cat_global["avg_views"].idxmax()
    highest_avg = int(cat_global.loc[highest_avg_views_cat, "avg_views"])
    takeaways.append(
        f"**{highest_avg_views_cat}** has the highest average views per video ({highest_avg:,})."
    )

    top_ch = top_channels.iloc[0]["channel_title"]
    top_ch_count = int(top_channels.iloc[0]["appearances"])
    takeaways.append(
        f"**{top_ch}** appears {top_ch_count} times in trending — the most of any channel."
    )

    top_duration = duration_dist.idxmax()
    takeaways.append(
        f"Most trending videos are **{top_duration}** long."
    )

    if global_trends:
        takeaways.append(
            f"Categories trending globally (4+ countries): {', '.join(global_trends)}."
        )

    insights["key_takeaways"] = takeaways

    return insights


def parse_args():
    parser = argparse.ArgumentParser(description="Analyze YouTube trending data")
    parser.add_argument(
        "--month", default=config.RUN_MONTH,
        help="Month to analyze, e.g. --month 2026-03 (default: %(default)s)",
    )
    parser.add_argument(
        "--input-file", default=None,
        help="Override input CSV path",
    )
    parser.add_argument(
        "--output-dir", default=None,
        help="Override output directory",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    args.month = args.month or config.RUN_MONTH

    if args.input_file:
        if not os.path.exists(args.input_file):
            print(f"No data found at {args.input_file}")
            sys.exit(1)
        with open(args.input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        data = pd.DataFrame(data)
    else:
        data = load_data(args.month)

    print(f"Loaded {len(data)} videos")
    insights = analyze(data)

    print("\n--- Key Takeaways ---")
    for t in insights["key_takeaways"]:
        print(f"  • {t}")

    output_dir = args.output_dir or os.path.join(config.DATA_PROCESSED_DIR, args.month)
    os.makedirs(output_dir, exist_ok=True)

    summary = data.groupby(["country", "category_name"]).agg(
        video_count=("video_id", "count"),
        total_views=("view_count", "sum"),
        avg_views=("view_count", "mean"),
        avg_likes=("like_count", "mean"),
    ).round(0).reset_index()

    with open(os.path.join(output_dir, "summary.json"), "w") as f:
        json.dump(summary.to_dict(orient="records"), f, indent=2, default=str)

    with open(os.path.join(output_dir, "insights.json"), "w") as f:
        json.dump(insights, f, indent=2, default=str)

    print(f"Analysis saved to {output_dir}")


if __name__ == "__main__":
    main()
