import logging
import praw
from app.config import settings

logger = logging.getLogger(__name__)

# Target subreddits as specified in requirements
SUBREDDITS = [
    "FulfillmentByAmazon",
    "AmazonSeller",
    "Shopify",
    "ecommerce",
    "dropship",
    "TikTokShop"
]

# Core compliance and brand protection keywords from marketing blueprint
KEYWORDS = [
    "UKCA",
    "CE mark",
    "REACH compliance",
    "cosmetics portal",
    "customs seized",
    "toy safety directive",
    "buy box stolen",
    "ASIN hijack",
    "brand registry violation"
]

# Realistic mock posts for graceful local development fallback
MOCK_POSTS = [
    {
        "title": "Help! Shipment to UK customs seized!",
        "body_text": "My entire shipment of toy sets was customs seized at the UK port because of UKCA labeling. They are saying I don't have the toy safety directive documentation completed. What do I do? Is there any way to recover this?",
        "author": "anxious_seller123",
        "permalink": "https://www.reddit.com/r/FulfillmentByAmazon/comments/mock1/help_shipment_to_uk_customs_seized/",
        "created_utc": 1782542400.0,
        "subreddit": "FulfillmentByAmazon"
    },
    {
        "title": "Buy Box Stolen and ASIN Hijack by competitor",
        "body_text": "A hijacker just hopped onto my main listing and my buy box was stolen overnight! This is a clear brand registry violation. Does anyone have experience with getting an ASIN hijack resolved quickly? The support is taking forever.",
        "author": "shopify_ninja",
        "permalink": "https://www.reddit.com/r/AmazonSeller/comments/mock2/buy_box_stolen_and_asin_hijack_by_competitor/",
        "created_utc": 1782546000.0,
        "subreddit": "AmazonSeller"
    },
    {
        "title": "CE Mark and REACH compliance issues for EU market",
        "body_text": "We are trying to sell kitchenware in Germany. Amazon is asking for REACH compliance certificates and a CE mark declaration of conformity. We have no idea how to get these or where to start. Any advice?",
        "author": "eu_exporter",
        "permalink": "https://www.reddit.com/r/ecommerce/comments/mock3/ce_mark_and_reach_compliance_issues_for_eu/",
        "file_path": "ecommerce",
        "created_utc": 1782549600.0,
        "subreddit": "ecommerce"
    },
    {
        "title": "Cosmetics portal registration question",
        "body_text": "Is anyone selling beauty products on TikTok Shop? Do we need to register on the UK cosmetics portal (SCPN) or EU portal (CPNP)? Our supplier in China doesn't know what this is.",
        "author": "beauty_brand_owner",
        "permalink": "https://www.reddit.com/r/TikTokShop/comments/mock4/cosmetics_portal_registration_question/",
        "created_utc": 1782553200.0,
        "subreddit": "TikTokShop"
    }
]

def matches_keywords(title: str, body: str) -> bool:
    """
    Checks if any of the core compliance/brand protection keywords
    exist in the post's title or body text.
    """
    content = f"{title} {body}".lower()
    for kw in KEYWORDS:
        if kw.lower() in content:
            return True
    return False

def get_mock_posts(limit: int = 10):
    """
    Returns filtered mock posts matching keywords, up to the limit.
    """
    filtered = [p for p in MOCK_POSTS if matches_keywords(p["title"], p["body_text"])]
    return filtered[:limit]

def scan_subreddits(limit: int = 10):
    """
    Scans specified subreddits using PRAW and returns a list of matching
    posts filtered by brand protection and compliance keywords.
    Gracefully falls back to mock data if credentials are empty or invalid.
    """
    client_id = settings.REDDIT_CLIENT_ID
    client_secret = settings.REDDIT_CLIENT_SECRET
    user_agent = settings.REDDIT_USER_AGENT

    # Graceful fallback for local development if credentials are empty
    if not client_id or not client_secret:
        logger.warning(
            "Reddit API credentials (REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET) are not configured. "
            "Gracefully falling back to mock posts for local testing."
        )
        return get_mock_posts(limit)

    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )

        matched_posts = []

        for sub_name in SUBREDDITS:
            try:
                subreddit = reddit.subreddit(sub_name)
                seen_ids = set()
                submissions = []

                # Combine Hot and New posts for better brand surveillance
                for submission in subreddit.hot(limit=limit):
                    if submission.id not in seen_ids:
                        seen_ids.add(submission.id)
                        submissions.append(submission)

                for submission in subreddit.new(limit=limit):
                    if submission.id not in seen_ids:
                        seen_ids.add(submission.id)
                        submissions.append(submission)

                for submission in submissions:
                    title = submission.title or ""
                    body = submission.selftext or ""
                    author_name = submission.author.name if submission.author else "[deleted]"
                    
                    if matches_keywords(title, body):
                        permalink = submission.permalink or ""
                        if permalink and not permalink.startswith("http"):
                            permalink = f"https://www.reddit.com{permalink}"
                            
                        matched_posts.append({
                            "title": title,
                            "body_text": body,
                            "author": author_name,
                            "permalink": permalink,
                            "created_utc": submission.created_utc,
                            "subreddit": sub_name
                        })

            except Exception as e:
                logger.error(f"Error scanning subreddit r/{sub_name}: {e}")

        # Sort posts by creation time descending and apply limit
        matched_posts.sort(key=lambda x: x["created_utc"], reverse=True)
        return matched_posts[:limit]

    except Exception as e:
        logger.warning(
            f"An error occurred while initializing PRAW or scanning: {e}. "
            "Gracefully falling back to mock posts."
        )
        return get_mock_posts(limit)
