"""Shared helpers for the image scripts: load, edit, strip metadata, save, verify."""
import io
from pathlib import Path

from PIL import Image, ImageCms, ImageOps

ROOT = Path(__file__).resolve().parents[1]
RAW_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}



def load_oriented(path):
    """Open an image, apply its EXIF orientation and convert to plain sRGB."""
    im = Image.open(path)
    im = ImageOps.exif_transpose(im)
    icc = im.info.get("icc_profile")
    if icc:
        try:
            src = ImageCms.ImageCmsProfile(io.BytesIO(icc))
            dst = ImageCms.createProfile("sRGB")
            im = ImageCms.profileToProfile(im.convert("RGB"), src, dst, outputMode="RGB")
        except Exception:
            pass
    return im.convert("RGB")


def apply_edit(im, edit):
    """Optional per-image edits: rotate (degrees CCW), crop (fractions l,t,r,b), autocontrast."""
    if not edit:
        return im
    if edit.get("rotate"):
        im = im.rotate(edit["rotate"], expand=True)
    if edit.get("crop"):
        l, t, r, b = edit["crop"]
        W, H = im.size
        im = im.crop((round(l * W), round(t * H), round(r * W), round(b * H)))
    if edit.get("autocontrast"):
        im = ImageOps.autocontrast(im, cutoff=edit["autocontrast"])
    return im


def stripped(im):
    """A brand-new image built from pixels only, so no EXIF/XMP/ICC can carry over."""
    im = im.convert("RGB")
    return Image.frombytes("RGB", im.size, im.tobytes())


def fit(im, long_edge=None, width=None):
    im = im.copy()
    if width and im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    if long_edge and max(im.size) > long_edge:
        im.thumbnail((long_edge, long_edge), Image.LANCZOS)
    return im


def save(im, path, quality=80):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    im = stripped(im)
    if path.suffix == ".webp":
        im.save(path, "WEBP", quality=quality, method=6)
    elif path.suffix in (".jpg", ".jpeg"):
        im.save(path, "JPEG", quality=quality, optimize=True, progressive=True)
    elif path.suffix == ".png":
        im.save(path, "PNG", optimize=True)
    else:
        raise ValueError(path)
    return im.size


def _container_segments(data):
    """Names of the metadata-bearing segments/chunks in a JPEG, WebP or PNG file."""
    found = []
    if data[:2] == b"\xff\xd8":  # JPEG: walk markers until start-of-scan
        i = 2
        while i + 4 <= len(data) and data[i] == 0xFF:
            marker, length = data[i + 1], int.from_bytes(data[i + 2:i + 4], "big")
            if marker == 0xDA:
                break
            if marker in (0xE1, 0xE2, 0xED):  # APP1 (EXIF/XMP), APP2 (ICC), APP13 (IPTC)
                found.append(f"JPEG APP{marker - 0xE0} {data[i + 4:i + 14]!r}")
            i += 2 + length
    elif data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        i = 12
        while i + 8 <= len(data):
            tag, size = data[i:i + 4], int.from_bytes(data[i + 4:i + 8], "little")
            if tag in (b"EXIF", b"XMP ", b"ICCP"):
                found.append(f"WebP chunk {tag!r}")
            i += 8 + size + (size & 1)
    elif data[:8] == b"\x89PNG\r\n\x1a\n":
        i = 8
        while i + 8 <= len(data):
            size, tag = int.from_bytes(data[i:i + 4], "big"), data[i + 4:i + 8]
            if tag in (b"eXIf", b"iTXt", b"tEXt", b"zTXt", b"iCCP"):
                found.append(f"PNG chunk {tag!r}")
            i += 12 + size
    return found


def metadata_problems(path):
    """Return a list of reasons a published image still carries metadata."""
    problems = []
    with Image.open(path) as im:
        if len(im.getexif()):
            problems.append("EXIF tags present")
        for key in ("exif", "xmp", "XML:com.adobe.xmp", "icc_profile", "photoshop"):
            if im.info.get(key):
                problems.append(f"{key} in image info")
    problems += _container_segments(Path(path).read_bytes())
    return problems


def check_published_images():
    """Scan every image under assets/ and fail if any carries metadata."""
    bad = {}
    for p in sorted((ROOT / "assets").rglob("*")):
        if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
            probs = metadata_problems(p)
            if probs:
                bad[str(p.relative_to(ROOT))] = probs
    return bad
