# 🎨 AI Image Generator

A Streamlit web app that turns text descriptions into images using
**[FLUX.1-schnell](https://huggingface.co/black-forest-labs/FLUX.1-schnell)**
via the Hugging Face Inference API.

---

## What It Does

| Feature | Details |
|---|---|
| **Style conditioning** | Realistic, Anime, Cyberpunk, Watercolor, Pixel Art, Fantasy |
| **Prompt builder** | `prompts.py` appends style-specific quality keywords to your input |
| **Random prompts** | 🎲 button fills the text area with an inspiration prompt |
| **Download** | Download any generated image as a PNG file |
| **Session gallery** | Grid of all images generated in the current session |
| **History sidebar** | Compact list of every prompt you've run |

---

## Project Structure

```
image-gen-app/
├── app.py            # Streamlit UI — layout, widgets, session state
├── api.py            # Hugging Face InferenceClient wrapper
├── prompts.py        # build_prompt(user_prompt, style) → enriched prompt
├── .env              # Local API key — never committed to git
├── .gitignore
├── requirements.txt
└── README.md
```

---

## How to Run Locally

### 1 — Clone the repo

```bash
git clone https://github.com/your-username/image-gen-app.git
cd image-gen-app
```

### 2 — Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate      # macOS / Linux
# .venv\Scripts\activate       # Windows
```

### 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### 4 — Add your API key (see section below)

### 5 — Launch the app

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

---

## How to Add Your API Key

### Local development

1. Go to <https://huggingface.co/settings/tokens> and create a **Read** token.
2. Open (or create) the `.env` file in the project root:

   ```
   HF_API_KEY=hf_your_actual_token_here
   ```

3. `.env` is listed in `.gitignore` — it will **not** be committed.

### Streamlit Community Cloud (production)

1. In your app's dashboard, go to **Settings → Secrets**.
2. Add:

   ```toml
   HF_API_KEY = "hf_your_actual_token_here"
   ```

3. Save and reboot the app.

`api.py` automatically checks `st.secrets` first, then falls back to
the environment variable, so the same code works in both environments.

---

## How to Deploy on Streamlit Community Cloud

1. Push the project to a **public** GitHub repository
   (the `.env` file is excluded by `.gitignore`, so secrets stay safe).

2. Go to <https://share.streamlit.io> and sign in with GitHub.

3. Click **New app**, select your repo and set the main file to `app.py`.

4. Before deploying, open **Advanced settings → Secrets** and paste:

   ```toml
   HF_API_KEY = "hf_your_actual_token_here"
   ```

5. Click **Deploy** — Streamlit installs `requirements.txt` automatically.

Your app will be live at `https://<your-app-name>.streamlit.app`.

---

## Known Limitation

**No persistent image storage between sessions.**  
Generated images are held in `st.session_state`, which lives only for
the duration of a single browser session. Refreshing the page clears the
gallery. To persist images across sessions you would need to add a
database or object-storage backend (e.g. Supabase Storage, AWS S3).

---

## Tech Stack

| Layer | Library |
|---|---|
| UI | [Streamlit](https://streamlit.io) |
| Inference | [huggingface-hub `InferenceClient`](https://huggingface.co/docs/huggingface_hub/package_reference/inference_client) |
| Model | [black-forest-labs/FLUX.1-schnell](https://huggingface.co/black-forest-labs/FLUX.1-schnell) |
| Secrets | [python-dotenv](https://github.com/theskumar/python-dotenv) |
| Images | [Pillow](https://pillow.readthedocs.io) |
