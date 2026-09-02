"""Gera o icon.ico usado no executável, reaproveitando o mesmo design (círculo
roxo com "SP") já desenhado em tempo real para o ícone da bandeja."""
from PIL import Image, ImageDraw, ImageFont

SIZES = [16, 32, 48, 64, 128, 256]


def make_icon(path="icon.ico"):
    imgs = []
    for s in SIZES:
        img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        pad = max(1, s // 16)
        d.ellipse([pad, pad, s - pad, s - pad], fill="#7c3aed")
        try:
            font = ImageFont.truetype("arialbd.ttf", int(s * 0.38))
        except Exception:
            font = ImageFont.load_default()
        text = "SP"
        bbox = d.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        d.text(((s - tw) / 2 - bbox[0], (s - th) / 2 - bbox[1]), text,
                fill="white", font=font)
        imgs.append(img)
    imgs[0].save(path, format="ICO", sizes=[(s, s) for s in SIZES],
                 append_images=imgs[1:])
    print(f"Ícone gerado em {path}")


if __name__ == "__main__":
    make_icon()
