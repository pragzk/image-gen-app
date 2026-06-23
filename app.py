"""
app.py — Streamlit front-end for the AI Image Generator.

Complete upgrade pass: No emojis, typography upgrade, multiple image generation,
size selection, negative prompt, and responsive grid layout.
"""

import logging
import random
import time
import os

from dotenv import load_dotenv
load_dotenv(override=True)

import streamlit as st

from api import generate_image
from prompts import STYLE_KEYWORDS, build_prompt
from storage import upload_image, fetch_gallery, get_db_stats

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Image Generator",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session-state defaults ────────────────────────────────────────────────────
if "history" not in st.session_state:
    try:
        st.session_state.history = fetch_gallery()
        # Since we fetch descending (newest first) from DB, reverse to match append order
        st.session_state.history.reverse()
    except Exception as e:
        st.error(f"Failed to load database history: {e}")
        st.session_state.history = []
if "prompt_input" not in st.session_state:
    st.session_state.prompt_input = ""
if "last_gen_time" not in st.session_state:
    st.session_state.last_gen_time = 0.0
if "gen_count" not in st.session_state:
    st.session_state.gen_count = 0
if "theme" not in st.session_state:
    st.session_state.theme = "Dark"

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────
RANDOM_PROMPTS = [
    "A lone astronaut standing on an alien planet with twin moons rising",
    "A cozy candlelit coffee shop on a rainy cobblestone street at night",
    "An ancient dragon sleeping on an enormous pile of glittering treasure",
    "A futuristic mega-city floating above the clouds at golden hour",
    "A fox in a three-piece suit reading a broadsheet newspaper in a park",
    "A magical forest where every mushroom glows a different neon color",
    "An old lighthouse standing defiant in the middle of a violent storm",
    "A samurai meditating under a full-bloom cherry blossom tree at dusk",
    "An underwater city of coral towers inhabited by merfolk and sea creatures",
    "A friendly robot carefully tending rows of colorful flowers in a garden",
    "A steam-powered airship docking at a cloud-top harbor at sunrise",
    "A snow leopard perched on a Himalayan cliff overlooking a frozen valley",
]

STYLES = list(STYLE_KEYWORDS.keys())

SIZE_OPTIONS = {
    "Square (512x512)": (512, 512),
    "Portrait (512x768)": (512, 768),
    "Landscape (768x512)": (768, 512),
    "HD (768x768)": (768, 768),
}

MAX_CHARS = 500
RATE_LIMIT_SECONDS = 15
MAX_GENS_PER_SESSION = 50
MAX_HISTORY = 20

# ══════════════════════════════════════════════════════════════════════════════
#  THEMING & CSS
# ══════════════════════════════════════════════════════════════════════════════

if st.session_state.theme == "Dark":
    css_vars = """
    --bg-main: linear-gradient(160deg, #0a0a14 0%, #0f0f1a 40%, #141428 70%, #0f0f1a 100%);
    --bg-sidebar: linear-gradient(180deg, #12122a 0%, #0e0e20 100%);
    --bg-panel: rgba(255, 255, 255, 0.02);
    --border-color: rgba(255, 255, 255, 0.06);
    --border-highlight: rgba(168, 85, 247, 0.4);
    --text-primary: #e4e4ed;
    --text-muted: rgba(228, 228, 237, 0.5);
    --btn-primary-bg: linear-gradient(135deg, #a855f7, #7c3aed);
    --btn-primary-shadow: rgba(168, 85, 247, 0.3);
    --btn-secondary-bg: rgba(255, 255, 255, 0.04);
    --btn-secondary-border: rgba(255, 255, 255, 0.1);
    --btn-secondary-hover-bg: rgba(168, 85, 247, 0.1);
    --hero-gradient: linear-gradient(135deg, #a855f7, #6366f1, #ec4899);
    """
else:
    css_vars = """
    --bg-main: #f8fafc;
    --bg-sidebar: #f1f5f9;
    --bg-panel: #ffffff;
    --border-color: #cbd5e1;
    --border-highlight: #6366f1;
    --text-primary: #0f172a;
    --text-muted: #64748b;
    --btn-primary-bg: linear-gradient(135deg, #4f46e5, #3b82f6);
    --btn-primary-shadow: rgba(79, 70, 229, 0.3);
    --btn-secondary-bg: #ffffff;
    --btn-secondary-border: #cbd5e1;
    --btn-secondary-hover-bg: #e0e7ff;
    --hero-gradient: linear-gradient(135deg, #4f46e5, #ec4899);
    """

st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@600&family=Outfit:wght@300;400&display=swap');

