"""Process the photography gallery.

  photos-raw/<name>.jpg   (originals, git-ignored)
    -> assets/photos/web/<name>.webp     ~1600 px long edge
    -> assets/photos/thumb/<name>.webp   ~600 px long edge
    -> _data/photos.json                 manifest the gallery page is built from

All EXIF/XMP/ICC metadata (including GPS) is stripped; the script fails if any
image under assets/ still carries metadata.

The manifest keeps whatever you edit by hand (title, category, caption, alt,
optional "edit" block). New photos get placeholder text marked as a draft.
Optional per-photo "edit" keys: "rotate" (degrees counter-clockwise),
"crop" ([left, top, right, bottom] as fractions), "autocontrast" (percent cutoff).

Usage:  python scripts/process_photos.py
"""
import json
from pathlib import Path

from imgutil import ROOT, RAW_EXTS, apply_edit, check_published_images, fit, load_oriented, save

RAW = ROOT / "photos-raw"
WEB = ROOT / "assets" / "photos" / "web"
THUMB = ROOT / "assets" / "photos" / "thumb"
MANIFEST = ROOT / "_data" / "photos.json"
WEB_EDGE, THUMB_EDGE = 1600, 600


def main():
    entries = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else []
    by_name = {e["filename"]: e for e in entries}

    raws = sorted(p for p in RAW.iterdir() if p.suffix.lower() in RAW_EXTS) if RAW.exists() else []
    for raw in raws:
        entry = by_name.get(raw.name)
        if entry is None:
            entry = {
                "filename": raw.name,
                "title": raw.stem.replace("-", " ").replace("_", " ").capitalize(),
                "category": "Uncategorised",
                "caption": "Add a caption.",
                "caption_is_draft": True,
                "alt": "TODO: describe what is in this photo.",
            }
            entries.append(entry)
            by_name[raw.name] = entry
            print(f"  new photo: {raw.name} (edit its title, category, caption and alt in _data/photos.json)")

        im = apply_edit(load_oriented(raw), entry.get("edit"))
        stem = raw.stem
        w, h = save(fit(im, long_edge=WEB_EDGE), WEB / f"{stem}.webp", quality=80)
        tw, th = save(fit(im, long_edge=THUMB_EDGE), THUMB / f"{stem}.webp", quality=74)
        entry.update({
            "web": f"/assets/photos/web/{stem}.webp",
            "thumb": f"/assets/photos/thumb/{stem}.webp",
            "width": w, "height": h, "thumb_width": tw, "thumb_height": th,
        })
        print(f"  {raw.name}: web {w}x{h} ({(WEB / f'{stem}.webp').stat().st_size // 1024} KB), "
              f"thumb {tw}x{th} ({(THUMB / f'{stem}.webp').stat().st_size // 1024} KB)")

    missing = [e["filename"] for e in entries if not (RAW / e["filename"]).exists()]
    for name in missing:
        print(f"  warning: {name} is in the manifest but not in photos-raw/ (kept; delete the entry to remove it)")

    MANIFEST.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    bad = check_published_images()
    if bad:
        raise SystemExit(f"Metadata found: {bad}")
    print(f"OK: {len(entries)} photos in _data/photos.json; all images under assets/ are metadata-free.")


if __name__ == "__main__":
    main()
