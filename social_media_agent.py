"""
╔══════════════════════════════════════════════════════════╗
║       AI Social Media Agent  —  Digital Marketing        ║
║  Platforms : Facebook · X (Twitter) · Instagram · LinkedIn║
║  Services  : SEO · Citations · AI SEO · GBP · Marketing  ║
║  Text AI   : Google Gemini 2.5 Flash  (free)             ║
║  Image AI  : Pollinations.AI (free · no key needed)       ║
╚══════════════════════════════════════════════════════════╝

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
from io import BytesIO
from datetime import datetime, timedelta
from urllib.parse import quote

# ── Import our fixed scheduler module ────────────────────────────────────────
from scheduler_fix import (
    load_queue_from_disk,
    save_queue_to_disk,
    load_config_from_disk,
    save_config_to_disk,
    process_due_posts,
    start_scheduler,
    QUEUE_FILE,
    CONFIG_FILE,
)

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
    overflow: hidden; margin: 6px 0 14px; font-size: 14px;
    color: #1c1e21; box-shadow: 0 1px 4px rgba(0,0,0,0.07);
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

.queue-card {
    background: white; border: 1px solid #e5e7eb;
    border-radius: 10px; padding: 14px 16px; margin-bottom: 10px;
}
.failed-card {
    background: #fff0f0; border: 1px solid #fca5a5;
    border-radius: 10px; padding: 14px 16px; margin-bottom: 10px;
}

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
    "SEO":                   "search engine optimization, keyword rankings, on-page SEO, technical SEO, backlinks",
    "Local Citations":       "local citation building, NAP consistency, directory listings, local SEO presence",
    "AI SEO":                "AI-driven SEO strategies, AI content optimization, machine learning for search, SGE/AI search visibility",
    "GBP Optimization":      "Google Business Profile optimization, local pack rankings, GBP posts, reviews, Q&A",
    "Link Building":         "link building, backlink acquisition, domain authority, outreach campaigns",
    "Content Marketing":     "content strategy, blog posts, content that ranks, thought leadership",
    "Social Media Marketing":"social media growth, engagement, community building, social signals",
    "Digital Marketing":     "digital marketing strategies, online presence, brand awareness, lead generation",
}

TONES = ["Professional", "Casual & Friendly", "Educational", "Promotional", "Inspirational", "Thought-leadership"]

POST_TYPES = [
    "General promotional", "Educational tip / how-to", "Industry news / trend",
    "Case study / result", "Client success story", "FAQ answer", "Seasonal / timely",
]


# ─── START SCHEDULER (once per process) ──────────────────────────────────────
# This runs in a daemon thread.  Calling start_scheduler() multiple times is
# safe — it checks if the thread is already alive before starting a new one.
if "scheduler_started" not in st.session_state:
    started = start_scheduler(interval_seconds=60)
    st.session_state.scheduler_started = True
    if started:
        print("[app] Background scheduler thread started.")


# ─── SESSION STATE ────────────────────────────────────────────────────────────
def init_state():
    defaults = {
        # Load queue from disk so it survives browser refreshes
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
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ── On every Streamlit interaction, sync queue from disk and check due posts ──
# This is the belt-and-braces fallback for when the background thread missed
# a post (e.g. after a process restart on Render).
def sync_and_check():
    """Re-read queue from disk (catches changes from background thread) and
    publish any overdue posts inline so the user always sees fresh state."""
    disk_queue = load_queue_from_disk()
    # Merge: keep in-session edits for items the background thread hasn't touched,
    # but always trust disk for status changes (posted / failed).
    disk_by_id = {item["id"]: item for item in disk_queue}
    merged = []
    for item in st.session_state.queue:
        if item["id"] in disk_by_id:
            disk_item = disk_by_id[item["id"]]
            # Trust disk status
            item["status"] = disk_item["status"]
            if "publish_errors" in disk_item:
                item["publish_errors"] = disk_item["publish_errors"]
        merged.append(item)
    # Add items that appeared on disk (from other tabs / background job)
    session_ids = {i["id"] for i in merged}
    for item in disk_queue:
        if item["id"] not in session_ids:
            merged.append(item)
    st.session_state.queue = merged

    # Publish any overdue posts that the background thread may have missed
    n = process_due_posts()
    if n:
        # Re-read after publish
        st.session_state.queue = load_queue_from_disk()

sync_and_check()


# ─── GEMINI TEXT ──────────────────────────────────────────────────────────────
def call_gemini(prompt: str) -> str:
    key = st.session_state.gemini_key
    if not key:
        st.error("⚠️ Gemini API key missing. Add it in the sidebar.")
        st.stop()

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

You MUST respond with ONLY a valid JSON object, no markdown fences, no explanation.
Example: {{"Facebook": "post text here", "LinkedIn": "post text here"}}
Include only these platforms: {", ".join(platforms)}"""

    raw = call_gemini(prompt)
    clean = re.sub(r"^```[a-zA-Z]*\s*", "", raw.strip())
    clean = re.sub(r"\s*```$", "", clean).strip()
    brace_start = clean.find("{")
    brace_end   = clean.rfind("}")
    if brace_start != -1 and brace_end != -1:
        clean = clean[brace_start:brace_end + 1]

    try:
        result = json.loads(clean)
        for p in platforms:
            if p not in result or not result[p].strip():
                result[p] = call_gemini(
                    f"Write a single {p} post about {service}. Tone: {tone}. Return ONLY the post text."
                )
        return result
    except Exception:
        result = {}
        for p in platforms:
            try:
                result[p] = call_gemini(
                    f"Write a single {p} post about {service}. Tone: {tone}. "
                    f"Post type: {post_type}. "
                    f"{'Include 3-5 hashtags.' if hashtags else ''} "
                    f"{'Include a call-to-action.' if cta else ''} "
                    f"Return ONLY the post text."
                )
            except Exception as e:
                result[p] = f"Could not generate post: {e}"
        return result


