import random
import time
import os

from dotenv import load_dotenv
load_dotenv(override=True)

import streamlit as st

from api import generate_image
from prompts import STYLE_KEYWORDS, build_prompt
from storage import upload_image, fetch_gallery, get_db_stats

st.set_page_config(
    page_title="AI Image Generator",
    layout="wide",
    initial_sidebar_state="expanded",
)

# setup session state
if "history" not in st.session_state:
    try:
        st.session_state.history = fetch_gallery()
        st.session_state.history.reverse()
    except Exception as e:
        print(f"couldnt load history: {e}")
        st.session_state.history = []
        
if "prompt_input" not in st.session_state:
    st.session_state.prompt_input = ""
if "last_gen_time" not in st.session_state:
    st.session_state.last_gen_time = 0.0
if "gen_count" not in st.session_state:
    st.session_state.gen_count = 0
if "theme" not in st.session_state:
    st.session_state.theme = "Dark"

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

def load_css(theme):
    if theme == "Light":
        vars = """
      --bg: #f6f3ee;
      --surface: rgba(255, 255, 255, 0.78);
      --surface-2: #ffffff;
      --panel-border: rgba(0, 0, 0, 0.08);
      --text: #1b1d24;
      --text-muted: #5a6376;
      --text-faint: #64748b;
      --accent: #8b5cf6;
      --accent-2: #4f8cff;
      --accent-soft: rgba(139, 92, 246, 0.12);
      --shadow: 0 10px 40px rgba(0, 0, 0, 0.08);
      --radius-card: 24px;
      --radius-input: 18px;
      --radius-pill: 999px;
      --hero-text: #1b1d24;
      --input-bg: #ffffff;
      --sidebar-bg: rgba(246, 243, 238, 0.88);
      --eyebrow-text: #6d28d9;
      --bg-gradient: linear-gradient(180deg, #f6f3ee 0%, #fdfcfb 100%);
        """
    else:
        vars = """
      --bg: #0b1020;
      --surface: rgba(19, 24, 39, 0.78);
      --surface-2: #151b2f;
      --panel-border: rgba(255, 255, 255, 0.08);
      --text: #f4f7fb;
      --text-muted: #9ea7ba;
      --text-faint: #6f7890;
      --accent: #8b5cf6;
      --accent-2: #4f8cff;
      --accent-soft: rgba(139, 92, 246, 0.16);
      --shadow: 0 20px 60px rgba(0, 0, 0, 0.35);
      --radius-card: 24px;
      --radius-input: 18px;
      --radius-pill: 999px;
      --hero-text: #efe9ff;
      --input-bg: #11172a;
      --sidebar-bg: rgba(11, 16, 32, 0.88);
      --eyebrow-text: #d8c9ff;
      --bg-gradient: linear-gradient(180deg, #0b1020 0%, #0e1426 100%);
        """

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600;700&family=Inter:wght@400;500;600;700&display=swap');

    :root {{
{vars}
    }}

    html, body, [class*="css"]  {{
      font-family: 'Inter', sans-serif;
      color: var(--text);
    }}

    .stApp {{
      background: var(--bg-gradient) !important;
    }}

    .block-container {{
      max-width: 1320px;
      padding-top: 2rem;
      padding-bottom: 2rem;
      padding-left: 2rem;
      padding-right: 2rem;
    }}

    h1, h2, h3 {{
      font-family: 'Cormorant Garamond', serif !important;
      letter-spacing: -0.02em;
      line-height: 0.95;
      color: var(--hero-text) !important;
    }}

    h1 {{
      font-size: clamp(2.8rem, 5vw, 4.8rem) !important;
      font-weight: 600 !important;
      margin-bottom: 0.75rem !important;
      max-width: 12ch;
    }}

    p, label, .stMarkdown, .stCaption {{
      color: var(--text-muted);
      font-size: 0.98rem;
    }}

    section[data-testid="stSidebar"] {{
      background: var(--sidebar-bg) !important;
      border-right: 1px solid var(--panel-border);
      backdrop-filter: blur(18px);
    }}

    section[data-testid="stSidebar"] .block-container {{
      padding-top: 1.5rem;
      padding-left: 1rem;
      padding-right: 1rem;
    }}

    div[data-testid="stTextArea"],
    div[data-testid="stSelectbox"],
    div[data-testid="stNumberInput"],
    div[data-testid="stSlider"],
    div[data-testid="stRadio"],
    div[data-testid="stExpander"] {{
      background: var(--surface);
      border: 1px solid var(--panel-border);
      border-radius: var(--radius-card);
      box-shadow: var(--shadow);
      backdrop-filter: blur(14px);
      padding: 0.35rem 0.5rem;
    }}

    textarea, input, .stTextInput input, [data-baseweb="textarea"], [data-baseweb="input"] {{
      background: var(--input-bg) !important;
      color: var(--text) !important;
      border-radius: var(--radius-input) !important;
      border: 1px solid var(--panel-border) !important;
    }}

    [data-baseweb="select"] > div {{
      background-color: var(--input-bg) !important;
      color: var(--text) !important;
      border-color: var(--panel-border) !important;
    }}

    [data-baseweb="select"] span, [data-baseweb="select"] div {{
      color: var(--text) !important;
    }}

    div[data-baseweb="popover"],
    div[data-baseweb="popover"] > div,
    div[data-baseweb="popover"] > div > div,
    div[data-baseweb="popover"] ul,
    div[data-baseweb="popover"] li,
    [role="listbox"],
    [role="listbox"] * {{
      background-color: var(--input-bg) !important;
      color: var(--text) !important;
    }}

    [role="option"]:hover, 
    [role="option"]:hover *, 
    [role="option"][aria-selected="true"], 
    [role="option"][aria-selected="true"] *, 
    [role="option"][aria-highlighted="true"],
    [role="option"][aria-highlighted="true"] * {{
      background-color: var(--accent-soft) !important;
      color: var(--text) !important;
    }}

    .stRadio div[role="radiogroup"] label > div:first-child {{
      background-color: transparent !important;
    }}

    textarea::placeholder, input::placeholder {{
      color: var(--text-faint) !important;
    }}

    div[data-testid="stButton"] > button {{
      width: 100%;
      border-radius: 999px;
      border: none;
      color: white;
      font-weight: 600;
      padding: 0.9rem 1.25rem;
      background: linear-gradient(135deg, var(--accent) 0%, var(--accent-2) 100%);
      box-shadow: 0 10px 30px rgba(79, 140, 255, 0.28);
      transition: transform 180ms ease, box-shadow 180ms ease, opacity 180ms ease;
    }}

    div[data-testid="stButton"] > button:hover {{
      transform: translateY(-1px);
      box-shadow: 0 16px 40px rgba(79, 140, 255, 0.34);
      opacity: 0.98;
    }}

    div[data-testid="stButton"] > button:focus {{
      outline: none;
      box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.18);
    }}

    .stDownloadButton > button {{
      border-radius: 999px !important;
      background: rgba(255,255,255,0.05) !important;
      color: var(--text) !important;
      border: 1px solid var(--panel-border) !important;
    }}

    img {{
      border-radius: 28px !important;
    }}

    div[data-testid="stImage"] img {{
      border: 1px solid var(--panel-border);
      box-shadow: var(--shadow);
    }}

    div[data-testid="stExpander"] details {{
      border: none !important;
      background: transparent !important;
    }}

    div[data-testid="stExpander"] details summary {{
      background: transparent !important;
      color: var(--text) !important;
    }}

    div[data-testid="stRadio"] label,
    div[data-testid="stCheckbox"] label {{
      color: var(--text);
    }}

    hr {{
      border-color: rgba(255,255,255,0.06);
      margin: 1.5rem 0;
    }}

    div[data-testid="stVerticalBlockBorderWrapper"] {{
      background: var(--surface);
      border: 1px solid var(--panel-border);
      border-radius: var(--radius-card);
      padding: 1.25rem;
      box-shadow: var(--shadow);
      backdrop-filter: blur(14px);
    }}

    .eyebrow {{
      display: inline-block;
      padding: 0.35rem 0.75rem;
      border-radius: 999px;
      background: var(--accent-soft);
      color: var(--eyebrow-text);
      font-size: 0.82rem;
      font-weight: 600;
      letter-spacing: 0.02em;
      margin-bottom: 1rem;
    }}

    .subcopy {{
      max-width: 58ch;
      color: var(--text-muted);
      font-size: 1.02rem;
      margin-bottom: 1.5rem;
    }}
    
    #MainMenu, footer {{ visibility: hidden !important; }}
    header {{ background: transparent !important; }}
    .stDeployButton {{ display: none !important; }}
    </style>
    """, unsafe_allow_html=True)

load_css(st.session_state.theme)

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

    with st.expander("Generation Settings", expanded=True):
        st.markdown("**Image Size**")
        size_choice = st.selectbox(
            label="size_selector",
            options=list(SIZE_OPTIONS.keys()),
            index=0,
            label_visibility="collapsed"
        )
        width, height = SIZE_OPTIONS[size_choice]

        st.markdown("**Batch Size**")
        num_images = st.slider("num_images", min_value=1, max_value=4, value=1, label_visibility="collapsed")

    st.divider()

    gen_c = st.session_state.gen_count
    hist_c = len(st.session_state.history)
    st.caption(f"Session: {hist_c} images  |  Quota: {gen_c}/{MAX_GENS_PER_SESSION} generations")

    st.divider()

    if st.session_state.history:
        st.markdown("**Recent Prompts**")
        for i, item in enumerate(reversed(st.session_state.history[-5:])):
            short = item["prompt"][:40] + "..." if len(item["prompt"]) > 40 else item["prompt"]
            st.caption(f"[{item['style']}] {short}")
        if st.button("Clear history", use_container_width=True):
            st.session_state.history = []
            st.rerun()
    else:
        st.caption("Generate your first image to start.")


left_col, right_col = st.columns([0.95, 1.25], gap="large")

with left_col:
    st.markdown("""
    <div class="eyebrow">AI image studio</div>
    <h1>Create cinematic images from a single prompt</h1>
    <p class="subcopy">
    Describe a scene, choose a visual language, and generate artwork that feels curated rather than random.
    </p>
    """, unsafe_allow_html=True)

    with st.container(border=True):
        text = st.text_area(
            label="prompt",
            placeholder="A foggy lighthouse on a black-rock coastline, dramatic clouds, cinematic light...",
            height=180,
            key="prompt_input",
            label_visibility="collapsed",
        )

        c1, c2 = st.columns([1, 0.32])
        with c1:
            st.caption("Use vivid subjects, lighting, mood, and composition.")
            if text:
                n = len(text)
                if n > MAX_CHARS:
                    st.markdown(f":red[{n}/{MAX_CHARS} chars - too long!]")
        with c2:
            def random_prompt():
                st.session_state.prompt_input = random.choice(RANDOM_PROMPTS)
            st.button("Random", use_container_width=True, on_click=random_prompt)

        with st.expander("Advanced controls"):
            negative_prompt = st.text_input("What to exclude", placeholder="blur, text, watermark, bad anatomy...", label_visibility="collapsed")
            if text.strip():
                st.caption("Preview final prompt:")
                st.code(build_prompt(text.strip(), style), language=None)

    if len(text) > MAX_CHARS:
        st.warning(f"Prompt too long ({len(text)}/{MAX_CHARS} chars). Please shorten it.")
        st.stop()
    if style not in STYLES:
        st.error("Invalid style selected.")
        st.stop()

    generate_clicked = st.button(
        "Generate Image" if num_images == 1 else f"Generate {num_images} Images",
        type="primary",
        use_container_width=True,
        disabled=not text.strip(),
    )


with right_col:
    if generate_clicked and text.strip():
        elapsed = time.time() - st.session_state.last_gen_time
        if elapsed < RATE_LIMIT_SECONDS:
            remaining = int(RATE_LIMIT_SECONDS - elapsed)
            st.warning(f"Please wait {remaining}s before generating again.")
            st.stop()

        if st.session_state.gen_count + num_images > MAX_GENS_PER_SESSION:
            st.error("Session limit reached. Refresh to start a new session.")
            st.stop()

        prompt = build_prompt(text.strip(), style)
        current_batch_images = []
        st.session_state.last_gen_time = time.time()

        for i in range(num_images):
            with st.spinner(f"Creating image {i+1} of {num_images}..."):
                try:
                    img = generate_image(prompt, width, height, negative_prompt)
                    st.session_state.gen_count += 1
                    
                    try:
                        record = upload_image(img, text.strip(), style)
                    except Exception as e:
                        st.error(f"Supabase save failed: {e}")
                        record = {
                            "prompt": text.strip(),
                            "style": style,
                            "image": img,
                        }
                    
                    record["final_prompt"] = prompt
                    record["negative_prompt"] = negative_prompt
                    record["size"] = f"{width}x{height}"
                    
                    st.session_state.history.append(record)
                    current_batch_images.append(record)
                    
                    if len(st.session_state.history) > MAX_HISTORY:
                        st.session_state.history = st.session_state.history[-MAX_HISTORY:]

                except ValueError:
                    st.error("Image generation is currently unavailable. Please try again later.")
                    st.stop()
                except Exception as e:
                    print(f"generation failed: {e}")
                    st.error("Generation failed. Please try again in a moment.")
                    st.stop()

    if st.session_state.history:
        if generate_clicked and text.strip() and num_images > 1:
            display_items = current_batch_images
        else:
            display_items = [st.session_state.history[-1]]
            
        with st.container(border=True):
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
        with st.container(border=True):
            st.markdown("""
            <div style="display:flex; flex-direction:column; align-items:center;
                justify-content:center; min-height:400px; color:var(--text-muted);">
                <span style="margin-top:12px; font-size:16px;">Your image will appear here</span>
                <span style="font-size:14px; opacity:0.8;">Type a prompt and click Generate</span>
            </div>
            """, unsafe_allow_html=True)


if len(st.session_state.history) >= 2:
    st.divider()
    count = len(st.session_state.history)
    st.markdown(f"<h3>Session Gallery ({count} images)</h3>", unsafe_allow_html=True)

    cols = st.columns(3, gap="medium")

    for idx, item in enumerate(reversed(st.session_state.history)):
        col = cols[idx % 3]
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
