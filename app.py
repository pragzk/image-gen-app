"""
app.py — Streamlit front-end for the AI Image Generator.

Features
--------
• Text prompt input with live character count
• Six visual styles via sidebar radio buttons
• 🎲 Random prompt generator
• ✨ Generate button → calls FLUX.1-schnell
• Prominent latest-image display with ⬇ download
• Full-session gallery grid with per-image download
• Prompt history panel in the sidebar
"""

import random

import streamlit as st

from api import generate_image
from prompts import STYLE_KEYWORDS, build_prompt

# ── Page configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Image Generator",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session-state defaults ────────────────────────────────────────────────────
if "history" not in st.session_state:
    # Each entry: {"prompt", "style", "final_prompt", "image": bytes}
    st.session_state.history = []

if "prompt_input" not in st.session_state:
    st.session_state.prompt_input = ""

# ── Random prompt bank ────────────────────────────────────────────────────────
RANDOM_PROMPTS: list[str] = [
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

STYLES: list[str] = list(STYLE_KEYWORDS.keys())

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🎨 AI Image Gen")
    st.markdown("Powered by **FLUX.1-schnell** via Hugging Face")
    st.divider()

    # Style selector
    st.subheader("🎭 Visual Style")
    style = st.radio(
        label="style_radio",
        options=STYLES,
        index=0,
        label_visibility="collapsed",
    )

    st.divider()

    # Prompt history
    if st.session_state.history:
        st.subheader(f"📜 History ({len(st.session_state.history)})")
        for i, item in enumerate(reversed(st.session_state.history)):
            short = (
                item["prompt"][:45] + "…"
                if len(item["prompt"]) > 45
                else item["prompt"]
            )
            st.caption(f"**{item['style']}** · {short}")
        if st.button("🗑️ Clear history", use_container_width=True):
            st.session_state.history = []
            st.rerun()
    else:
        st.caption("No images generated yet.")

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
st.title("🎨 AI Image Generator")
st.markdown(
    "Describe any scene, pick a style, and **FLUX.1-schnell** will paint it "
    "for you in seconds. Use the 🎲 button if you need inspiration."
)
st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# PROMPT INPUT ROW
# ─────────────────────────────────────────────────────────────────────────────
input_col, rand_col = st.columns([5, 1], gap="small")

with input_col:
    user_prompt: str = st.text_area(
        label="📝 Your prompt",
        placeholder="A serene mountain lake at sunset with perfect reflections…",
        height=110,
        key="prompt_input",
        help="Describe the image you want. The selected style will be appended automatically.",
    )

with rand_col:
    # Push button down to align with text area
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    if st.button("🎲 Random", use_container_width=True, help="Fill with a random prompt"):
        st.session_state.prompt_input = random.choice(RANDOM_PROMPTS)
        st.rerun()

# Character / word count hint
if user_prompt:
    st.caption(f"{len(user_prompt)} characters · style: **{style}**")

# ─────────────────────────────────────────────────────────────────────────────
# PROMPT VALIDATION
# ─────────────────────────────────────────────────────────────────────────────
MAX_CHARS = 500
if len(user_prompt) > MAX_CHARS:
    st.warning(f"Prompt too long ({len(user_prompt)}/{MAX_CHARS} chars). Please shorten it.")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# GENERATE BUTTON
# ─────────────────────────────────────────────────────────────────────────────
gen_col, preview_col = st.columns([2, 5])

with gen_col:
    generate_clicked = st.button(
        "✨ Generate Image",
        type="primary",
        use_container_width=True,
        disabled=not user_prompt.strip(),
    )

with preview_col:
    if user_prompt.strip():
        preview = build_prompt(user_prompt.strip(), style)
        with st.expander("👁 Preview final prompt"):
            st.code(preview, language=None)

# ─────────────────────────────────────────────────────────────────────────────
# GENERATION LOGIC
# ─────────────────────────────────────────────────────────────────────────────
if generate_clicked and user_prompt.strip():
    final_prompt = build_prompt(user_prompt.strip(), style)

    with st.spinner("🖼️ Generating your image — usually takes 10–30 s…"):
        try:
            image_bytes = generate_image(final_prompt)

            st.session_state.history.append(
                {
                    "prompt": user_prompt.strip(),
                    "style": style,
                    "final_prompt": final_prompt,
                    "image": image_bytes,
                }
            )

            # Cap history to prevent unbounded memory growth
            MAX_HISTORY = 20
            if len(st.session_state.history) > MAX_HISTORY:
                st.session_state.history = st.session_state.history[-MAX_HISTORY:]

        except ValueError as exc:
            st.error(f"🔑 API key error: {exc}")
            st.info(
                "Add your Hugging Face token to `.env` (local) or "
                "Streamlit Secrets (cloud). See the README for details."
            )
            st.stop()

        except Exception as exc:
            st.error(f"Generation failed: {exc}")
            st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# LATEST IMAGE — PROMINENT DISPLAY
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.history:
    latest = st.session_state.history[-1]

    st.divider()
    st.subheader("🖼️ Latest Generation")

    img_col, meta_col = st.columns([3, 2], gap="large")

    with img_col:
        st.image(latest["image"], use_container_width=True)

    with meta_col:
        st.markdown(f"**Style**&ensp;`{latest['style']}`")
        st.markdown("**Your prompt**")
        st.info(latest["prompt"])

        with st.expander("Full prompt sent to model"):
            st.code(latest["final_prompt"], language=None)

        st.download_button(
            label="⬇️ Download PNG",
            data=latest["image"],
            file_name=f"flux_{latest['style'].lower().replace(' ', '_')}.png",
            mime="image/png",
            use_container_width=True,
            type="secondary",
        )

# ─────────────────────────────────────────────────────────────────────────────
# SESSION GALLERY — shown when 2 or more images have been generated
# ─────────────────────────────────────────────────────────────────────────────
if len(st.session_state.history) >= 2:
    st.divider()
    count = len(st.session_state.history)
    st.subheader(f"🗂️ Session Gallery  ·  {count} image{'s' if count != 1 else ''}")

    COLS = 3
    cols = st.columns(COLS, gap="small")

    # Show newest first
    for idx, item in enumerate(reversed(st.session_state.history)):
        col = cols[idx % COLS]
        caption_text = (
            item["prompt"][:50] + "…"
            if len(item["prompt"]) > 50
            else item["prompt"]
        )
        with col:
            st.image(
                item["image"],
                caption=f"[{item['style']}] {caption_text}",
                use_container_width=True,
            )
            st.download_button(
                label="⬇️",
                data=item["image"],
                file_name=f"flux_{idx:02d}_{item['style'].lower().replace(' ', '_')}.png",
                mime="image/png",
                key=f"dl_gallery_{idx}",
                use_container_width=True,
            )
