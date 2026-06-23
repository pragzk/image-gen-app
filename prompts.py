"""
prompts.py — Style-conditioned prompt builder.

Each style appends a curated set of quality keywords that steer FLUX
toward the desired aesthetic without overriding the user's intent.
"""

STYLE_KEYWORDS: dict[str, str] = {
    "Realistic": (
        "photorealistic, highly detailed, 8k resolution, "
        "professional photography, natural lighting, sharp focus, "
        "RAW photo, ultra-realistic textures"
    ),
    "Anime": (
        "anime style, manga illustration, vibrant colors, cel shading, "
        "Studio Ghibli inspired, detailed anime art, beautiful anime scenery, "
        "2D animation, clean linework"
    ),
    "Cyberpunk": (
        "cyberpunk aesthetic, neon lights, futuristic cityscape, "
        "dark atmosphere, dystopian, Blade Runner inspired, synthwave palette, "
        "rain-slicked streets, holographic displays, high contrast"
    ),
    "Watercolor": (
        "watercolor painting, soft wet brushstrokes, pastel tones, "
        "artistic, flowing pigment, traditional media, dreamy atmosphere, "
        "paper texture, delicate washes, impressionistic"
    ),
    "Pixel Art": (
        "pixel art, 16-bit style, retro game aesthetic, pixelated, "
        "classic video game sprite, limited color palette, dithering, "
        "8-bit charm, crisp pixels"
    ),
    "Fantasy": (
        "epic fantasy art, magical atmosphere, highly detailed illustration, "
        "mythical world, enchanted environment, high fantasy, "
        "cinematic dramatic lighting, painterly, concept art"
    ),
}


def build_prompt(user_prompt: str, style: str) -> str:
    """
    Append style-specific quality keywords to the user's base prompt.

    Args:
        user_prompt: The raw description entered by the user.
        style:       One of the keys in STYLE_KEYWORDS.

    Returns:
        A single enriched prompt string ready to send to the model.
    """
    user_prompt = user_prompt.strip()
    keywords = STYLE_KEYWORDS.get(style, "")

    if not keywords:
        return user_prompt

    return f"{user_prompt}, {keywords}"
