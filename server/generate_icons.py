from PIL import Image, ImageDraw, ImageFont

def make_icon(size, path):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Purple circle background
    draw.ellipse([0, 0, size - 1, size - 1], fill=(167, 139, 250, 255))
    # White 'AI' text, scaled to icon size
    font_size = max(size // 3, 8)
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()
    text = "AI"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size - tw) // 2, (size - th) // 2 - 1), text, fill='white', font=font)
    img.save(path)

make_icon(16,  '../extension/icons/icon16.png')
make_icon(48,  '../extension/icons/icon48.png')
make_icon(128, '../extension/icons/icon128.png')
print("Icons generated.")
