"""
scheduler.py — Run this SEPARATELY alongside your Streamlit app.
It checks every 30 seconds and publishes due posts automatically.

Run in a separate terminal:
    python scheduler.py
"""

import json
import time
import requests
import pathlib
from datetime import datetime

QUEUE_FILE  = pathlib.Path("queue_data.json")
CONFIG_FILE = pathlib.Path("config_data.json")

def load_json(path):
    try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {} if path == CONFIG_FILE else []

def save_queue(queue):
    try:
        with open(QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump(queue, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[ERROR] Could not save queue: {e}")

def publish(platform, message, image_url, link_url, config):
    print(f"  → Publishing to {platform}...")

    if platform == "Facebook":
        page_id = config.get("fb_page_id", "")
        token   = config.get("fb_token", "")
        if not page_id or not token:
            return {"error": "Facebook credentials missing."}
        if image_url:
            r = requests.post(
                f"https://graph.facebook.com/{page_id}/photos",
                data={"url": image_url, "caption": message, "access_token": token, "published": True},
                timeout=30,
            )
        else:
            payload = {"message": message, "access_token": token}
            if link_url:
                payload["link"] = link_url
            r = requests.post(f"https://graph.facebook.com/{page_id}/feed", data=payload, timeout=30)
        return r.json()

    elif platform == "Instagram":
        user_id = config.get("ig_user_id", "")
        token   = config.get("ig_token", "")
        if not user_id or not token:
            return {"error": "Instagram credentials missing."}
        img = image_url or "https://picsum.photos/1080/1080"
        c = requests.post(
            f"https://graph.facebook.com/v25.0/{user_id}/media",
            data={"image_url": img, "caption": message, "access_token": token}, timeout=30,
        ).json()
        if "error" in c:
            return {"error": c["error"]["message"]}
        return requests.post(
            f"https://graph.facebook.com/v25.0/{user_id}/media_publish",
            data={"creation_id": c.get("id"), "access_token": token}, timeout=30,
        ).json()

    elif platform == "LinkedIn":
        token = config.get("li_access_token", "")
        if not token:
            return {"error": "LinkedIn credentials missing."}
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "LinkedIn-Version": "202401",
            "X-Restli-Protocol-Version": "2.0.0",
        }
        me = requests.get("https://api.linkedin.com/v2/userinfo", headers=headers, timeout=15)
        if me.status_code != 200:
            return {"error": f"LinkedIn auth failed: {me.text}"}
        urn = f"urn:li:person:{me.json().get('sub')}"
        body = {
            "author": urn, "commentary": message, "visibility": "PUBLIC",
            "distribution": {"feedDistribution": "MAIN_FEED", "targetEntities": [], "thirdPartyDistributionChannels": []},
            "lifecycleState": "PUBLISHED", "isReshareDisabledByAuthor": False,
        }
        r = requests.post("https://api.linkedin.com/rest/posts", headers=headers, json=body, timeout=30)
        if r.status_code in [200, 201]:
            return {"id": r.headers.get("x-restli-id", "posted")}
        return {"error": r.text}

    elif platform == "X (Twitter)":
        try:
            import tweepy
            vals = [config.get(k, "") for k in ["tw_api_key", "tw_api_secret", "tw_access_token", "tw_access_secret"]]
            if not all(vals):
                return {"error": "Twitter credentials missing."}
            client = tweepy.Client(
                consumer_key=vals[0], consumer_secret=vals[1],
                access_token=vals[2], access_token_secret=vals[3],
            )
            resp = client.create_tweet(text=message[:280])
            return {"id": resp.data["id"]}
        except ImportError:
            return {"error": "tweepy not installed."}
        except Exception as e:
            return {"error": str(e)}

    return {"error": f"Unknown platform: {platform}"}


def check_and_publish():
    config = load_json(CONFIG_FILE)
    queue  = load_json(QUEUE_FILE)
    now    = datetime.now()
    changed = False

    for item in queue:
        if item.get("status") != "scheduled":
            continue
        scheduled_time = item.get("scheduled_time")
        if not scheduled_time:
            continue
        try:
            sched = datetime.strptime(scheduled_time, "%Y-%m-%d %H:%M")
        except Exception:
            continue

        if now < sched:
            continue  # Not time yet

        print(f"\n[{now.strftime('%H:%M:%S')}] Due: '{item.get('service')}' scheduled for {scheduled_time}")

        all_ok = True
        errors = {}
        for platform, text in item.get("posts", {}).items():
            result = publish(platform, text, item.get("image_url"), item.get("link_url"), config)
            if "error" in result:
                print(f"  ✗ {platform}: {result['error']}")
                errors[platform] = result["error"]
                all_ok = False
            else:
                print(f"  ✓ {platform}: published (id={result.get('id','')})")

        item["status"]       = "posted" if all_ok else "failed"
        item["published_at"] = now.strftime("%Y-%m-%d %H:%M")
        if errors:
            item["errors"] = errors
        changed = True

    if changed:
        save_queue(queue)
        print(f"[{now.strftime('%H:%M:%S')}] Queue updated on disk.")


print("=" * 50)
print("  AI Social Media Agent — Scheduler")
print("  Checking every 30 seconds for due posts")
print("  Press Ctrl+C to stop")
print("=" * 50)

while True:
    try:
        check_and_publish()
    except KeyboardInterrupt:
        print("\nScheduler stopped.")
        break
    except Exception as e:
        print(f"[ERROR] {e}")
    time.sleep(30)