:root {{
    {css_vars}
}}

/* Typography: Avoid span/div to protect Material Icons (like arrow_down) */
html, body, .stApp, p, label, button, input, textarea, summary {{
    font-family: 'Outfit', sans-serif !important;
}}
h1, h2, h3, h4, h5, h6 {{
    font-family: 'Cormorant Garamond', serif !important;
}}

/* Backgrounds */
.stApp {{
    background: var(--bg-main) !important;
    color: var(--text-primary) !important;
}}
section[data-testid="stSidebar"] {{
    background: var(--bg-sidebar) !important;
    border-right: 1px solid var(--border-color) !important;
}}

/* Text Color Enforcement for Light/Dark Mode */
p, h1, h2, h3, h4, h5, h6, label, summary, .stMarkdown p, .stCaption, .stRadio label {{
    color: var(--text-primary) !important;
}}

/* Muted Text */
.muted-text {{
    color: var(--text-muted) !important;
    font-size: 16px !important;
    font-weight: 300 !important;
    letter-spacing: 0.05em !important;
}}

/* Buttons */
button[kind="primary"] {{
    background: var(--btn-primary-bg) !important;
    border: none !important;
    border-radius: 14px !important;
    color: #ffffff !important;
    font-weight: 400 !important;
    box-shadow: 0 4px 20px var(--btn-primary-shadow) !important;
    transition: all 0.3s ease !important;
}}
button[kind="primary"]:hover {{
    box-shadow: 0 6px 30px var(--btn-primary-shadow) !important;
    transform: translateY(-1px);
}}
button[kind="secondary"], .stDownloadButton button {{
    background: var(--btn-secondary-bg) !important;
    border: 1px solid var(--btn-secondary-border) !important;
    border-radius: 12px !important;
    color: var(--text-primary) !important;
    transition: all 0.25s ease !important;
}}
button[kind="secondary"]:hover, .stDownloadButton button:hover {{
    background: var(--btn-secondary-hover-bg) !important;
    border-color: var(--border-highlight) !important;
}}

/* Input areas */
.stTextArea textarea, .stTextInput input, .stSelectbox > div > div {{
    background: var(--bg-panel) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 14px !important;
    color: var(--text-primary) !important;
}}
.stTextArea textarea:focus, .stTextInput input:focus, .stSelectbox > div > div:focus {{
    border-color: var(--border-highlight) !important;
    box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.1) !important;
}}

/* Expanders & Code Blocks */
[data-testid="stExpander"] details summary {{
    background-color: var(--bg-panel) !important;
    color: var(--text-primary) !important;
}}
[data-testid="stExpander"] details {{
    background-color: var(--bg-panel) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 14px !important;
}}
[data-testid="stExpander"] details[open] summary {{
    border-bottom: 1px solid var(--border-color) !important;
}}
[data-testid="stCodeBlock"] pre {{
    background-color: var(--bg-sidebar) !important;
}}
[data-testid="stCodeBlock"] code {{
    color: var(--text-primary) !important;
    text-shadow: none !important;
}}

/* Panels */
div[data-testid="stVerticalBlockBorderWrapper"] {{
    background: var(--bg-panel) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 18px !important;
}}
.stImage img {{ border-radius: 14px; }}
hr {{ border-color: var(--border-color) !important; }}

