import re

# extra words to add based on the style they pick
STYLE_KEYWORDS = {
    "Realistic": "photorealistic, highly detailed, 8k resolution, professional photography, natural lighting, sharp focus, RAW photo, ultra-realistic textures",
    "Anime": "anime style, manga illustration, vibrant colors, cel shading, Studio Ghibli inspired, detailed anime art, beautiful anime scenery, 2D animation, clean linework",
    "Cyberpunk": "cyberpunk aesthetic, neon lights, futuristic cityscape, dark atmosphere, dystopian, Blade Runner inspired, synthwave palette, rain-slicked streets, holographic displays, high contrast",
    "Watercolor": "watercolor painting, soft wet brushstrokes, pastel tones, artistic, flowing pigment, traditional media, dreamy atmosphere, paper texture, delicate washes, impressionistic",
    "Pixel Art": "pixel art, 16-bit style, retro game aesthetic, pixelated, classic video game sprite, limited color palette, dithering, 8-bit charm, crisp pixels",
    "Fantasy": "epic fantasy art, magical atmosphere, highly detailed illustration, mythical world, enchanted environment, high fantasy, cinematic dramatic lighting, painterly, concept art"
}

def clean_text(text):
    # remove weird control characters
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    # fix extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def build_prompt(text, style):
    text = clean_text(text)
    keywords = STYLE_KEYWORDS.get(style, "")
    
    if not text:
        return ""
    if not keywords:
        return text
        
    return f"{text}, {keywords}"
