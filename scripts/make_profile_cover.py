"""Export the profile picture and the cover image used in the home-page hero.

Sources live in originals/ (git-ignored). If originals/profile.* or
originals/cover.* exist they are used for that role (centre-cropped);
otherwise the crop boxes below are applied to originals/portrait-source.jpg.

Writes (all metadata stripped):
  assets/img/profile-800.webp, profile-400.webp   square, centred on the face
  assets/img/apple-touch-icon.png                 180 px
  assets/img/cover-2400.webp, cover-1200.webp     wide hero image
  assets/img/og-cover.jpg                         1200x630 Open Graph preview

Usage:  python scripts/make_profile_cover.py
"""
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont

from imgutil import ROOT, RAW_EXTS, check_published_images, fit, load_oriented, save

ORIGINALS = ROOT / "originals"
OUT = ROOT / "assets" / "img"

# Crop boxes as fractions (left, top, right, bottom) of the EXIF-oriented source.
PROFILE = {"source": "portrait-source.jpg", "box": (752 / 2822, 884 / 3762, 2068 / 2822, 2200 / 3762)}
COVER = {"source": "portrait-source.jpg", "box": (0.0, 0.0, 0.90, 0.30)}  # window grid above the portrait


def role_file(role):
    for p in ORIGINALS.glob(f"{role}.*"):
        if p.suffix.lower() in RAW_EXTS:
            return p
    return None


def crop(im, box):
    W, H = im.size
    l, t, r, b = box
    return im.crop((round(l * W), round(t * H), round(r * W), round(b * H)))


def centre_square(im):
    s = min(im.size)
    l, t = (im.width - s) // 2, (im.height - s) // 2
    return im.crop((l, t, l + s, t + s))


def centre_aspect(im, aspect):
    if im.width / im.height > aspect:
        w = round(im.height * aspect)
        l = (im.width - w) // 2
        return im.crop((l, 0, l + w, im.height))
    h = round(im.width / aspect)
    t = (im.height - h) // 2
    return im.crop((0, t, im.width, t + h))


def social_card(cover, profile):
    """1200x630 Open Graph image: the cover with the hero's scrim, name, tagline and avatar."""
    W, H = 1200, 630
    card = centre_aspect(cover, W / H).resize((W, H), Image.LANCZOS).convert("RGB")
    card = Image.blend(card, ImageChops.multiply(card, Image.new("RGB", (W, H), (47, 75, 114))), 0.28)
    shade = Image.new("L", (W, H))
    px = shade.load()
    for x in range(W):
        a = 0.86 - 0.62 * (x / W)            # dark on the left where the text sits
        for y in range(H):
            px[x, y] = int(255 * min(0.92, a + 0.25 * (y / H)))
    card = Image.composite(Image.new("RGB", (W, H), (9, 17, 29)), card, shade)

    fonts = ROOT / "assets" / "fonts"
    serif = ImageFont.truetype(str(fonts / "newsreader-latin-wght-normal.woff2"), 92)
    sans = ImageFont.truetype(str(fonts / "instrument-sans-latin-wght-normal.woff2"), 26)
    small = ImageFont.truetype(str(fonts / "instrument-sans-latin-wght-normal.woff2"), 22)
    sans.set_variation_by_axes([600])
    small.set_variation_by_axes([600])
    d = ImageDraw.Draw(card)
    d.ellipse((72, 212, 84, 224), fill=(242, 154, 98))
    d.text((98, 205), "SENIOR PROJECT ASSOCIATE · IIT JODHPUR & NBRC", font=small, fill=(232, 236, 241))
    d.text((68, 238), "Swatantra Dhara", font=serif, fill=(255, 255, 255))
    d.text((72, 365), "Computational neuroscience · fMRI · brain dynamics & ageing", font=sans, fill=(238, 232, 222))
    d.text((72, 545), "swatantra-d.github.io", font=small, fill=(242, 154, 98))

    size = 210
    av = profile.resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size * 4, size * 4))
    ImageDraw.Draw(mask).ellipse((0, 0, size * 4 - 1, size * 4 - 1), fill=255)
    mask = mask.resize((size, size), Image.LANCZOS)
    x0, y0 = W - size - 90, (H - size) // 2
    ImageDraw.Draw(card).ellipse((x0 - 8, y0 - 8, x0 + size + 7, y0 + size + 7), outline=(242, 154, 98), width=4)
    card.paste(av, (x0, y0), mask)
    return card


def main():
    p = role_file("profile")
    profile = centre_square(load_oriented(p)) if p else crop(load_oriented(ORIGINALS / PROFILE["source"]), PROFILE["box"])
    for size in (800, 400):
        save(profile.resize((size, size)), OUT / f"profile-{size}.webp", quality=82)
    save(profile.resize((180, 180)), OUT / "apple-touch-icon.png")

    c = role_file("cover")
    cover = load_oriented(c) if c else crop(load_oriented(ORIGINALS / COVER["source"]), COVER["box"])
    for width in (2400, 1200):
        save(fit(cover, width=width), OUT / f"cover-{width}.webp", quality=78)
    save(social_card(cover, profile), OUT / "og-cover.jpg", quality=84)

    for f in sorted(OUT.glob("*")):
        print(f"  {f.relative_to(ROOT)}  {f.stat().st_size // 1024} KB")
    bad = check_published_images()
    if bad:
        raise SystemExit(f"Metadata found: {bad}")
    print("OK: all images under assets/ are free of EXIF/XMP/ICC metadata.")


if __name__ == "__main__":
    main()