# ─── IMAGE GENERATION ─────────────────────────────────────────────────────────
def image_prompt(service, brief):
    service_visuals = {
        "SEO": "a glowing search bar with rising graph analytics on a modern dashboard",
        "Local Citations": "a city map with location pins and business icons",
        "AI SEO": "a futuristic AI brain connected to search engine nodes, neural network",
        "GBP Optimization": "a Google Business Profile on a smartphone with 5-star reviews",
        "Link Building": "a network of interconnected website nodes with glowing links",
        "Content Marketing": "a modern content creation workspace with blog posts and social media icons",
        "Social Media Marketing": "colorful social media platform icons floating around a smartphone",
        "Digital Marketing": "a wide digital marketing dashboard with analytics charts",
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
    from PIL import Image
    encoded = quote(prompt)
    seed = int(time.time())
    url = (
        f"https://gen.pollinations.ai/image/{encoded}"
        f"?model=flux&width=1200&height=628&nologo=true&seed={seed}"
    )
    try:
        r = requests.get(url, timeout=120)
        r.raise_for_status()
        return Image.open(BytesIO(r.content)), url
    except Exception:
        fallback = (
            f"https://image.pollinations.ai/prompt/{encoded}"
            f"?model=turbo&width=1200&height=628&nologo=true&seed={seed}"
        )
        r = requests.get(fallback, timeout=120)
        r.raise_for_status()
        return Image.open(BytesIO(r.content)), fallback


def generate_image(service: str, brief: str):
    return gen_image_pollinations(image_prompt(service, brief))


# ─── SOCIAL PUBLISHING  (session-state version used in UI buttons) ─────────────
def publish_post(platform, message, image_url=None, link_url=None):
    """Uses session state credentials — call this from UI buttons only."""
    from scheduler_fix import _publish_one
    config = {
        "fb_page_id":       st.session_state.fb_page_id,
        "fb_token":         st.session_state.fb_token,
        "tw_api_key":       st.session_state.tw_api_key,
        "tw_api_secret":    st.session_state.tw_api_secret,
        "tw_access_token":  st.session_state.tw_access_token,
        "tw_access_secret": st.session_state.tw_access_secret,
        "li_access_token":  st.session_state.li_access_token,
        "ig_user_id":       st.session_state.ig_user_id,
        "ig_token":         st.session_state.ig_token,
    }
    return _publish_one(platform, message,
                        image_url=image_url, link_url=link_url, config=config)


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
    name = name_map.get(platform, "Your Page")
    initials = "".join(w[0].upper() for w in name.replace("@", "").split()[:2])
    meta_map = {
        "Facebook":    "Just now · 🌐",
        "X (Twitter)": "Just now",
        "Instagram":   "Just now",
        "LinkedIn":    "Just now · 🌐 Public",
    }
    link_html = f'<a href="{link_url}" style="color:{color};font-size:12px">{link_url}</a>' if link_url else ""
    safe_text = html_lib.escape(text).replace("\n", "<br>")
    st.markdown(f"""
    <div class="post-preview">
        <div class="preview-header">
            <div class="preview-avatar" style="background:{color}">{initials}</div>
            <div>
                <div class="preview-name">{name}</div>
                <div class="preview-meta">{meta_map.get(platform, "Just now")}</div>
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
            pass

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
    return item


def status_badge(status):
    cls = {
        "draft":     "badge-draft",
        "scheduled": "badge-scheduled",
        "posted":    "badge-posted",
        "failed":    "badge-failed",
    }.get(status, "badge-draft")
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

    # Show scheduler health
    from scheduler_fix import _scheduler_thread
    sched_ok = _scheduler_thread is not None and _scheduler_thread.is_alive()
    st.markdown(
        f'<div class="info-box">⏰ Scheduler: {"🟢 Running" if sched_ok else "🔴 Stopped — reload page"}'
        f'<br>🤖 <b>Text</b>: Gemini 2.5 Flash (free)<br>🖼️ <b>Images</b>: Pollinations.AI (free)</div>',
        unsafe_allow_html=True,
    )

    st.markdown("## ⚙️ Settings")

    with st.expander("📘 Facebook"):
        st.session_state.fb_page_name = st.text_input("Page Name (preview)", value=st.session_state.fb_page_name, placeholder="My Business Page", key="fb_nm")
        st.session_state.fb_page_id   = st.text_input("Page ID",             value=st.session_state.fb_page_id,   placeholder="123456789",        key="fb_id")
        st.session_state.fb_token     = st.text_input("Page Access Token",   value=st.session_state.fb_token,     type="password",                key="fb_tk")

    with st.expander("𝕏 X (Twitter)"):
        st.session_state.tw_handle        = st.text_input("@Handle (preview)",   value=st.session_state.tw_handle,        placeholder="@YourBusiness", key="tw_h")
        st.session_state.tw_api_key       = st.text_input("API Key",             value=st.session_state.tw_api_key,       type="password",             key="tw_ak")
        st.session_state.tw_api_secret    = st.text_input("API Secret",          value=st.session_state.tw_api_secret,    type="password",             key="tw_as")
        st.session_state.tw_access_token  = st.text_input("Access Token",        value=st.session_state.tw_access_token,  type="password",             key="tw_at")
        st.session_state.tw_access_secret = st.text_input("Access Token Secret", value=st.session_state.tw_access_secret, type="password",             key="tw_ats")

    with st.expander("💼 LinkedIn"):
        st.session_state.li_name         = st.text_input("Page Name (preview)", value=st.session_state.li_name,         placeholder="Your Company", key="li_nm")
        st.session_state.li_access_token = st.text_input("Access Token",        value=st.session_state.li_access_token, type="password",            key="li_tk")
        st.caption("[Get token →](https://www.linkedin.com/developers)")

    with st.expander("📸 Instagram"):
        st.session_state.ig_handle  = st.text_input("@Handle (preview)", value=st.session_state.ig_handle,  placeholder="@yourbusiness", key="ig_h")
        st.session_state.ig_user_id = st.text_input("Business User ID",  value=st.session_state.ig_user_id, key="ig_uid")
        st.session_state.ig_token   = st.text_input("Access Token",      value=st.session_state.ig_token,   type="password",             key="ig_tk")

    # Persist credentials for background scheduler
    save_config_to_disk(st.session_state)

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
            st.markdown(
                f'<div class="info-box">⏰ Will publish at <b>{scheduled_dt}</b> — '
                f'UptimeRobot keeps the app alive, the background thread will fire within 60 s of that time.</div>',
                unsafe_allow_html=True,
            )

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
                st.download_button(
                    "⬇️ Download Image", data=buf.getvalue(),
                    file_name=f"{service.lower().replace(' ','_')}_social_image.png",
                    mime="image/png",
                )

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
                    "Save as Draft":      "💾 Already above",
                    "Add to Queue":       "📥 Add to Queue",
                    "Schedule for Later": f"📅 Schedule for {scheduled_dt or '...'}",
                }.get(sched_type, "Add")

                if sched_type != "Save as Draft":
                    if st.button(sched_label, type="primary", use_container_width=True):
                        save_to_queue(
                            edited_posts, service, post_type,
                            scheduled_dt if sched_type == "Schedule for Later" else None,
                            link_url,
                            image=st.session_state.generated_image,
                            image_url=st.session_state.generated_image_url,
                        )
                        st.success("✅ Added to queue!")
                        st.balloons()


# ══════════════════════════════════════════════════════════════
# TAB 2 — QUEUE & PUBLISH
# ══════════════════════════════════════════════════════════════
with tab_queue:
    st.markdown("### 📋 Post Queue")

    # Manual "check now" button — useful if user is watching and doesn't want to wait 60 s
    if st.button("🔄 Check & Publish Due Posts Now", use_container_width=False):
        n = process_due_posts()
        if n:
            st.success(f"✅ Published {n} overdue post(s)!")
            st.session_state.queue = load_queue_from_disk()
            st.rerun()
        else:
            st.info("No posts due right now.")

    if not st.session_state.queue:
        st.info("No posts in queue yet.")
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
            badge    = status_badge(item["status"])
            card_cls = "failed-card" if item["status"] == "failed" else "queue-card"
            sched_html = (
                f'<br><small style="color:#1877f2">📅 {item["scheduled_time"]}</small>'
                if item.get("scheduled_time") else ""
            )
            error_html = ""
            if item.get("publish_errors"):
                errs = "; ".join(f"{p}: {e}" for p, e in item["publish_errors"].items())
                error_html = f'<br><small style="color:#dc2626">⚠️ {errs}</small>'

            st.markdown(f"""
            <div class="{card_cls}">
                <b>#{idx+1} · {item['service']}</b>&nbsp;{badge}&nbsp;
                <small style="color:#888">{item['post_type']} · {item['created_at']}</small>
                {sched_html}{error_html}
            </div>
            """, unsafe_allow_html=True)

            if item.get("image_b64"):
                try:
                    from PIL import Image as PILImage
                    img_obj = PILImage.open(BytesIO(base64.b64decode(item["image_b64"])))
                    st.image(img_obj, caption="🖼️ Queued Image", use_container_width=True)
                except Exception:
                    st.warning("⚠️ Could not display saved image.")

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
                                                      image_url=item.get("image_url"),
                                                      link_url=item.get("link_url"))
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
            done = 0
            errors = []

            for svc in bulk_services:
                for i in range(posts_per_service):
                    pt = POST_TYPES[i % len(POST_TYPES)]
                    progress_bar.progress(done / total_posts, text=f"✍️ Writing {svc} — {pt}…")
                    try:
                        posts_dict = generate_bulk_posts(bulk_platforms, svc, bulk_tone, pt, bulk_hashtags, bulk_cta)
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
                    time.sleep(0.4)

            progress_bar.progress(1.0, text="✅ Done!")
            st.success(f"Generated {done} post set(s) → saved to Queue tab as drafts.")
            for err in errors:
                st.warning(f"⚠️ {err}")

    st.markdown("---")
    st.markdown("#### 📅 Weekly Content Calendar Planner")
    st.caption("Map a topic to each day, then bulk-generate the actual posts above.")

    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    cal_cols = st.columns(7)
    calendar_plan = {}
    for i, day in enumerate(days):
        with cal_cols[i]:
            st.markdown(f"**{day[:3]}**")
            pick = st.selectbox(day, ["—"] + list(SERVICES.keys()),
                                label_visibility="collapsed", key=f"cal_{day}")
            calendar_plan[day] = pick if pick != "—" else None

    planned = [f"{d}: {s}" for d, s in calendar_plan.items() if s]
    if planned:
        st.markdown("**This week's plan:**")
        st.markdown(" · ".join(planned))

    st.markdown("---")
    st.markdown("#### 📊 Queue Stats")
    q = st.session_state.queue
    s1, s2, s3, s4, s5 = st.columns(5)
    s1.metric("Total Posts", len(q))
    s2.metric("Drafts",      sum(1 for i in q if i["status"] == "draft"))
    s3.metric("Scheduled",   sum(1 for i in q if i["status"] == "scheduled"))
    s4.metric("Posted",      sum(1 for i in q if i["status"] == "posted"))
    s5.metric("Failed",      sum(1 for i in q if i["status"] == "failed"))
