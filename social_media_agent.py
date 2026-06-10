"""
╔══════════════════════════════════════════════════════════════╗
║       AI Social Media Agent  —  Digital Marketing            ║
║  Platforms : Facebook · X (Twitter) · Instagram · LinkedIn   ║
║  Services  : SEO · Citations · AI SEO · GBP · Marketing      ║
║  Text AI   : Google Gemini 2.5 Flash  (free)                 ║
║  Image AI  : Pollinations.AI (free · no key needed)          ║
╚══════════════════════════════════════════════════════════════╝

Run:
    pip install streamlit requests pillow google-generativeai tweepy apscheduler
    streamlit run social_media_agent.py
"""

import streamlit as st
import requests
import json
import time
import base64
import re
import pathlib
import os
from io import BytesIO
from datetime import datetime, timedelta
from urllib.parse import quote

# ─── PAGE CONFIG ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Social Media Agent",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CUSTOM CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@400;500;600;700&display=swap');
html, body, .stApp { font-family: 'Sora', sans-serif; }
.block-container { padding-top: 1.2rem; max-width: 1200px; }
h1 { font-size: 1.6rem !important; font-weight: 700 !important; }
h2 { font-size: 1.15rem !important; }
h3 { font-size: 1rem !important; }
.hero {
    background: linear-gradient(135deg, #1877f2 0%, #0a66c2 100%);
    border-radius: 12px; padding: 18px 24px; margin-bottom: 20px; color: white;
}
.hero h1 { color: white !important; margin: 0 !important; font-size: 1.5rem !important; }
.hero p  { color: rgba(255,255,255,0.85); margin: 4px 0 0; font-size: 13px; }
.post-preview {
    background: #fff; border: 1px solid #dddfe2; border-radius: 10px;
    overflow: hidden; margin: 6px 0 14px; font-size: 14px; color: #1c1e21;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
}
.preview-header { padding: 10px 14px 6px; display: flex; align-items: center; gap: 10px; }
.preview-avatar {
    width: 40px; height: 40px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 15px; color: white; flex-shrink: 0;
}
.preview-name { font-weight: 600; font-size: 14px; }
.preview-meta { font-size: 12px; color: #65676b; }
.preview-body { padding: 4px 14px 14px; white-space: pre-wrap; line-height: 1.65; }
.preview-actions { border-top: 1px solid #e4e6eb; padding: 4px 14px; font-size: 13px; color: #65676b; }
.queue-card { background: white; border: 1px solid #e5e7eb; border-radius: 10px; padding: 14px 16px; margin-bottom: 10px; }
.badge { display: inline-block; padding: 2px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; }
.badge-draft     { background: #fff8e1; color: #b45309; }
.badge-scheduled { background: #e8f5e9; color: #1a7f37; }
.badge-posted    { background: #e3f2fd; color: #0d5ea6; }
.badge-failed    { background: #fff0f0; color: #dc2626; }
.info-box  { background:#eef4ff; border:1px solid #b8d0ff; border-radius:8px; padding:10px 14px; font-size:13px; color:#2c5fbc; margin-bottom:12px; }
.warn-box  { background:#fffbeb; border:1px solid #fde68a; border-radius:8px; padding:10px 14px; font-size:13px; color:#92400e; margin-bottom:12px; }
.error-box { background:#fff0f0; border:1px solid #fca5a5; border-radius:8px; padding:10px 14px; font-size:13px; color:#dc2626; margin-bottom:12px; }
</style>
""", unsafe_allow_html=True)

# ─── CONSTANTS ────────────────────────────────────────────────────────────────
PLATFORMS = {
    "Facebook":    {"icon": "📘", "max_chars": 63206, "color": "#1877f2", "actions": "👍 Like · 💬 Comment · ↗ Share"},
    "X (Twitter)": {"icon": "𝕏",  "max_chars": 280,   "color": "#000000", "actions": "💬 Reply · 🔁 Repost · ❤️ Like"},
    "Instagram":   {"icon": "📸", "max_chars": 2200,   "color": "#e1306c", "actions": "❤️ Like · 💬 Comment · ↗ Share · 🔖 Save"},
    "LinkedIn":    {"icon": "💼", "max_chars": 3000,   "color": "#0a66c2", "actions": "👍 Like · 💬 Comment · ↗ Share · ✉️ Send"},
}

SERVICES = {
    "SEO":                    "search engine optimization, keyword rankings, on-page SEO, technical SEO, backlinks",
    "Local Citations":        "local citation building, NAP consistency, directory listings, local SEO presence",
    "AI SEO":                 "AI-driven SEO strategies, AI content optimization, machine learning for search, SGE/AI search visibility",
    "GBP Optimization":       "Google Business Profile optimization, local pack rankings, GBP posts, reviews, Q&A",
    "Link Building":          "link building, backlink acquisition, domain authority, outreach campaigns",
    "Content Marketing":      "content strategy, blog posts, content that ranks, thought leadership",
    "Social Media Marketing": "social media growth, engagement, community building, social signals",
    "Digital Marketing":      "digital marketing strategies, online presence, brand awareness, lead generation",
}

TONES = ["Professional", "Casual & Friendly", "Educational", "Promotional", "Inspirational", "Thought-leadership"]
POST_TYPES = [
    "General promotional", "Educational tip / how-to", "Industry news / trend",
    "Case study / result", "Client success story", "FAQ answer", "Seasonal / timely",
]

# ─── FILE PATHS ───────────────────────────────────────────────────────────────
# On Render, use /tmp which persists during the session
_BASE = pathlib.Path("/tmp") if os.environ.get("RENDER") else pathlib.Path(".")
QUEUE_FILE  = _BASE / "queue_data.json"
CONFIG_FILE = _BASE / "config_data.json"

# ─── DISK I/O ─────────────────────────────────────────────────────────────────
def load_queue_from_disk():
    try:
        if QUEUE_FILE.exists():
            with open(QUEUE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return []

def save_queue_to_disk(queue: list):
    try:
        serialisable = []
        for item in queue:
            safe = {k: v for k, v in item.items() if isinstance(v, (str, int, float, bool, list, dict, type(None)))}
            serialisable.append(safe)
        with open(QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump(serialisable, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.warning(f"Could not save queue: {e}")

def save_config_to_disk():
    """Save ALL credentials including Gemini key so background scheduler can use them."""
    config = {
        "gemini_key":      st.session_state.get("gemini_key", ""),
        "fb_page_id":      st.session_state.get("fb_page_id", ""),
        "fb_token":        st.session_state.get("fb_token", ""),
        "tw_api_key":      st.session_state.get("tw_api_key", ""),
        "tw_api_secret":   st.session_state.get("tw_api_secret", ""),
        "tw_access_token": st.session_state.get("tw_access_token", ""),
        "tw_access_secret":st.session_state.get("tw_access_secret", ""),
        "li_access_token": st.session_state.get("li_access_token", ""),
        "ig_user_id":      st.session_state.get("ig_user_id", ""),
        "ig_token":        st.session_state.get("ig_token", ""),
    }
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)
    except Exception:
        pass

def load_config_from_disk():
    """Load config from disk AND override with Render environment variables."""
    config = {}
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r") as f:
                config = json.load(f)
    except Exception:
        pass

    # ✅ Render environment variables always win over saved file
    env_map = {
        "GEMINI_KEY":       "gemini_key",
        "FB_PAGE_ID":       "fb_page_id",
        "FB_PAGE_NAME":     "fb_page_name",
        "FB_TOKEN":         "fb_token",
        "TW_HANDLE":        "tw_handle",
        "TW_API_KEY":       "tw_api_key",
        "TW_API_SECRET":    "tw_api_secret",
        "TW_ACCESS_TOKEN":  "tw_access_token",
        "TW_ACCESS_SECRET": "tw_access_secret",
        "LI_NAME":          "li_name",
        "LI_ACCESS_TOKEN":  "li_access_token",
        "IG_HANDLE":        "ig_handle",
        "IG_USER_ID":       "ig_user_id",
        "IG_TOKEN":         "ig_token",
    }
    for env_key, config_key in env_map.items():
        val = os.environ.get(env_key, "")
        if val:
            config[config_key] = val

    return config

# ─── PUBLISH FUNCTIONS (credential-dict based, safe for background use) ───────
def publish_post_direct(platform, message, image_url=None, link_url=None, config=None):
    """Publish using a config dict — works in background thread (no session_state)."""
    if config is None:
        config = {}

    if platform == "Facebook":
        page_id = config.get("fb_page_id", "")
        token   = config.get("fb_token", "")
        if not page_id or not token:
            return {"error": "Facebook credentials not configured."}
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

    elif platform == "X (Twitter)":
        try:
            import tweepy
        except ImportError:
            return {"error": "tweepy not installed."}
        vals = [config.get(k, "") for k in ["tw_api_key", "tw_api_secret", "tw_access_token", "tw_access_secret"]]
        if not all(vals):
            return {"error": "Twitter/X credentials not configured."}
        try:
            client = tweepy.Client(
                consumer_key=vals[0], consumer_secret=vals[1],
                access_token=vals[2], access_token_secret=vals[3],
            )
            resp = client.create_tweet(text=message[:280])
            return {"id": resp.data["id"]}
        except Exception as e:
            return {"error": str(e)}

    elif platform == "LinkedIn":
        token = config.get("li_access_token", "")
        if not token:
            return {"error": "LinkedIn access token not configured."}
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "LinkedIn-Version": "20250101",
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

    elif platform == "Instagram":
        user_id = config.get("ig_user_id", "")
        token   = config.get("ig_token", "")
        if not user_id or not token:
            return {"error": "Instagram credentials not configured."}
        if not image_url:
            image_url = "https://picsum.photos/1080/1080"
        container = requests.post(
            f"https://graph.facebook.com/v25.0/{user_id}/media",
            data={"image_url": image_url, "caption": message, "access_token": token},
            timeout=30,
        )
        cd = container.json()
        if "error" in cd:
            return {"error": cd["error"]["message"]}
        publish = requests.post(
            f"https://graph.facebook.com/v25.0/{user_id}/media_publish",
            data={"creation_id": cd.get("id"), "access_token": token},
            timeout=30,
        )
        return publish.json()

    return {"error": f"Platform '{platform}' not supported."}


def publish_post(platform, message, image_url=None, link_url=None):
    """Publish using current session_state credentials."""
    config = {
        "fb_page_id":      st.session_state.get("fb_page_id", ""),
        "fb_token":        st.session_state.get("fb_token", ""),
        "tw_api_key":      st.session_state.get("tw_api_key", ""),
        "tw_api_secret":   st.session_state.get("tw_api_secret", ""),
        "tw_access_token": st.session_state.get("tw_access_token", ""),
        "tw_access_secret":st.session_state.get("tw_access_secret", ""),
        "li_access_token": st.session_state.get("li_access_token", ""),
        "ig_user_id":      st.session_state.get("ig_user_id", ""),
        "ig_token":        st.session_state.get("ig_token", ""),
    }
    return publish_post_direct(platform, message, image_url=image_url, link_url=link_url, config=config)


# ─── BACKGROUND SCHEDULER (Render-compatible) ────────────────────────────────
import threading as _threading

_scheduler_started = False
_scheduler_lock    = _threading.Lock()

def _scheduler_loop():
    """Infinite loop — checks queue every 30 seconds."""
    while True:
        try:
            config  = load_config_from_disk()
            queue   = load_queue_from_disk()
            now     = datetime.now()
            changed = False
            for item in queue:
                if item.get("status") != "scheduled":
                    continue
                sched_str = item.get("scheduled_time")
                if not sched_str:
                    continue
                try:
                    sched = datetime.strptime(sched_str, "%Y-%m-%d %H:%M")
                except Exception:
                    continue
                if now < sched:
                    continue
                all_ok, errors = True, {}
                for platform, text in item.get("posts", {}).items():
                    result = publish_post_direct(
                        platform, text,
                        image_url=item.get("image_url"),
                        link_url=item.get("link_url"),
                        config=config,
                    )
                    if "error" in result:
                        all_ok = False
                        errors[platform] = result["error"]
                item["status"]       = "posted" if all_ok else "failed"
                item["published_at"] = now.strftime("%Y-%m-%d %H:%M")
                if errors:
                    item["errors"] = errors
                changed = True
            if changed:
                save_queue_to_disk(queue)
        except Exception:
            pass
        time.sleep(30)


def start_scheduler_once():
    global _scheduler_started
    with _scheduler_lock:
        if not _scheduler_started:
            t = _threading.Thread(target=_scheduler_loop, daemon=True)
            t.start()
            _scheduler_started = True


# ─── SESSION STATE ────────────────────────────────────────────────────────────
# ─── SESSION STATE ────────────────────────────────────────────────────────────
def init_state():
    # Always reload credentials from env vars / config on every run
    saved = load_config_from_disk()

    # These are always overwritten from env vars if available
    credential_keys = {
        "gemini_key":      saved.get("gemini_key", ""),
        "fb_page_id":      saved.get("fb_page_id", ""),
        "fb_token":        saved.get("fb_token", ""),
        "tw_api_key":      saved.get("tw_api_key", ""),
        "tw_api_secret":   saved.get("tw_api_secret", ""),
        "tw_access_token": saved.get("tw_access_token", ""),
        "tw_access_secret":saved.get("tw_access_secret", ""),
        "li_access_token": saved.get("li_access_token", ""),
        "li_name":         saved.get("li_name", os.environ.get("LI_NAME", "")),
        "ig_user_id":      saved.get("ig_user_id", ""),
        "ig_token":        saved.get("ig_token", ""),
        "ig_handle":       saved.get("ig_handle", os.environ.get("IG_HANDLE", "")),
        "fb_page_name":    saved.get("fb_page_name", os.environ.get("FB_PAGE_NAME", "")),
        "tw_handle":       saved.get("tw_handle", os.environ.get("TW_HANDLE", "")),
    }
    # Always update credentials from env (survives Streamlit reruns)
    for k, v in credential_keys.items():
        if v:  # only overwrite if env/config has a value
            st.session_state[k] = v

    # These are only set once (not overwritten on rerun)
    once_defaults = {
        "queue":               load_queue_from_disk(),
        "generated_posts":     {},
        "generated_image":     None,
        "generated_image_url": None,
    }
    for k, v in once_defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # Ensure all keys exist even if empty
    for k in ["gemini_key", "fb_page_name", "fb_page_id", "fb_token",
              "tw_handle", "tw_api_key", "tw_api_secret", "tw_access_token", "tw_access_secret",
              "li_name", "li_access_token", "ig_handle", "ig_user_id", "ig_token"]:
        if k not in st.session_state:
            st.session_state[k] = ""

init_state()
start_scheduler_once()

# ─── GEMINI TEXT ──────────────────────────────────────────────────────────────
def call_gemini(prompt: str, gemini_key: str = None) -> str:
    key = gemini_key or st.session_state.get("gemini_key", "")
    if not key:
        raise ValueError("Gemini API key not set.")

    models = ["gemini-2.5-flash", "gemini-2.5-flash-lite-preview-06-17", "gemini-2.0-flash"]
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": 8192, "temperature": 0.8},
    }
    last_error = "Unknown error"
    for model in models:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
        try:
            r = requests.post(url, json=payload, timeout=30)
            data = r.json()
            if "error" in data:
                last_error = data["error"]["message"]
                if any(w in last_error.lower() for w in ["denied", "billing", "quota", "not found", "not supported"]):
                    continue
                raise ValueError(last_error)
            candidate = data["candidates"][0]
            text = candidate["content"]["parts"][0]["text"].strip()
            if candidate.get("finishReason") == "MAX_TOKENS":
                text += "\n\n[⚠️ Post truncated — please edit to complete it]"
            return text
        except (requests.RequestException, KeyError):
            continue
    raise ValueError(f"All Gemini models failed. Last error: {last_error}")


def build_post_prompt(platform, service, tone, post_type, brief, hashtags, cta, link_url):
    ctx = SERVICES.get(service, service)
    char_note = {
        "X (Twitter)": "CRITICAL: Post MUST be under 270 characters. Be punchy and concise.",
        "Instagram":   "Optimise for Instagram: strong opening line, use emojis, add line breaks.",
        "LinkedIn":    "LinkedIn style: professional insight, hook first, line breaks, can be longer.",
        "Facebook":    "Facebook style: conversational, drives comments and shares.",
    }.get(platform, "")
    return f"""You are a digital marketing copywriter specialising in SEO and local digital marketing.

Write a {platform} post about: {service}
Service context: {ctx}
Post type: {post_type}
Tone: {tone}
Brief: {brief or f"Generate a compelling post about {service}."}

Platform rules: {char_note}
{"Include 3-5 relevant hashtags at the end." if hashtags else ""}
{"End with a clear, compelling call-to-action." if cta else ""}
{f"Naturally reference: {link_url}" if link_url else ""}

Return ONLY the post text. No explanation, no preamble, no quotes."""


def generate_post(platform, service, tone, post_type, brief, hashtags, cta, link_url):
    return call_gemini(build_post_prompt(platform, service, tone, post_type, brief, hashtags, cta, link_url))


def generate_bulk_posts(platforms, service, tone, post_type, hashtags, cta):
    ctx = SERVICES.get(service, service)
    specs = []
    for p in platforms:
        note = {
            "X (Twitter)": "max 270 chars, punchy",
            "Instagram":   "engaging opener, emojis, line breaks",
            "LinkedIn":    "professional, hook, longer-form ok",
            "Facebook":    "conversational, engagement-driven",
        }.get(p, "")
        specs.append(f'{p}: {note}, max {PLATFORMS[p]["max_chars"]} chars')

    prompt = f"""You are a digital marketing copywriter for SEO/local marketing services.

Generate one social media post for EACH of these platforms about: {service}
Context: {ctx}
Post type: {post_type}
Tone: {tone}

Platform requirements:
{chr(10).join(specs)}
{"Include 3-5 hashtags per post." if hashtags else ""}
{"Include a call-to-action in each post." if cta else ""}

You MUST respond with ONLY a valid JSON object, no markdown fences, no explanation.
Example: {{"Facebook": "post text here", "LinkedIn": "post text here"}}
Include only these platforms: {", ".join(platforms)}"""

    raw = call_gemini(prompt)
    clean = re.sub(r"^```[a-zA-Z]*\s*", "", raw.strip())
    clean = re.sub(r"\s*```$", "", clean).strip()
    brace_start, brace_end = clean.find("{"), clean.rfind("}")
    if brace_start != -1 and brace_end != -1:
        clean = clean[brace_start:brace_end + 1]
    try:
        result = json.loads(clean)
        for p in platforms:
            if p not in result or not result[p].strip():
                result[p] = call_gemini(f"Write a single {p} post about {service}. Tone: {tone}. Return ONLY the post text.")
        return result
    except Exception:
        result = {}
        for p in platforms:
            try:
                result[p] = call_gemini(f"Write a single {p} post about {service}. Tone: {tone}. Post type: {post_type}. Return ONLY the post text.")
            except Exception as e:
                result[p] = f"Could not generate post: {e}"
        return result


# ─── IMAGE GENERATION ─────────────────────────────────────────────────────────
def image_prompt(service, brief):
    service_visuals = {
        "SEO": "a glowing search bar with rising graph analytics on a modern dashboard",
        "Local Citations": "a city map with location pins and business icons glowing",
        "AI SEO": "a futuristic AI brain connected to search engine nodes, neural network",
        "GBP Optimization": "a Google Business Profile on a smartphone with 5-star reviews",
        "Link Building": "a network of interconnected website nodes with glowing links",
        "Content Marketing": "a modern content creation workspace with blog posts and social media icons",
        "Social Media Marketing": "colorful social media platform icons floating around a smartphone",
        "Digital Marketing": "a wide digital marketing dashboard with analytics charts and social icons",
    }
    visual_hint = service_visuals.get(service, f"professional digital marketing scene representing {service}")
    extra = f", featuring {brief}" if brief and len(brief) > 10 else ""
    return (
        f"Ultra high quality professional digital marketing photograph: {visual_hint}{extra}. "
        "Photorealistic, 4K, sharp focus, cinematic lighting, deep blue and white color scheme, "
        "NO text, NO words, NO watermarks, clean minimal composition."
    )


def generate_image(service: str, brief: str):
    from PIL import Image
    prompt  = image_prompt(service, brief)
    encoded = quote(prompt)
    seed    = int(time.time())

    # Try new endpoint first, fallback to old
    for url in [
        f"https://gen.pollinations.ai/image/{encoded}?model=flux&width=1200&height=628&nologo=true&seed={seed}",
        f"https://image.pollinations.ai/prompt/{encoded}?model=turbo&width=1200&height=628&nologo=true&seed={seed}",
    ]:
        try:
            r = requests.get(url, timeout=120)
            r.raise_for_status()
            img = Image.open(BytesIO(r.content))
            return img, url
        except Exception:
            continue
    raise RuntimeError("All Pollinations image endpoints failed.")


# ─── HELPERS ──────────────────────────────────────────────────────────────────
def char_color(text, max_chars):
    pct = len(text) / max_chars
    if pct > 0.95: return "🔴"
    if pct > 0.80: return "🟡"
    return "🟢"


def render_post_preview(platform, text, link_url=""):
    import html as html_lib
    info = PLATFORMS[platform]
    color = info["color"]
    name_map = {
        "Facebook":    st.session_state.fb_page_name or "Your Facebook Page",
        "X (Twitter)": st.session_state.tw_handle    or "@YourBusiness",
        "Instagram":   st.session_state.ig_handle    or "@yourbusiness",
        "LinkedIn":    st.session_state.li_name      or "Your LinkedIn Page",
    }
    meta_map = {
        "Facebook":    "Just now · 🌐",
        "X (Twitter)": "Just now",
        "Instagram":   "Just now",
        "LinkedIn":    "Just now · 🌐 Public",
    }
    name     = name_map.get(platform, "Your Page")
    initials = "".join(w[0].upper() for w in name.replace("@", "").split()[:2])
    link_html = f'<a href="{link_url}" style="color:{color};font-size:12px">{link_url}</a>' if link_url else ""
    safe_text = html_lib.escape(text).replace("\n", "<br>")
    st.markdown(f"""
    <div class="post-preview">
        <div class="preview-header">
            <div class="preview-avatar" style="background:{color}">{initials}</div>
            <div>
                <div class="preview-name">{name}</div>
                <div class="preview-meta">{meta_map.get(platform, 'Just now')}</div>
            </div>
        </div>
        <div class="preview-body">{safe_text}<br>{link_html}</div>
        <div class="preview-actions">{info["actions"]}</div>
    </div>
    """, unsafe_allow_html=True)


def save_to_queue(posts_dict, service, post_type, scheduled_time, link_url, image=None, image_url=None):
    image_b64 = None
    if image is not None:
        try:
            buf = BytesIO()
            image.save(buf, format="PNG")
            image_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        except Exception:
            image_b64 = None

    item = {
        "id":             int(time.time() * 1000),
        "posts":          posts_dict,
        "service":        service,
        "post_type":      post_type,
        "scheduled_time": scheduled_time,
        "link_url":       link_url,
        "image_url":      image_url,
        "status":         "scheduled" if scheduled_time else "draft",
        "created_at":     datetime.now().strftime("%Y-%m-%d %H:%M"),
        "image_b64":      image_b64,
    }
    st.session_state.queue.append(item)
    save_queue_to_disk(st.session_state.queue)
    # ✅ FIX: Save credentials every time a scheduled post is added
    save_config_to_disk()
    return item


def status_badge(status):
    cls = {"draft": "badge-draft", "scheduled": "badge-scheduled", "posted": "badge-posted", "failed": "badge-failed"}.get(status, "badge-draft")
    return f'<span class="badge {cls}">{status.capitalize()}</span>'


# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.session_state.gemini_key = st.text_input(
        "🔑 Gemini API Key",
        value=st.session_state.gemini_key,
        type="password",
        placeholder="AIza...",
        key="gemini_key_input",
    )

    st.markdown("## ⚙️ Settings")
    st.markdown("""
    <div class="info-box">
        🤖 <b>Text</b>: Gemini 2.5 Flash (free)<br>
        🖼️ <b>Images</b>: Pollinations.AI (free · no key needed)
    </div>
    """, unsafe_allow_html=True)

    with st.expander("📘 Facebook"):
        st.session_state.fb_page_name = st.text_input("Page Name (preview)", value=st.session_state.fb_page_name, placeholder="My Business Page", key="fb_nm")
        st.session_state.fb_page_id   = st.text_input("Page ID",             value=st.session_state.fb_page_id,   placeholder="123456789",       key="fb_id")
        st.session_state.fb_token     = st.text_input("Page Access Token",   value=st.session_state.fb_token,     type="password",               key="fb_tk")

    with st.expander("𝕏 X (Twitter)"):
        st.session_state.tw_handle        = st.text_input("@Handle (preview)",   value=st.session_state.tw_handle,        placeholder="@YourBusiness", key="tw_h")
        st.session_state.tw_api_key       = st.text_input("API Key",             value=st.session_state.tw_api_key,       type="password",             key="tw_ak")
        st.session_state.tw_api_secret    = st.text_input("API Secret",          value=st.session_state.tw_api_secret,    type="password",             key="tw_as")
        st.session_state.tw_access_token  = st.text_input("Access Token",        value=st.session_state.tw_access_token,  type="password",             key="tw_at")
        st.session_state.tw_access_secret = st.text_input("Access Token Secret", value=st.session_state.tw_access_secret, type="password",             key="tw_ats")

    with st.expander("💼 LinkedIn"):
        st.session_state.li_name         = st.text_input("Page Name (preview)", value=st.session_state.li_name,         placeholder="Your Company", key="li_nm")
        st.session_state.li_access_token = st.text_input("Access Token",        value=st.session_state.li_access_token, type="password",            key="li_tk")

    with st.expander("📸 Instagram"):
        st.session_state.ig_handle  = st.text_input("@Handle (preview)", value=st.session_state.ig_handle,  placeholder="@yourbusiness", key="ig_h")
        st.session_state.ig_user_id = st.text_input("Business User ID",  value=st.session_state.ig_user_id, key="ig_uid")
        st.session_state.ig_token   = st.text_input("Access Token",      value=st.session_state.ig_token,   type="password",             key="ig_tk")

    # ✅ FIX: Always save config on every sidebar interaction
    save_config_to_disk()

    # Show scheduler status
    scheduled_count = sum(1 for i in st.session_state.queue if i.get("status") == "scheduled")
    if scheduled_count > 0:
        st.markdown("---")
        st.markdown(f"🕐 **{scheduled_count} post(s) scheduled**")
        st.markdown("""
        <div class="info-box">
            ✅ Scheduler running inside app<br>
            Checks every 30 seconds automatically.
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")
    st.caption("Built with Gemini · Pollinations.AI · Social Graph APIs")


# ─── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <h1>🚀 AI Social Media Agent</h1>
    <p>Powered by Gemini AI &nbsp;·&nbsp; SEO · Local Citations · AI SEO · GBP Optimization · Digital Marketing</p>
</div>
""", unsafe_allow_html=True)

# ─── TABS ─────────────────────────────────────────────────────────────────────
tab_compose, tab_queue, tab_bulk = st.tabs([
    "✍️ Compose & Schedule",
    f"📋 Queue & Publish  ({len(st.session_state.queue)})",
    "⚡ Bulk Generator",
])


# ══════════════════════════════════════════════════════════════
# TAB 1 — COMPOSE & SCHEDULE
# ══════════════════════════════════════════════════════════════
with tab_compose:
    col_left, col_right = st.columns([1, 1], gap="large")

    with col_left:
        st.markdown("### 1️⃣ Post Setup")
        service   = st.selectbox("Service / Topic", list(SERVICES.keys()))
        post_type = st.selectbox("Post Type", POST_TYPES)
        tone      = st.selectbox("Tone", TONES)
        brief     = st.text_area("Brief / Key Message (optional)", placeholder="e.g. Share 3 quick GBP wins…", height=85)

        st.markdown("**Platforms**")
        plat_cols = st.columns(4)
        selected_platforms = []
        for i, (pname, pinfo) in enumerate(PLATFORMS.items()):
            with plat_cols[i]:
                if st.checkbox(f"{pinfo['icon']} {pname}", value=pname in ["Facebook", "LinkedIn"], key=f"plat_{pname}"):
                    selected_platforms.append(pname)

        st.markdown("**Options**")
        opt1, opt2, opt3 = st.columns(3)
        with opt1: include_hashtags = st.checkbox("# Hashtags", value=True)
        with opt2: include_cta      = st.checkbox("📣 CTA",     value=True)
        with opt3: add_image        = st.checkbox("🖼️ AI Image", value=False)

        include_link = st.checkbox("🔗 Include Link", value=False)
        link_url = ""
        if include_link:
            link_url = st.text_input("Link URL", placeholder="https://yoursite.com/page")

        st.markdown("**Schedule**")
        sched_type = st.radio("Publish type", ["Save as Draft", "Add to Queue", "Schedule for Later"], horizontal=True)
        scheduled_dt = None
        if sched_type == "Schedule for Later":
            sc1, sc2 = st.columns(2)
            with sc1:
                sched_date = st.date_input("Date", value=datetime.now().date() + timedelta(days=1))
            with sc2:
                sched_time = st.time_input("Time", value=datetime.strptime("09:00", "%H:%M").time())
            scheduled_dt = datetime.combine(sched_date, sched_time).strftime("%Y-%m-%d %H:%M")

            # ✅ Show clear confirmation of scheduled time
            st.markdown(f"""
            <div class="info-box">
                📅 Will auto-publish at: <b>{scheduled_dt}</b><br>
                ⚠️ Keep this app running for scheduled posts to publish automatically.
            </div>
            """, unsafe_allow_html=True)

    with col_right:
        st.markdown("### 2️⃣ Generate & Preview")

        if not st.session_state.gemini_key:
            st.markdown('<div class="warn-box">⚠️ Add your Gemini API key in the sidebar. Free at aistudio.google.com</div>', unsafe_allow_html=True)

        gen_btn = st.button("✨ Generate Posts", type="primary", use_container_width=True, disabled=not selected_platforms)

        if gen_btn:
            if not selected_platforms:
                st.error("Select at least one platform.")
            else:
                st.session_state.generated_posts = {}
                st.session_state.generated_image = None
                st.session_state.generated_image_url = None

                with st.spinner(f"Writing posts for {', '.join(selected_platforms)}…"):
                    for p in selected_platforms:
                        try:
                            st.session_state.generated_posts[p] = generate_post(
                                p, service, tone, post_type, brief,
                                include_hashtags, include_cta, link_url,
                            )
                        except Exception as e:
                            st.error(f"❌ {p}: {e}")

                if add_image:
                    with st.spinner("Generating image with Pollinations.AI…"):
                        try:
                            img, img_url = generate_image(service, brief)
                            st.session_state.generated_image = img
                            st.session_state.generated_image_url = img_url
                        except Exception as e:
                            st.warning(f"🖼️ Image failed: {e}")

        if st.session_state.generated_posts:
            edited_posts = {}
            for platform, text in st.session_state.generated_posts.items():
                if platform not in selected_platforms:
                    continue
                pinfo = PLATFORMS[platform]
                indicator = char_color(text, pinfo["max_chars"])
                st.markdown(f"**{pinfo['icon']} {platform}** {indicator} `{len(text)}/{pinfo['max_chars']}`")
                edited = st.text_area(
                    f"Edit {platform}", value=text, height=110,
                    key=f"edit_{platform}", label_visibility="collapsed",
                )
                edited_posts[platform] = edited
                with st.expander(f"👁️ Preview {platform}", expanded=True):
                    render_post_preview(platform, edited, link_url)

            if st.session_state.generated_image:
                st.markdown("---")
                st.markdown("**🖼️ AI Generated Image**")
                st.image(st.session_state.generated_image, use_container_width=True)
                buf = BytesIO()
                st.session_state.generated_image.save(buf, format="PNG")
                st.download_button("⬇️ Download Image", data=buf.getvalue(),
                    file_name=f"{service.lower().replace(' ','_')}_social_image.png", mime="image/png")

            st.markdown("---")
            col_save, col_sched = st.columns(2)
            with col_save:
                if st.button("💾 Save as Draft", use_container_width=True):
                    save_to_queue(edited_posts, service, post_type, None, link_url,
                        image=st.session_state.generated_image,
                        image_url=st.session_state.generated_image_url)
                    st.success("✅ Saved to drafts!")

            with col_sched:
                sched_label = {
                    "Add to Queue":       "📥 Add to Queue",
                    "Schedule for Later": f"📅 Schedule for {scheduled_dt or '...'}",
                }.get(sched_type, "")

                if sched_type != "Save as Draft" and sched_label:
                    if st.button(sched_label, type="primary", use_container_width=True):
                        save_to_queue(
                            edited_posts, service, post_type,
                            scheduled_dt if sched_type == "Schedule for Later" else None,
                            link_url,
                            image=st.session_state.generated_image,
                            image_url=st.session_state.generated_image_url,
                        )
                        st.success("✅ Added to queue!")
                        if sched_type == "Schedule for Later":
                            st.info(f"⏰ Will publish automatically at {scheduled_dt}")
                        st.balloons()


# ══════════════════════════════════════════════════════════════
# TAB 2 — QUEUE & PUBLISH
# ══════════════════════════════════════════════════════════════
with tab_queue:
    st.markdown("### 📋 Post Queue")

    # ✅ Reload queue from disk to pick up background scheduler updates
    fresh_queue = load_queue_from_disk()
    if fresh_queue != st.session_state.queue:
        st.session_state.queue = fresh_queue
        st.rerun()

    if not st.session_state.queue:
        st.info("No posts in queue yet. Generate some in the Compose tab.")
    else:
        f1, f2 = st.columns([3, 1])
        with f1:
            filter_status = st.selectbox("Filter", ["All", "Draft", "Scheduled", "Posted", "Failed"], key="q_filter")
        with f2:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🗑️ Clear All", use_container_width=True):
                st.session_state.queue = []
                save_queue_to_disk([])
                st.rerun()

        shown = [
            item for item in st.session_state.queue
            if filter_status == "All" or item["status"].lower() == filter_status.lower()
        ]

        if not shown:
            st.info(f"No {filter_status.lower()} posts.")

        for idx, item in enumerate(shown):
            badge = status_badge(item["status"])
            sched_html = f'<br><small style="color:#1877f2">📅 Scheduled: {item["scheduled_time"]}</small>' if item.get("scheduled_time") else ""
            pub_html   = f'<br><small style="color:#1a7f37">✅ Published: {item.get("published_at","")}</small>' if item.get("published_at") else ""
            err_html   = f'<br><small style="color:#dc2626">❌ Errors: {item.get("errors","")}</small>' if item.get("errors") else ""

            st.markdown(f"""
            <div class="queue-card">
                <b>#{idx+1} · {item['service']}</b>&nbsp;{badge}&nbsp;
                <small style="color:#888">{item['post_type']} · {item['created_at']}</small>
                {sched_html}{pub_html}{err_html}
            </div>
            """, unsafe_allow_html=True)

            if item.get("image_b64"):
                try:
                    from PIL import Image as PILImage
                    img_bytes = base64.b64decode(item["image_b64"])
                    img_obj = PILImage.open(BytesIO(img_bytes))
                    st.image(img_obj, caption="🖼️ Queued Image", use_container_width=True)
                except Exception:
                    pass

            for platform, text in item["posts"].items():
                pinfo = PLATFORMS.get(platform, {})
                with st.expander(f"{pinfo.get('icon','📄')} {platform}"):
                    current_text = st.text_area(
                        "Post text", value=text, height=90,
                        key=f"q_{item['id']}_{platform}", label_visibility="collapsed",
                    )
                    pcol1, pcol2, pcol3 = st.columns(3)
                    with pcol1:
                        if st.button(f"🚀 Publish to {platform}", key=f"pub_{item['id']}_{platform}"):
                            with st.spinner(f"Publishing to {platform}…"):
                                result = publish_post(platform, current_text,
                                    image_url=item.get("image_url"), link_url=item.get("link_url"))
                            if "error" in result:
                                st.error(f"❌ {result['error']}")
                            else:
                                st.success(f"✅ Published! ID: {result.get('id','')}")
                                item["status"] = "posted"
                                item["published_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                                save_queue_to_disk(st.session_state.queue)
                    with pcol2:
                        if item["status"] != "posted":
                            if st.button("✅ Mark Posted", key=f"mark_{item['id']}_{platform}"):
                                item["status"] = "posted"
                                save_queue_to_disk(st.session_state.queue)
                                st.rerun()
                    with pcol3:
                        if st.button("🗑️ Delete", key=f"del_{item['id']}_{platform}"):
                            st.session_state.queue = [i for i in st.session_state.queue if i["id"] != item["id"]]
                            save_queue_to_disk(st.session_state.queue)
                            st.rerun()


# ══════════════════════════════════════════════════════════════
# TAB 3 — BULK GENERATOR
# ══════════════════════════════════════════════════════════════
with tab_bulk:
    st.markdown("### ⚡ Bulk Content Generator")
    st.caption("Generate a week's worth of content across all your services at once.")

    b1, b2 = st.columns(2)
    with b1:
        bulk_services = st.multiselect("Services", list(SERVICES.keys()), default=["SEO", "GBP Optimization", "AI SEO"])
        bulk_tone     = st.selectbox("Tone", TONES, key="bulk_tone")
        bulk_hashtags = st.checkbox("Include Hashtags", value=True, key="b_ht")
        bulk_cta      = st.checkbox("Include CTA",      value=True, key="b_cta")
        bulk_image    = st.checkbox("🖼️ Generate Image per post", value=False, key="b_img")
    with b2:
        bulk_platforms    = st.multiselect("Platforms", list(PLATFORMS.keys()), default=["Facebook", "LinkedIn"])
        posts_per_service = st.number_input("Posts per service", min_value=1, max_value=5, value=1)

    total_posts = len(bulk_services) * posts_per_service

    if st.button(f"⚡ Generate {total_posts} Post Sets", type="primary", use_container_width=True):
        if not bulk_services:
            st.error("Select at least one service.")
        elif not bulk_platforms:
            st.error("Select at least one platform.")
        elif not st.session_state.gemini_key:
            st.error("Add your Gemini API key in the sidebar.")
        else:
            progress_bar = st.progress(0, text="Starting bulk generation…")
            done, errors = 0, []
            for svc in bulk_services:
                for i in range(posts_per_service):
                    pt = POST_TYPES[i % len(POST_TYPES)]
                    progress_bar.progress(done / total_posts, text=f"✍️ Writing {svc} — {pt}…")
                    try:
                        posts_dict = generate_bulk_posts(bulk_platforms, svc, bulk_tone, pt, bulk_hashtags, bulk_cta)
                        img = None
                        if bulk_image:
                            try:
                                img, _ = generate_image(svc, "")
                            except Exception as img_err:
                                errors.append(f"{svc} image: {img_err}")
                        save_to_queue(posts_dict, svc, pt, None, "", image=img)
                    except Exception as e:
                        errors.append(f"{svc}: {e}")
                    done += 1
                    time.sleep(0.4)
            progress_bar.progress(1.0, text="✅ Done!")
            st.success(f"Generated {done} post set(s) → saved to Queue tab.")
            for err in errors:
                st.warning(f"⚠️ {err}")

    st.markdown("---")
    st.markdown("#### 📅 Weekly Content Calendar Planner")
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    cal_cols = st.columns(7)
    calendar_plan = {}
    for i, day in enumerate(days):
        with cal_cols[i]:
            st.markdown(f"**{day[:3]}**")
            pick = st.selectbox(day, ["—"] + list(SERVICES.keys()), label_visibility="collapsed", key=f"cal_{day}")
            calendar_plan[day] = pick if pick != "—" else None
    planned = [f"{d}: {s}" for d, s in calendar_plan.items() if s]
    if planned:
        st.markdown("**This week's plan:** " + " · ".join(planned))

    st.markdown("---")
    st.markdown("#### 📊 Queue Stats")
    q = st.session_state.queue
    s1, s2, s3, s4, s5 = st.columns(5)
    s1.metric("Total",     len(q))
    s2.metric("Drafts",    sum(1 for i in q if i["status"] == "draft"))
    s3.metric("Scheduled", sum(1 for i in q if i["status"] == "scheduled"))
    s4.metric("Posted",    sum(1 for i in q if i["status"] == "posted"))
    s5.metric("Failed",    sum(1 for i in q if i["status"] == "failed"))
