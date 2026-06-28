import json
import logging
import urllib.request
import urllib.error
from app.config import settings
from app.scraper import KEYWORDS

logger = logging.getLogger(__name__)

def find_matched_keywords(post_data: dict) -> str:
    title = post_data.get("title", "")
    body = post_data.get("body_text", "")
    content = f"{title} {body}".lower()
    matched = [kw for kw in KEYWORDS if kw.lower() in content]
    return ", ".join(matched) if matched else "None"

def send_webhook_notification(post_data: dict) -> bool:
    """
    Formats and dispatches an interactive reply card payload to a configured
    Slack/Discord webhook, enabling 1-click approvals for manual outreach.
    """
    webhook_url = settings.WEBHOOK_URL
    
    # Determine matched keyword
    keyword_match = find_matched_keywords(post_data)
    
    # Extract details
    title = post_data.get("title", "No Title")
    subreddit = post_data.get("subreddit", "Unknown")
    author = post_data.get("author", "Unknown")
    permalink = post_data.get("permalink", "")
    body_text = post_data.get("body_text", "")
    
    # Truncate text to avoid hitting payload limits
    max_text_len = 1000
    body_truncated = body_text if len(body_text) <= max_text_len else body_text[:max_text_len] + "..."
    
    # Format payload depending on URL signature
    # Default to Discord if signature doesn't specify Slack
    is_slack = webhook_url and "hooks.slack.com" in webhook_url
    
    if is_slack:
        # Slack Block Kit blocks
        payload = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": "🚨 NEW LEADER EVENT DETECTED",
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Title:* {title}\n*Subreddit:* r/{subreddit}\n*Author:* {author}\n*Keyword Match:* {keyword_match}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Raw Text:*\n{body_truncated}"
                    }
                }
            ]
        }
        
        # Add direct button / link context block
        context_elements = []
        if permalink:
            context_elements.append({
                "type": "mrkdwn",
                "text": f"<{permalink}|View on Reddit>"
            })
            
        if context_elements:
            payload["blocks"].append({
                "type": "context",
                "elements": context_elements
            })
            
        # Add interactive action button for outreach approval
        if permalink:
            payload["blocks"].append({
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Approve & Outreach",
                            "emoji": True
                        },
                        "url": permalink,
                        "style": "primary"
                    }
                ]
            })
    else:
        # Discord Embed / generic embeds
        # Discord expects color as a decimal integer: #E74C3C is 15158332
        payload = {
            "embeds": [
                {
                    "title": "🚨 NEW LEADER EVENT DETECTED",
                    "description": f"**Title:** {title}",
                    "color": 15158332,
                    "fields": [
                        {
                            "name": "Subreddit",
                            "value": f"r/{subreddit}",
                            "inline": True
                        },
                        {
                            "name": "Author",
                            "value": author,
                            "inline": True
                        },
                        {
                            "name": "Keyword Match",
                            "value": keyword_match,
                            "inline": True
                        }
                    ]
                }
            ]
        }
        
        if permalink:
            payload["embeds"][0]["fields"].append({
                "name": "Reddit URL",
                "value": f"[Link to Post]({permalink})",
                "inline": False
            })
            
        if body_truncated:
            payload["embeds"][0]["fields"].append({
                "name": "Raw Text",
                "value": body_truncated,
                "inline": False
            })
            
    # Handle empty webhook_url gracefully
    if not webhook_url:
        logger.warning(
            "WEBHOOK_URL is empty. Notification was not sent. Formatted payload was:\n%s",
            json.dumps(payload, indent=2, ensure_ascii=False)
        )
        return False
        
    # Dispatch the webhook using urllib.request
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            webhook_url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "ReguShield-Notification-Worker/1.0"
            },
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            status_code = response.getcode()
            response_body = response.read().decode("utf-8")
            
        if 200 <= status_code < 300:
            logger.info(f"Notification successfully sent to webhook. Response status: {status_code}")
            return True
        else:
            logger.error(f"Failed to send webhook notification. Status: {status_code}, Response: {response_body}")
            return False
            
    except urllib.error.HTTPError as e:
        error_body = ""
        try:
            error_body = e.read().decode("utf-8")
        except Exception:
            pass
        logger.error(f"HTTP Error while sending webhook: {e.code} {e.reason}. Response: {error_body}")
        return False
    except urllib.error.URLError as e:
        logger.error(f"URL Error while sending webhook: {e.reason}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error while sending webhook: {e}", exc_info=True)
        return False
