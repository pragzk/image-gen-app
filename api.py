"""
api.py — Hugging Face Inference API wrapper.

Key loading order:
  1. st.secrets["HF_API_KEY"]  — Streamlit Community Cloud deployment
  2. os.getenv("HF_API_KEY")   — local .env file (loaded via python-dotenv)

generate_image() calls FLUX.1-schnell via InferenceClient and returns
the result as raw PNG bytes ready for st.image() or st.download_button().
"""

import io
import logging
import os

logger = logging.getLogger(__name__)


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
    except (ImportError, FileNotFoundError, KeyError):
        # Streamlit not available or secrets not configured — fall through.
        pass

    # ── 2. .env file / process environment (local dev) ──────────────────────
    try:
        from dotenv import load_dotenv  # noqa: PLC0415

        load_dotenv(override=True)
    except ImportError:
        pass  # python-dotenv is optional; key may already be in the env.

    api_key = os.getenv("HF_API_KEY")
    if not api_key:
        logger.error(
            "HF_API_KEY not found in st.secrets or environment. "
            "Set it in .env (local) or Streamlit Secrets (cloud)."
        )
        raise ValueError("Image generation service is not configured.")

    return api_key


def _get_client():
    """Create the Hugging Face InferenceClient."""
    from huggingface_hub import InferenceClient  # noqa: PLC0415

    return InferenceClient(
        token=_load_api_key(),
        base_url="https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"
    )

def get_current_key() -> str:
    """Returns the loaded API key for debug purposes."""
    try:
        return _load_api_key()
    except ValueError:
        return "NOT_FOUND"


def generate_image(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    negative_prompt: str = ""
) -> bytes:
    """
    Generate an image from a text prompt using FLUX.1-schnell.

    Args:
        prompt: The fully-enriched prompt string (base + style keywords).
        width: Image width in pixels.
        height: Image height in pixels.
        negative_prompt: What not to include in the image.

    Returns:
        Raw PNG image bytes.

    Raises:
        ValueError: If the API key is missing.
        Exception:  Propagates any Hugging Face / network error.
    """
    client = _get_client()  # recreated on every call to avoid stale tokens

    kwargs = {"width": width, "height": height}
    if negative_prompt.strip():
        kwargs["negative_prompt"] = negative_prompt.strip()

    # Returns a PIL.Image.Image
    image = client.text_to_image(prompt, **kwargs)

    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()
