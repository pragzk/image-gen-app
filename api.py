"""
api.py — Hugging Face Inference API wrapper.

Key loading order:
  1. st.secrets["HF_API_KEY"]  — Streamlit Community Cloud deployment
  2. os.getenv("HF_API_KEY")   — local .env file (loaded via python-dotenv)

generate_image() calls FLUX.1-schnell via InferenceClient and returns
the result as raw PNG bytes ready for st.image() or st.download_button().
"""

import io
import os


def _load_api_key() -> str:
    """
    Retrieve the Hugging Face API key from the environment.

    Tries Streamlit secrets first (production), then falls back to a
    .env file loaded by python-dotenv (local development).

    Raises:
        ValueError: If the key cannot be found in either location.
    """
    # ── 1. Streamlit secrets (Streamlit Community Cloud) ────────────────────
    try:
        import streamlit as st  # noqa: PLC0415

        if hasattr(st, "secrets") and "HF_API_KEY" in st.secrets:
            return st.secrets["HF_API_KEY"]
    except Exception:
        # Streamlit not available or secrets not configured — fall through.
        pass

    # ── 2. .env file / process environment (local dev) ──────────────────────
    try:
        from dotenv import load_dotenv  # noqa: PLC0415

        load_dotenv()
    except ImportError:
        pass  # python-dotenv is optional; key may already be in the env.

    api_key = os.getenv("HF_API_KEY")
    if not api_key:
        raise ValueError(
            "HF_API_KEY not found.\n"
            "  • Local dev : add HF_API_KEY=<token> to your .env file.\n"
            "  • Deployment: add HF_API_KEY to your app's Streamlit Secrets."
        )

    return api_key


import streamlit as st  # noqa: PLC0415


@st.cache_resource
def _get_client():
    """Create and cache the Hugging Face InferenceClient (reused across calls)."""
    from huggingface_hub import InferenceClient  # noqa: PLC0415

    return InferenceClient(token=_load_api_key())


def generate_image(prompt: str) -> bytes:
    """
    Generate an image from a text prompt using FLUX.1-schnell.

    Args:
        prompt: The fully-enriched prompt string (base + style keywords).

    Returns:
        Raw PNG image bytes.

    Raises:
        ValueError: If the API key is missing.
        Exception:  Propagates any Hugging Face / network error.
    """
    client = _get_client()  # reused across all calls

    # Returns a PIL.Image.Image
    image = client.text_to_image(
        prompt,
        model="black-forest-labs/FLUX.1-schnell",
    )

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()