#MainMenu, footer {{ visibility: hidden; }}
</style>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("<h2 style='margin-bottom:0;'>Image Studio</h2>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:14px; color:var(--text-muted);'>Powered by FLUX.1-schnell</p>", unsafe_allow_html=True)
    st.divider()

    theme_toggle = st.toggle("Enable Light Theme", value=(st.session_state.theme == "Light"))
    new_theme = "Light" if theme_toggle else "Dark"
    if new_theme != st.session_state.theme:
        st.session_state.theme = new_theme
        st.rerun()
    
    st.divider()

    st.markdown("**Visual Style**")
    style = st.radio(
        label="style_radio",
        options=STYLES,
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("**Image Size**")
    size_choice = st.selectbox(
        label="size_selector",
        options=list(SIZE_OPTIONS.keys()),
        index=0,
        label_visibility="collapsed"
    )
    width, height = SIZE_OPTIONS[size_choice]

    st.markdown("**Images to Generate**")
    num_images = st.slider("num_images", min_value=1, max_value=4, value=1, label_visibility="collapsed")

    st.divider()

    gen_c = st.session_state.gen_count
    hist_c = len(st.session_state.history)
    st.caption(f"Session: {hist_c} images  |  Quota: {gen_c}/{MAX_GENS_PER_SESSION} generations")

    st.divider()

    st.markdown("**Storage Status**")
    is_connected, db_count, last_ts = get_db_stats()
    if is_connected:
        st.markdown(f"🟢 **Supabase Connected**")
        st.caption(f"Images in DB: **{db_count}**")
        st.caption(f"Last saved: {last_ts}")
    else:
        st.markdown(f"🔴 **Supabase Offline**")
        st.caption(f"Error: {last_ts}")
    
    st.divider()

    if debug_mode := st.toggle("Developer Mode", value=True):
        current_key = os.getenv("HF_API_KEY", "NOT_FOUND")
        masked_key = current_key[:8] + "..." if current_key != "NOT_FOUND" else "NOT_FOUND"
        st.info(f"Loaded Key: {masked_key}\n\nRouting: router.huggingface.co")

    if st.session_state.history:
        st.markdown("**Recent Prompts**")
        for i, item in enumerate(reversed(st.session_state.history[-5:])): # show only last 5 in sidebar
            short = item["prompt"][:40] + "..." if len(item["prompt"]) > 40 else item["prompt"]
            st.caption(f"[{item['style']}] {short}")
        if st.button("Clear history", use_container_width=True):
            st.session_state.history = []
            st.rerun()
    else:
        st.caption("Generate your first image to start.")


# ══════════════════════════════════════════════════════════════════════════════
#  HERO HEADER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<h1 style="font-size:52px; font-weight:600; letter-spacing:-0.02em;
    background:var(--hero-gradient);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    background-clip:text; margin-bottom:4px;">
    Create stunning images with a single prompt
</h1>
<p class="muted-text" style="margin-bottom:24px;">
    Describe any scene, pick a style, and the model will paint it for you.
</p>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN LAYOUT
# ══════════════════════════════════════════════════════════════════════════════
left_col, right_col = st.columns([4, 6], gap="large")

with left_col:
    with st.container(border=True):
        st.markdown("**Describe your image**")

        user_prompt: str = st.text_area(
            label="prompt",
            placeholder="A serene mountain lake at sunset with perfect reflections...",
            height=130,
            key="prompt_input",
            label_visibility="collapsed",
        )

        c1, c2 = st.columns([3, 1])
        with c1:
            if user_prompt:
                n = len(user_prompt)
                if n > MAX_CHARS:
                    st.markdown(f":red[{n}/{MAX_CHARS} chars - too long!]")
                else:
                    st.caption(f"{n}/{MAX_CHARS} chars | {style}")
            else:
                st.caption("Type a prompt or click Random")

        with c2:
            def _set_random_prompt():
                st.session_state.prompt_input = random.choice(RANDOM_PROMPTS)
            st.button("Random", use_container_width=True, on_click=_set_random_prompt)

        with st.expander("Advanced: Negative Prompt"):
            negative_prompt = st.text_input("What to exclude", placeholder="blur, text, watermark, bad anatomy...", label_visibility="collapsed")

        if user_prompt.strip():
            with st.expander("Preview final prompt"):
                st.code(build_prompt(user_prompt.strip(), style), language=None)

    if len(user_prompt) > MAX_CHARS:
        st.warning(f"Prompt too long ({len(user_prompt)}/{MAX_CHARS} chars). Please shorten it.")
        st.stop()
    if style not in STYLES:
        st.error("Invalid style selected.")
        st.stop()

    generate_clicked = st.button(
        "Generate Image" if num_images == 1 else f"Generate {num_images} Images",
        type="primary",
        use_container_width=True,
        disabled=not user_prompt.strip(),
    )


with right_col:
    if generate_clicked and user_prompt.strip():
        elapsed = time.time() - st.session_state.last_gen_time
        if elapsed < RATE_LIMIT_SECONDS:
            remaining = int(RATE_LIMIT_SECONDS - elapsed)
            st.warning(f"Please wait {remaining}s before generating again.")
            st.stop()

        if st.session_state.gen_count + num_images > MAX_GENS_PER_SESSION:
            st.error("Session limit reached. Refresh to start a new session.")
            st.stop()

        final_prompt = build_prompt(user_prompt.strip(), style)
        
        current_batch_images = []
        st.session_state.last_gen_time = time.time()

        for i in range(num_images):
            with st.spinner(f"Creating image {i+1} of {num_images}..."):
                try:
                    image_bytes = generate_image(final_prompt, width, height, negative_prompt)
                    st.session_state.gen_count += 1
                    
                    try:
                        record = upload_image(image_bytes, user_prompt.strip(), style)
                        st.success(f"Image saved to Supabase! [View URL]({record['image_url']})")
                    except Exception as e:
                        st.error(f"Supabase save failed: {e}")
                        record = {
                            "prompt": user_prompt.strip(),
                            "style": style,
                            "image": image_bytes,
                        }
                    
                    # Fill in UI-specific missing keys
                    record["final_prompt"] = final_prompt
                    record["negative_prompt"] = negative_prompt
                    record["size"] = f"{width}x{height}"
                    
                    st.session_state.history.append(record)
                    current_batch_images.append(record)
                    
                    if len(st.session_state.history) > MAX_HISTORY:
                        st.session_state.history = st.session_state.history[-MAX_HISTORY:]

                except ValueError as e:
                    st.error("Image generation is currently unavailable. Please contact the admin.")
                    if debug_mode: st.error(f"DEBUG: ValueError: {e}")
                    st.stop()
                except Exception as e:
                    logger.exception("Image generation failed")
                    st.error("Generation failed. Please try again in a moment.")
                    if debug_mode: st.error(f"DEBUG ERROR TRACE:\n\n{type(e).__name__}: {str(e)}")
                    st.stop()

    # Display area
    if st.session_state.history:
        # Check if we just generated a batch
        if generate_clicked and user_prompt.strip() and num_images > 1:
            display_items = current_batch_images
        else:
            display_items = [st.session_state.history[-1]]
            
        if len(display_items) == 1:
            latest = display_items[0]
            st.image(latest.get("image", latest.get("image_url")), use_container_width=True)
            m1, m2 = st.columns([3, 1])
            with m1:
                st.markdown(f"**[{latest['style']}]** {latest['prompt'][:80]}{'...' if len(latest['prompt']) > 80 else ''}")
            with m2:
                if "image" in latest:
                    st.download_button(
                        label="Download",
                        data=latest["image"],
                        file_name=f"flux_{latest['style'].lower().replace(' ', '_')}.png",
                        mime="image/png",
                        use_container_width=True,
                    )
                else:
                    st.markdown(f"[Download Image]({latest.get('image_url')})")
            with st.expander("Full generation details"):
                st.text(f"Size: {latest.get('size', '1024x1024')}")
                if latest.get('negative_prompt'):
                    st.text(f"Negative: {latest['negative_prompt']}")
                st.code(latest["final_prompt"], language=None)
        else:
            # Grid for multiple images
            grid_cols = st.columns(2)
            for idx, item in enumerate(display_items):
                col = grid_cols[idx % 2]
                with col:
                    st.image(item.get("image", item.get("image_url")), use_container_width=True)
                    if "image" in item:
                        st.download_button(
                            label="Download",
                            data=item["image"],
                            file_name=f"flux_batch_{idx}_{item['style'].lower().replace(' ', '_')}.png",
                            mime="image/png",
                            key=f"dl_batch_{idx}_{time.time()}",
                            use_container_width=True,
                        )
                    else:
                        st.markdown(f"[Download Image]({item.get('image_url')})")
    else:
        st.markdown("""
        <div style="display:flex; flex-direction:column; align-items:center;
            justify-content:center; min-height:400px; border:2px dashed var(--border-color);
            border-radius:20px; color:var(--text-muted);">
            <span style="margin-top:12px; font-size:16px;">Your image will appear here</span>
            <span style="font-size:14px; opacity:0.8;">Type a prompt and click Generate</span>
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
#  GALLERY
# ══════════════════════════════════════════════════════════════════════════════
if len(st.session_state.history) >= 2:
    st.divider()
    count = len(st.session_state.history)
    st.markdown(f"<h3>Session Gallery ({count} images)</h3>", unsafe_allow_html=True)

    COLS = 3
    cols = st.columns(COLS, gap="medium")

    for idx, item in enumerate(reversed(st.session_state.history)):
        col = cols[idx % COLS]
        short = item["prompt"][:55] + "..." if len(item["prompt"]) > 55 else item["prompt"]

        with col:
            with st.container(border=True):
                st.image(item.get("image", item.get("image_url")), use_container_width=True)
                st.caption(f"**{item['style']}**")
                st.caption(short)
                if "image" in item:
                    st.download_button(
                        label="Download",
                        data=item["image"],
                        file_name=f"flux_{idx:02d}_{item['style'].lower().replace(' ', '_')}.png",
                        mime="image/png",
                        key=f"dl_gallery_{idx}_{time.time()}",
                        use_container_width=True,
                    )
                else:
                    st.markdown(f"[Download Image]({item.get('image_url')})")
