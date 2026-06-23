# 🎨 AI Image Generator

A Streamlit web app that turns text descriptions into images using **[FLUX.1-schnell](https://huggingface.co/black-forest-labs/FLUX.1-schnell)** via the Hugging Face Inference API, and persistently saves them to a Supabase PostgreSQL database and Storage bucket.

---

## What the project does

- **Generates Images**: Uses the FLUX.1-schnell model to create stunning images from text prompts.
- **Style Conditioning**: Automatically enhances prompts with curated keywords for styles like Realistic, Anime, Cyberpunk, Watercolor, Pixel Art, and Fantasy.
- **Batch Generation**: Generate up to 4 images at a time.
- **Persistent Gallery**: Uploads generated images to Supabase Storage and saves metadata in a PostgreSQL database, so your gallery persists across sessions.
- **Dark/Light Themes**: A beautifully polished, cinematic custom UI with a toggleable theme.

---

## How to run it locally

### 1 — Clone the repo
```bash
git clone https://github.com/pragzk/image-gen-app.git
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

### 4 — Launch the app
```bash
streamlit run app.py
```

---

## How to add your API key

You will need three keys for this project to work fully:
1. **Hugging Face Token**: Go to <https://huggingface.co/settings/tokens> and create a **Read** token.
2. **Supabase URL & Key**: Create a Supabase project, go to Project Settings -> API, and get the Project URL and the `anon` `public` API key.

Create a `.env` file in the project root and add your keys:
```
HF_API_KEY=hf_your_actual_token_here
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your_supabase_anon_key
```
*(The `.env` file is in `.gitignore` and won't be committed to version control.)*

---

## How to deploy it

1. Push the project to your GitHub repository.
2. Go to <https://share.streamlit.io> and sign in with GitHub.
3. Click **New app**, select your repo and set the main file to `app.py`.
4. Open **Advanced settings → Secrets** and paste your keys in TOML format:
   ```toml
   HF_API_KEY = "hf_your_actual_token_here"
   SUPABASE_URL = "https://your-project-id.supabase.co"
   SUPABASE_KEY = "your_supabase_anon_key"
   ```
5. Click **Deploy**. Streamlit Cloud will automatically install the requirements and launch your app.

---

## One known limitation

**Sequential Batch Generation and Rate Limits**: When generating multiple images at once (Batch Size > 1), the app makes sequential API calls to Hugging Face rather than asynchronous parallel requests. Because it relies on the free Hugging Face Inference API, generating too many images back-to-back can cause the generation process to take a long time, and you might occasionally hit rate-limit errors or experience temporary unavailability during high network traffic.
