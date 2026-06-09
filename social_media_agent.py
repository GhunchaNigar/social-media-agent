"""
╔══════════════════════════════════════════════════════════╗
║       AI Social Media Agent  —  Digital Marketing        ║
║  Platforms : Facebook · X (Twitter) · Instagram · LinkedIn║
║  Services  : SEO · Citations · AI SEO · GBP · Marketing  ║
║  Text AI   : Google Gemini 2.0 Flash  (free)             ║
║  Image AI  : Gemini Image · FLUX/HuggingFace · Pollinations║
╚══════════════════════════════════════════════════════════╝

Run:
    pip install streamlit requests pillow google-generativeai tweepy
    streamlit run social_media_agent.py
"""

import streamlit as st
import requests
import json
import time
import base64
import re
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

/* Hero banner */
.hero {
    background: linear-gradient(135deg, #1877f2 0%, #0a66c2 100%);
    border-radius: 12px;
    padding: 18px 24px;
    margin-bottom: 20px;
    color: white;
}
.hero h1 { color: white !important; margin: 0 !important; font-size: 1.5rem !important; }
.hero p  { color: rgba(255,255,255,0.85); margin: 4px 0 0; font-size: 13px; }

/* Post preview card */
.post-preview {
    background: #fff;
    border: 1px solid #dddfe2;
    border-radius: 10px;
    overflow: hidden;
    margin: 6px 0 14px;
    font-size: 14px;
    color: #1c1e21;
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
.preview-actions {
    border-top: 1px solid #e4e6eb;
    padding: 4px 14px;
    font-size: 13px;
    color: #65676b;
}

/* Queue item */
.queue-card {
    background: white;
    border: 1px solid #e5e7eb;
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 10px;
}

/* Badge */
.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 600;
}
.badge-draft     { background: #fff8e1; color: #b45309; }
.badge-scheduled { background: #e8f5e9; color: #1a7f37; }
.badge-posted    { background: #e3f2fd; color: #0d5ea6; }

/* Char bar */
.char-bar-wrap { margin-bottom: 4px; }
.char-bar-bg   { height: 3px; background: #f0f0f0; border-radius: 2px; }
.char-bar-fill { height: 3px; border-radius: 2px; transition: width 0.2s; }

/* Info / warning box */
.info-box  { background:#eef4ff; border:1px solid #b8d0ff; border-radius:8px; padding:10px 14px; font-size:13px; color:#2c5fbc; margin-bottom:12px; }
.warn-box  { background:#fffbeb; border:1px solid #fde68a; border-radius:8px; padding:10px 14px; font-size:13px; color:#92400e; margin-bottom:12px; }
.error-box { background:#fff0f0; border:1px solid #fca5a5; border-radius:8px; padding:10px 14px; font-size:13px; color:#dc2626; margin-bottom:12px; }

/* Image provider radio */
.provider-card {
    border: 2px solid #e5e7eb;
    border-radius: 8px;
    padding: 8px 12px;
    cursor: pointer;
    transition: all 0.15s;
    margin-bottom: 6px;
}
.provider-card.active { border-color: #1877f2; background: #e8f4fd; }
</style>
""", unsafe_allow_html=True)


# ─── CONSTANTS ────────────────────────────────────────────────────────────────
PLATFORMS = {
    "Facebook":   {"icon": "📘", "max_chars": 63206, "color": "#1877f2", "actions": "👍 Like · 💬 Comment · ↗ Share"},
    "X (Twitter)":{"icon": "𝕏",  "max_chars": 280,   "color": "#000000", "actions": "💬 Reply · 🔁 Repost · ❤️ Like"},
    "Instagram":  {"icon": "📸", "max_chars": 2200,   "color": "#e1306c", "actions": "❤️ Like · 💬 Comment · ↗ Share · 🔖 Save"},
    "LinkedIn":   {"icon": "💼", "max_chars": 3000,   "color": "#0a66c2", "actions": "👍 Like · 💬 Comment · ↗ Share · ✉️ Send"},
}

SERVICES = {
    "SEO":                   "search engine optimization, keyword rankings, on-page SEO, technical SEO, backlinks",
    "Local Citations":       "local citation building, NAP consistency, directory listings, local SEO presence",
    "AI SEO":                "AI-driven SEO strategies, AI content optimization, machine learning for search, SGE/AI search visibility",
    "GBP Optimization":      "Google Business Profile optimization, local pack rankings, GBP posts, reviews, Q&A",
    "Link Building":         "link building, backlink acquisition, domain authority, outreach campaigns",
    "Content Marketing":     "content strategy, blog posts, content that ranks, thought leadership",
    "Social Media Marketing":"social media growth, engagement, community building, social signals",
    "Digital Marketing":     "digital marketing strategies, online presence, brand awareness, lead generation",
}

TONES = [
    "Professional", "Casual & Friendly", "Educational",
    "Promotional", "Inspirational", "Thought-leadership",
]

POST_TYPES = [
    "General promotional", "Educational tip / how-to", "Industry news / trend",
    "Case study / result", "Client success story", "FAQ answer", "Seasonal / timely",
]




import os, pathlib

QUEUE_FILE = pathlib.Path("queue_data.json")

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

def auto_publish_scheduled():
    now = datetime.now()
    changed = False
    for item in st.session_state.queue:
        if item.get("status") == "scheduled" and item.get("scheduled_time"):
            try:
                sched = datetime.strptime(item["scheduled_time"], "%Y-%m-%d %H:%M")
                if now >= sched:
                    for platform, text in item["posts"].items():
                        result = publish_post(platform, text, image_url=item.get("image_url"), link_url=item.get("link_url"))
                        if "error" not in result:
                            item["status"] = "posted"
                            changed = True
            except Exception:
                pass
    if changed:
        save_queue_to_disk(st.session_state.queue)

# ─── SESSION STATE ────────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "queue": load_queue_from_disk(),
        "generated_posts": {},
        "generated_image": None,
        "generated_image_url": None,
        "gemini_key": "",
        "fb_page_name": "", "fb_page_id": "", "fb_token": "",
        "tw_handle": "", "tw_api_key": "", "tw_api_secret": "",
        "tw_access_token": "", "tw_access_secret": "",
        "li_name": "", "li_access_token": "",
        "ig_handle": "", "ig_user_id": "", "ig_token": "",
        "active_tab": "compose",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()
auto_publish_scheduled()


# ─── GEMINI TEXT ──────────────────────────────────────────────────────────────
def call_gemini(prompt: str) -> str:
    key = st.session_state.gemini_key
    if not key:
        st.error("⚠️ Gemini API key error. Please contact the administrator.")
        st.stop()

    # Try models in order — newer ones need billing; older ones are free for all keys
    # Free-tier models as of 2026 (2.0 deprecated June 2026, 1.5 removed)
    models = ["gemini-2.5-flash", "gemini-2.5-flash-lite-preview-06-17", "gemini-2.5-pro"]
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
            finish_reason = candidate.get("finishReason", "")
            text = candidate["content"]["parts"][0]["text"].strip()
            if finish_reason == "MAX_TOKENS":
                # Post was cut off — append a note so the user knows to edit
                text += "\n\n[⚠️ Post was truncated — please edit to complete it]"
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

You MUST respond with ONLY a valid JSON object, no markdown fences, no explanation, no preamble.
Example format: {{"Facebook": "post text here", "LinkedIn": "post text here"}}
Include only these platforms: {", ".join(platforms)}"""

    raw = call_gemini(prompt)

    # Robustly strip any markdown fences and whitespace
    clean = raw.strip()
    # Remove ```json or ``` fences
    clean = re.sub(r"^```[a-zA-Z]*\s*", "", clean)
    clean = re.sub(r"\s*```$", "", clean)
    clean = clean.strip()

    # Find the JSON object boundaries in case there's extra text
    brace_start = clean.find("{")
    brace_end   = clean.rfind("}")
    if brace_start != -1 and brace_end != -1:
        clean = clean[brace_start:brace_end + 1]

    try:
        result = json.loads(clean)
        # Validate it has the right keys; fill missing ones individually
        for p in platforms:
            if p not in result or not result[p].strip():
                result[p] = call_gemini(
                    f"Write a single {p} post about {service}. Tone: {tone}. "
                    f"Return ONLY the post text, no explanation."
                )
        return result
    except Exception:
        # JSON parse failed entirely — generate each platform individually
        result = {}
        for p in platforms:
            try:
                result[p] = call_gemini(
                    f"Write a single {p} post about {service}. Tone: {tone}. "
                    f"Post type: {post_type}. "
                    f"{'Include 3-5 hashtags.' if hashtags else ''} "
                    f"{'Include a call-to-action.' if cta else ''} "
                    f"Return ONLY the post text, no explanation."
                )
            except Exception as e:
                result[p] = f"Could not generate post: {e}"
        return result

# ─── IMAGE GENERATION ─────────────────────────────────────────────────────────
def image_prompt(service, brief):
    service_visuals = {
        "SEO": "a glowing search bar with rising graph analytics on a modern dashboard, data visualization, upward trending charts",
        "Local Citations": "a city map with location pins and business icons, local business directory, map markers glowing",
        "AI SEO": "a futuristic AI brain connected to search engine nodes, neural network overlaid on web pages, digital intelligence",
        "GBP Optimization": "a Google Business Profile on a smartphone with 5-star reviews and location pin, modern mobile UI",
        "Link Building": "a network of interconnected website nodes with glowing links between them, web graph visualization",
        "Content Marketing": "a modern content creation workspace with blog posts, videos and social media icons floating around a laptop",
        "Social Media Marketing": "colorful social media platform icons floating around a smartphone, engagement metrics, likes and shares",
        "Digital Marketing": "a wide digital marketing dashboard with analytics charts, funnel, email, and social icons, professional workspace",
    }
    visual_hint = service_visuals.get(service, f"professional digital marketing scene representing {service}")
    extra = f", featuring {brief}" if brief and len(brief) > 10 else ""
    return (
        f"Ultra high quality professional digital marketing photograph: {visual_hint}{extra}. "
        "Photorealistic, 4K, sharp focus, cinematic lighting, deep blue and white color scheme, "
        "corporate photography style, NO text, NO words, NO letters, NO watermarks, NO logos, "
        "clean minimal composition, suitable for Facebook and LinkedIn social media post."
    )


def gen_image_pollinations(prompt: str):
    """Returns (PIL.Image, url_str) using the new gen.pollinations.ai endpoint"""
    from PIL import Image
    encoded = quote(prompt)
    seed = int(time.time())

    # New unified endpoint (as of 2026) — flux is free here
    url = (
        f"https://gen.pollinations.ai/image/{encoded}"
        f"?model=flux&width=1200&height=628&nologo=true&seed={seed}"
    )

    try:
        r = requests.get(url, timeout=120)
        r.raise_for_status()
        img = Image.open(BytesIO(r.content))
        return img, url
    except Exception:
        # Fallback: old endpoint with turbo (lightest free model)
        fallback_url = (
            f"https://image.pollinations.ai/prompt/{encoded}"
            f"?model=turbo&width=1200&height=628&nologo=true&seed={seed}"
        )
        r = requests.get(fallback_url, timeout=120)
        r.raise_for_status()
        img = Image.open(BytesIO(r.content))
        return img, fallback_url
def generate_image(service: str, brief: str):
    prompt = image_prompt(service, brief)
    return gen_image_pollinations(prompt)


# ─── SOCIAL PUBLISHING ────────────────────────────────────────────────────────
def post_to_facebook(message, image_url=None, link_url=None):
    page_id = st.session_state.fb_page_id
    token   = st.session_state.fb_token
    if not page_id or not token:
        return {"error": "Facebook credentials not configured."}
    if image_url:
        r = requests.post(
            f"https://graph.facebook.com/{page_id}/photos",
            data={"url": image_url, "caption": message, "access_token": token, "published": True},
        )
    else:
        payload = {"message": message, "access_token": token}
        if link_url:
            payload["link"] = link_url
        r = requests.post(f"https://graph.facebook.com/{page_id}/feed", data=payload)
    return r.json()


def post_to_twitter(message):
    try:
        import tweepy
    except ImportError:
        return {"error": "tweepy not installed. Run: pip install tweepy"}
    keys = ["tw_api_key", "tw_api_secret", "tw_access_token", "tw_access_secret"]
    vals = [st.session_state[k] for k in keys]
    if not all(vals):
        return {"error": "Twitter/X credentials not fully configured."}
    try:
        client = tweepy.Client(
            consumer_key=vals[0], consumer_secret=vals[1],
            access_token=vals[2], access_token_secret=vals[3],
        )
        resp = client.create_tweet(text=message[:280])
        return {"id": resp.data["id"]}
    except Exception as e:
        return {"error": str(e)}


def post_to_linkedin(message):
    token = st.session_state.li_access_token
    if not token:
        return {"error": "LinkedIn access token not configured."}
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "LinkedIn-Version": "202401",
        "X-Restli-Protocol-Version": "2.0.0",
    }
    me = requests.get("https://api.linkedin.com/v2/userinfo", headers=headers)
    if me.status_code != 200:
        return {"error": f"Could not fetch LinkedIn profile: {me.text}"}
    person_id = me.json().get("sub")
    urn = f"urn:li:person:{person_id}"
    body = {
        "author": urn,
        "commentary": message,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": []
        },
        "lifecycleState": "PUBLISHED",
        "isReshareDisabledByAuthor": False
    }
    r = requests.post(
        "https://api.linkedin.com/rest/posts",
        headers=headers,
        json=body
    )
    if r.status_code in [200, 201]:
        return {"id": r.headers.get("x-restli-id", "posted")}
    return {"error": r.text}


def post_to_instagram(message, image_url=None):
    if not st.session_state.ig_user_id or not st.session_state.ig_token:
        return {"error": "Instagram credentials not configured."}
    
    user_id = st.session_state.ig_user_id
    token = st.session_state.ig_token
    
    if not image_url:
    image_url = "https://picsum.photos/1080/1080"
    
    # Step 1 — Create media container
    container = requests.post(
        f"https://graph.facebook.com/v25.0/{user_id}/media",
        data={
            "image_url": image_url,
            "caption": message,
            "access_token": token
        }
    )
    container_data = container.json()
    if "error" in container_data:
        return {"error": container_data["error"]["message"]}
    
    creation_id = container_data.get("id")
    
    # Step 2 — Publish the container
    publish = requests.post(
        f"https://graph.facebook.com/v25.0/{user_id}/media_publish",
        data={
            "creation_id": creation_id,
            "access_token": token
        }
    )
    return publish.json()


def publish_post(platform, message, image_url=None, link_url=None):
    if platform == "Facebook":
        return post_to_facebook(message, image_url=image_url, link_url=link_url)
    elif platform == "X (Twitter)":
        return post_to_twitter(message)
    elif platform == "LinkedIn":
        return post_to_linkedin(message)
    elif platform == "Instagram":
        return post_to_instagram(message)
    return {"error": "Unknown platform."}


# ─── HELPERS ──────────────────────────────────────────────────────────────────
def char_color(text, max_chars):
    pct = len(text) / max_chars
    if pct > 0.95: return "🔴"
    if pct > 0.80: return "🟡"
    return "🟢"


def render_post_preview(platform, text, link_url=""):
    info = PLATFORMS[platform]
    color = info["color"]
    name_map = {
        "Facebook":    st.session_state.fb_page_name  or "Your Facebook Page",
        "X (Twitter)": st.session_state.tw_handle     or "@YourBusiness",
        "Instagram":   st.session_state.ig_handle     or "@yourbusiness",
        "LinkedIn":    st.session_state.li_name       or "Your LinkedIn Page",
    }
    meta_map = {
        "Facebook":    "Just now · 🌐",
        "X (Twitter)": "Just now",
        "Instagram":   "Just now",
        "LinkedIn":    "Just now · 🌐 Public",
    }
    name = name_map.get(platform, "Your Page")
    initials = "".join(w[0].upper() for w in name.replace("@","").split()[:2])
    link_html = f'<a href="{link_url}" style="color:{color};font-size:12px">{link_url}</a>' if link_url else ""
    import html as html_lib
    safe_text = html_lib.escape(text).replace("\n", "<br>")
    st.markdown(f"""
    <div class="post-preview">
        <div class="preview-header">
            <div class="preview-avatar" style="background:{color}">{initials}</div>
            <div>
                <div class="preview-name">{name}</div>
                <div class="preview-meta">{meta_map.get(platform,"Just now")}</div>
            </div>
        </div>
        <div class="preview-body">{safe_text}<br>{link_html}</div>
        <div class="preview-actions">{info["actions"]}</div>
    </div>
    """, unsafe_allow_html=True)


def save_to_queue(posts_dict, service, post_type, scheduled_time, link_url, image=None, image_url=None):
    # Serialize PIL image to base64 so it persists in session state
    image_b64 = None
    if image is not None:
        try:
            buf = BytesIO()
            image.save(buf, format="PNG")
            image_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
        except Exception:
            image_b64 = None

    item = {
        "id": int(time.time() * 1000),
        "posts": posts_dict,
        "service": service,
        "post_type": post_type,
        "scheduled_time": scheduled_time,
        "link_url": link_url,
        "image_url": image_url,   # public URL for Facebook API publishing
        "status": "scheduled" if scheduled_time else "draft",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "image_b64": image_b64,
    }
    st.session_state.queue.append(item)
    save_queue_to_disk(st.session_state.queue)
    return item


def status_badge(status):
    cls = {"draft": "badge-draft", "scheduled": "badge-scheduled", "posted": "badge-posted"}.get(status, "badge-draft")
    return f'<span class="badge {cls}">{status.capitalize()}</span>'


# ─── SIDEBAR ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.session_state.gemini_key = st.text_input(
    "🔑 Gemini API Key",
    value=st.session_state.gemini_key,
    type="password",
    placeholder="AIza...",
    key="gemini_key_input"
)
    st.markdown("## ⚙️ Settings")

    st.markdown("""
    <div class="info-box">
        🤖 <b>Text</b>: Gemini 2.5 Flash (free)<br>
        🖼️ <b>Images</b>: Pollinations.AI (free · no key needed)
    </div>
    """, unsafe_allow_html=True)

    # ── Platform credentials ──
    with st.expander("📘 Facebook"):
        st.session_state.fb_page_name = st.text_input("Page Name (preview)", value=st.session_state.fb_page_name, placeholder="My Business Page", key="fb_nm")
        st.session_state.fb_page_id   = st.text_input("Page ID",             value=st.session_state.fb_page_id,   placeholder="123456789",       key="fb_id")
        st.session_state.fb_token     = st.text_input("Page Access Token",   value=st.session_state.fb_token,     type="password",               key="fb_tk")

    with st.expander("𝕏 X (Twitter)"):
        st.session_state.tw_handle       = st.text_input("@Handle (preview)",    value=st.session_state.tw_handle,       placeholder="@YourBusiness", key="tw_h")
        st.session_state.tw_api_key      = st.text_input("API Key",              value=st.session_state.tw_api_key,      type="password",             key="tw_ak")
        st.session_state.tw_api_secret   = st.text_input("API Secret",           value=st.session_state.tw_api_secret,   type="password",             key="tw_as")
        st.session_state.tw_access_token = st.text_input("Access Token",         value=st.session_state.tw_access_token, type="password",             key="tw_at")
        st.session_state.tw_access_secret= st.text_input("Access Token Secret",  value=st.session_state.tw_access_secret,type="password",             key="tw_ats")

    with st.expander("💼 LinkedIn"):
        st.session_state.li_name         = st.text_input("Page Name (preview)", value=st.session_state.li_name,         placeholder="Your Company",   key="li_nm")
        st.session_state.li_access_token = st.text_input("Access Token",        value=st.session_state.li_access_token, type="password",              key="li_tk")
        st.caption("[Get token →](https://www.linkedin.com/developers)")

    with st.expander("📸 Instagram"):
        st.session_state.ig_handle  = st.text_input("@Handle (preview)", value=st.session_state.ig_handle,  placeholder="@yourbusiness", key="ig_h")
        st.session_state.ig_user_id = st.text_input("Business User ID",  value=st.session_state.ig_user_id, key="ig_uid")
        st.session_state.ig_token   = st.text_input("Access Token",      value=st.session_state.ig_token,   type="password", key="ig_tk")

    st.markdown("---")
    st.caption("Built with Gemini · Pollinations.AI · FLUX · Social Graph APIs")


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

    # ── LEFT: Setup ──────────────────────────────────────────
    with col_left:
        st.markdown("### 1️⃣ Post Setup")

        service   = st.selectbox("Service / Topic", list(SERVICES.keys()))
        post_type = st.selectbox("Post Type", POST_TYPES)
        tone      = st.selectbox("Tone", TONES)
        brief     = st.text_area(
            "Brief / Key Message (optional)",
            placeholder="e.g. Share 3 quick GBP wins local businesses can apply today…",
            height=85,
        )

        st.markdown("**Platforms**")
        plat_cols = st.columns(4)
        selected_platforms = []
        for i, (pname, pinfo) in enumerate(PLATFORMS.items()):
            with plat_cols[i]:
                default = pname in ["Facebook", "LinkedIn"]
                if st.checkbox(f"{pinfo['icon']} {pname}", value=default, key=f"plat_{pname}"):
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

        # Pollinations is the only image provider (free, no key needed)

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

    # ── RIGHT: Generate & Preview ─────────────────────────────
    with col_right:
        st.markdown("### 2️⃣ Generate & Preview")

        if not st.session_state.gemini_key:
            st.markdown('<div class="warn-box">⚠️ Add your Gemini API key in the sidebar to generate posts. Free at aistudio.google.com</div>', unsafe_allow_html=True)

        gen_btn = st.button("✨ Generate Posts", type="primary", use_container_width=True, disabled=not selected_platforms)

        if gen_btn:
            if not selected_platforms:
                st.error("Select at least one platform.")
            else:
                st.session_state.generated_posts = {}
                st.session_state.generated_image = None
                st.session_state.generated_image_url = None

                # ── Generate text posts ──
                with st.spinner(f"Writing posts for {', '.join(selected_platforms)}…"):
                    for p in selected_platforms:
                        try:
                            st.session_state.generated_posts[p] = generate_post(
                                p, service, tone, post_type, brief,
                                include_hashtags, include_cta, link_url,
                            )
                        except Exception as e:
                            st.error(f"❌ {p}: {e}")

                # ── Generate image ──
                if add_image:
                    with st.spinner("Generating image with Pollinations.AI…"):
                        try:
                            img, img_url = generate_image(service, brief)
                            st.session_state.generated_image = img
                            st.session_state.generated_image_url = img_url
                        except Exception as e:
                            st.warning(f"🖼️ Image failed: {e}")

        # ── Show generated posts ──
        if st.session_state.generated_posts:
            edited_posts = {}
            for platform, text in st.session_state.generated_posts.items():
                if platform not in selected_platforms:
                    continue
                pinfo = PLATFORMS[platform]
                indicator = char_color(text, pinfo["max_chars"])
                st.markdown(f"**{pinfo['icon']} {platform}** {indicator} `{len(text)}/{pinfo['max_chars']}`")

                edited = st.text_area(
                    f"Edit {platform}",
                    value=text,
                    height=110,
                    key=f"edit_{platform}",
                    label_visibility="collapsed",
                )
                edited_posts[platform] = edited

                with st.expander(f"👁️ Preview {platform}", expanded=True):
                    render_post_preview(platform, edited, link_url)

            # ── Image preview ──
            if st.session_state.generated_image:
                st.markdown("---")
                st.markdown("**🖼️ AI Generated Image**")
                st.image(st.session_state.generated_image, use_container_width=True, caption="AI-generated social media image")

                # Download button
                buf = BytesIO()
                st.session_state.generated_image.save(buf, format="PNG")
                st.download_button(
                    "⬇️ Download Image",
                    data=buf.getvalue(),
                    file_name=f"{service.lower().replace(' ','_')}_social_image.png",
                    mime="image/png",
                )

            st.markdown("---")

            # ── Save / Schedule ──
            col_save, col_sched = st.columns(2)
            with col_save:
                if st.button("💾 Save as Draft", use_container_width=True):
                    save_to_queue(
                        edited_posts, service, post_type, None, link_url,
                        image=st.session_state.generated_image,
                        image_url=st.session_state.generated_image_url,
                    )
                    st.success("✅ Saved to drafts!")

            with col_sched:
                sched_label = {
                    "Save as Draft":    "💾 Already above",
                    "Add to Queue":     "📥 Add to Queue",
                    "Schedule for Later": f"📅 Schedule for {scheduled_dt or '...'}",
                }.get(sched_type, "Add")

                if sched_type != "Save as Draft":
                    if st.button(sched_label, type="primary", use_container_width=True):
                        status = "scheduled" if sched_type == "Schedule for Later" else "draft"
                        save_to_queue(
                            edited_posts, service, post_type,
                            scheduled_dt if sched_type == "Schedule for Later" else None,
                            link_url,
                            image=st.session_state.generated_image,
                            image_url=st.session_state.generated_image_url,
                        )
                        st.success(f"✅ Added to queue!")
                        st.balloons()


# ══════════════════════════════════════════════════════════════
# TAB 2 — QUEUE & PUBLISH
# ══════════════════════════════════════════════════════════════
with tab_queue:
    st.markdown("### 📋 Post Queue")

    if not st.session_state.queue:
        st.info("No posts in queue yet. Generate some in the Compose tab or use the Bulk Generator.")
    else:
        # Filter + clear
        f1, f2 = st.columns([3, 1])
        with f1:
            filter_status = st.selectbox("Filter", ["All", "Draft", "Scheduled", "Posted"], key="q_filter")
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
            sched_html = f'<br><small style="color:#1877f2">📅 {item["scheduled_time"]}</small>' if item.get("scheduled_time") else ""

            st.markdown(f"""
            <div class="queue-card">
                <b>#{idx+1} · {item['service']}</b>&nbsp;{badge}&nbsp;
                <small style="color:#888">{item['post_type']} · {item['created_at']}</small>
                {sched_html}
            </div>
            """, unsafe_allow_html=True)

            # Show saved image if present
            if item.get("image_b64"):
                try:
                    from PIL import Image as PILImage
                    img_bytes = base64.b64decode(item["image_b64"])
                    img_obj = PILImage.open(BytesIO(img_bytes))
                    st.image(img_obj, caption="🖼️ Queued Image", use_container_width=True)
                except Exception:
                    st.warning("⚠️ Could not display saved image.")

            for platform, text in item["posts"].items():
                pinfo = PLATFORMS.get(platform, {})
                with st.expander(f"{pinfo.get('icon','📄')} {platform}"):
                    current_text = st.text_area(
                        "Post text",
                        value=text,
                        height=90,
                        key=f"q_{item['id']}_{platform}",
                        label_visibility="collapsed",
                    )

                    pcol1, pcol2, pcol3 = st.columns(3)
                    with pcol1:
                        if st.button(f"🚀 Publish to {platform}", key=f"pub_{item['id']}_{platform}"):
                            with st.spinner(f"Publishing to {platform}…"):
                                result = publish_post(platform, current_text, image_url=item.get("image_url"), link_url=item.get("link_url"))
                            if "error" in result:
                                st.error(f"❌ {result['error']}")
                            else:
                                st.success(f"✅ Published! ID: {result.get('id','')}")
                                item["status"] = "posted"
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
        bulk_services  = st.multiselect("Services", list(SERVICES.keys()), default=["SEO", "GBP Optimization", "AI SEO"])
        bulk_tone      = st.selectbox("Tone", TONES, key="bulk_tone")
        bulk_hashtags  = st.checkbox("Include Hashtags", value=True, key="b_ht")
        bulk_cta       = st.checkbox("Include CTA",      value=True, key="b_cta")
        bulk_image     = st.checkbox("🖼️ Generate Image per post (Pollinations, free)", value=False, key="b_img")

    with b2:
        bulk_platforms     = st.multiselect("Platforms", list(PLATFORMS.keys()), default=["Facebook", "LinkedIn"])
        posts_per_service  = st.number_input("Posts per service", min_value=1, max_value=5, value=1)

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
            done = 0
            errors = []

            for svc in bulk_services:
                for i in range(posts_per_service):
                    pt = POST_TYPES[i % len(POST_TYPES)]
                    progress_bar.progress(done / total_posts, text=f"✍️ Writing {svc} — {pt}…")
                    try:
                        posts_dict = generate_bulk_posts(
                            bulk_platforms, svc, bulk_tone, pt, bulk_hashtags, bulk_cta
                        )
                        img = None
                        if bulk_image:
                            progress_bar.progress(done / total_posts, text=f"🖼️ Generating image for {svc}…")
                            try:
                                img, _ = generate_image(svc, "")
                            except Exception as img_err:
                                errors.append(f"{svc} image: {img_err}")
                        save_to_queue(posts_dict, svc, pt, None, "", image=img)
                    except Exception as e:
                        errors.append(f"{svc}: {e}")
                    done += 1
                    time.sleep(0.4)  # gentle rate-limiting

            progress_bar.progress(1.0, text="✅ Done!")
            st.success(f"Generated {done} post set(s) → saved to Queue tab as drafts.")
            if errors:
                for err in errors:
                    st.warning(f"⚠️ {err}")

    # ── Weekly Calendar ──
    st.markdown("---")
    st.markdown("#### 📅 Weekly Content Calendar Planner")
    st.caption("Map a topic to each day, then bulk-generate the actual posts above.")

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    cal_cols = st.columns(7)
    calendar_plan = {}
    for i, day in enumerate(days):
        with cal_cols[i]:
            st.markdown(f"**{day[:3]}**")
            pick = st.selectbox(
                day, ["—"] + list(SERVICES.keys()),
                label_visibility="collapsed",
                key=f"cal_{day}",
            )
            calendar_plan[day] = pick if pick != "—" else None

    planned = [f"{d}: {s}" for d, s in calendar_plan.items() if s]
    if planned:
        st.markdown("**This week's plan:**")
        st.markdown(" · ".join(planned))

    # ── Stats ──
    st.markdown("---")
    st.markdown("#### 📊 Queue Stats")
    q = st.session_state.queue
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Total Posts", len(q))
    s2.metric("Drafts",      sum(1 for i in q if i["status"] == "draft"))
    s3.metric("Scheduled",   sum(1 for i in q if i["status"] == "scheduled"))
    s4.metric("Posted",      sum(1 for i in q if i["status"] == "posted"))
