import os
from datetime import datetime

# YouTube Data API
API_KEY = os.environ.get("YOUTUBE_API_KEY", "")

# Countries to fetch trending videos from
COUNTRIES = {
    "US": "United States",
    "IN": "India",
    "GB": "United Kingdom",
    "BR": "Brazil",
    "JP": "Japan",
    "DE": "Germany",
}

# How many trending videos to fetch per country (max 50 per request)
MAX_RESULTS_PER_COUNTRY = 50

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
DATA_PROCESSED_DIR = os.path.join(BASE_DIR, "data", "processed")

# Current run month
RUN_MONTH = datetime.now().strftime("%Y-%m")

# YouTube video category mapping (fallback if API call fails)
CATEGORY_FALLBACK = {
    "1": "Film & Animation",
    "2": "Autos & Vehicles",
    "10": "Music",
    "15": "Pets & Animals",
    "17": "Sports",
    "18": "Short Movies",
    "19": "Travel & Events",
    "20": "Gaming",
    "21": "Videoblogging",
    "22": "People & Blogs",
    "23": "Comedy",
    "24": "Entertainment",
    "25": "News & Politics",
    "26": "Howto & Style",
    "27": "Education",
    "28": "Science & Technology",
    "29": "Nonprofits & Activism",
    "30": "Movies",
    "43": "Shows",
}
