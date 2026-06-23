import io
import os
import streamlit as st
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

def get_key():
    # try to get the key from streamlit secrets first
    try:
        if hasattr(st, "secrets") and "HF_API_KEY" in st.secrets:
            return st.secrets["HF_API_KEY"]
    except Exception:
        pass

    # fallback to local .env file
    try:
        load_dotenv(override=True)
    except Exception:
        pass
        
    key = os.getenv("HF_API_KEY")
    if not key:
        print("error: hf api key is missing")
        raise ValueError("no api key found")
        
    return key

def get_client():
    return InferenceClient(
        token=get_key(),
        base_url="https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"
    )

def get_current_key():
    try:
        return get_key()
    except Exception:
        return "NOT_FOUND"

def generate_image(prompt, width=1024, height=1024, negative_prompt=""):
    client = get_client()
    
    args = {"width": width, "height": height}
    if negative_prompt.strip():
        args["negative_prompt"] = negative_prompt.strip()

    img = client.text_to_image(prompt, **args)

    # convert the image to bytes so we can display it
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
