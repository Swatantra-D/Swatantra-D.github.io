# swatantra-d.github.io

Personal academic website of **Swatantra Dhara**: <https://swatantra-d.github.io>

Built with Jekyll and published by GitHub Pages' built-in build (no Actions workflow,
no unsupported plugins). The content model comes from the
[academicpages](https://github.com/academicpages/academicpages.github.io) template (MIT, see
`LICENSE`); layouts, styles and scripts are custom.

```text
_config.yml          site settings, author profile, e-mail, Formspree ID
_data/               navigation, news strip, timelines, skills, CV details, photo manifest
_pages/              the nine pages (home, research, blog, publications, teaching, ...)
_portfolio/          research projects        -> /research/
_posts/              blog posts               -> /blog/
_publications/       papers, posters, theses  -> /publications-talks/
_talks/              talks, invited lectures  -> /publications-talks/ and /teaching-mentoring/
_teaching/           TA roles, workshops      -> /teaching-mentoring/
_layouts/ _includes/ HTML templates (figures/ holds the code-drawn research schematics)
assets/              css/main.css, js/site.js, fonts, images, photos, the public CV PDF
scripts/             image, figure and CV-redaction scripts (not published)
originals/           PRIVATE full-resolution sources and unredacted CV (git-ignored)
photos-raw/          PRIVATE original photos with EXIF/GPS (git-ignored)
```

## Preview locally

Install Ruby once (Windows):

```powershell
winget install --id RubyInstallerTeam.RubyWithDevKit.3.3 -e
# open a new terminal, then:
ridk install 3
gem install bundler
```

Then, from this folder:

```powershell
bundle install
bundle exec jekyll serve
```

Open <http://localhost:4000>. Changes to files rebuild automatically; restart after editing `_config.yml`.

No Ruby? With Docker Desktop running:

```powershell
docker run --rm -p 4000:4000 -v "${PWD}:/srv/site" -v sd-jekyll-bundle:/usr/local/bundle -w /srv/site ruby:3.3 `
  bash -lc "bundle install && bundle exec jekyll serve --host 0.0.0.0 --force_polling"
```

## Publish a change

```powershell
git add -A
git commit -m "Describe the change"
git push
```

GitHub Pages rebuilds the site in a minute or two. Check the build under the repository's **Actions** tab.

## Everyday edits

| To change… | Edit |
| --- | --- |
| E-mail address | `author.email` in `_config.yml` (replace `YOUR_EMAIL_HERE`) |
| Contact form | create a form at [formspree.io](https://formspree.io), put its ID in `formspree_id` in `_config.yml` |
| News strip on the home page | `_data/news.yml` (newest first; the first four are shown; `text` accepts Markdown) |
| Count-up numbers | `_data/facts.yml` |
| Home timeline | `_data/timeline.yml` (`kind: education` or `experience`) |
| About text, interests, identity line | `_pages/home.html` (front matter and the four paragraphs) |
| Experience & Service timeline | `_data/experience.yml` (`kind: research`, `leadership` or `service`) |
| Skills and CV sections | `_data/skills.yml`, `_data/cv.yml` |
| Navigation order | `_data/navigation.yml` |
| Colours, fonts, spacing | the tokens at the top of `assets/css/main.css` (light and dark sets) |

Search the repository for `PLACEHOLDER` to find everything still waiting for real content.

## Add a blog post

Create `_posts/YYYY-MM-DD-short-title.md`:

```markdown
---
title: "Your title"
date: 2026-11-15
tags: [fMRI, methods]
excerpt: "One or two sentences for the blog index and social previews."
draft_badge: false      # true shows a "Draft – verify" badge
---

Opening paragraph...

<!--more-->

## A section heading

Use ## and ### headings; they build the table of contents automatically.
```

Fenced code blocks (```` ```python ````) are syntax-highlighted. Posts dated in the future are not published until that date.

## Add a publication, talk or teaching entry

`_publications/2027-short-name.md`:

```markdown
---
title: "Paper title"
collection: publications
category: papers            # papers | posters | theses (see publication_category in _config.yml)
date: 2027-03-01            # used for sorting
year: 2027
authors: "A. Author, Swatantra Dhara, B. Author"   # your name is highlighted automatically
venue: "Journal or conference"
link_label: "Journal page"
paperurl: "https://..."
bibtex: |
  @article{key2027,
    title = {...},
    ...
  }
---
```

`_talks/2027-name.md` takes `title`, `type` (e.g. "Invited lecture"), `date`, `year`, `venue`, `location`, `slides`.
`_teaching/name.md` takes `title`, `type` ("Teaching assistant" or "Workshop"), `term`, `date`, `venue`, `location`.

## Add a research project

Copy any file in `_portfolio/` and edit the front matter. `filters` uses the slugs in
`_data/research_filters.yml`; `order` sets the position on the page.

### Swap a schematic for a real figure

Every project file has one commented line for this:

```yaml
image: /assets/img/research/brain-state-transitions.webp
image_alt: "What the figure shows"
```

Put the image in `assets/img/research/` (WebP or JPEG, about 1600 px wide, 16:10 works best).
While `image` is empty, the card shows the code-drawn schematic named by `figure`. The schematics are
generated by `python scripts/make_figures.py` into `_includes/figures/`.

## Add photos to the gallery

1. Drop the original photos into `photos-raw/` (this folder is never committed).
2. Run:

   ```powershell
   pip install pillow
   python scripts/process_photos.py
   ```

   This writes a ~1600 px web version and a ~600 px thumbnail of each photo to `assets/photos/`,
   strips **all** metadata (EXIF, GPS, XMP, colour profiles), and adds an entry to `_data/photos.json`.
   The script stops with an error if any published image still carries metadata.
3. In `_data/photos.json`, edit the new entry's `title`, `category`, `caption` and `alt`
   (describe what is in the photo for screen-reader users), and set `caption_is_draft` to `false`.
   Optional `edit` keys: `rotate` (degrees counter-clockwise), `crop` (`[left, top, right, bottom]` as
   fractions) and `autocontrast`. Re-run the script after changing them.
4. Commit and push.

New categories appear as filter buttons automatically.

## Swap the profile picture or cover image

Put the new source image in `originals/` named `profile.jpg` (it is centre-cropped to a square)
and/or `cover.jpg` (a wide image that still reads well with text over its left side), then run:

```powershell
python scripts/make_profile_cover.py
```

It regenerates `assets/img/profile-800.webp`, `profile-400.webp`, `apple-touch-icon.png`,
`cover-2400.webp`, `cover-1200.webp` and the 1200×630 social preview `og-cover.jpg`, all without metadata.
Without those files it uses the crop boxes at the top of the script on `originals/portrait-source.jpg`.

## Update the CV

1. Save the new CV as `originals/CV_Swatantra_Dhara.pdf`. Optionally list exact private strings
   (phone number, e-mail addresses, short-link IDs), one per line, in `originals/redaction_terms.txt`;
   the check then also hunts for each of them. That file is git-ignored, so it is never published.
2. Run:

   ```powershell
   pip install pymupdf pypdf
   python scripts/redact_cv.py
   ```

   The script deletes the phone number, supervisors' e-mail addresses and the documents short-link
   from the page content (not a box drawn over them), removes `mailto:` links, then re-reads the
   result with two PDF libraries and a raw-object scan. It refuses to write the file if anything
   is left. Read the "Changed lines" it prints before committing `assets/Swatantra_Dhara_CV.pdf`.

## Privacy

- Never commit `originals/` or `photos-raw/`; both are in `.gitignore`.
- The site never shows the phone number, supervisors' e-mail addresses or the documents short-link.
- All published images are re-encoded from pixels only, so camera metadata (including GPS) cannot leak.

## Design and accessibility notes

- One stylesheet (`assets/css/main.css`, plain CSS, no Sass build) and one script
  (`assets/js/site.js`, vanilla JS, no libraries).
- Light and dark themes follow the system setting until the visitor uses the toggle; the choice is
  remembered in `localStorage`.
- Page changes use cross-document View Transitions where supported, with a fade/slide fallback.
- Every animation is switched off for visitors who ask for reduced motion.
- Text colours meet WCAG AA contrast in both themes.

## Credits

- Content model: [academicpages](https://github.com/academicpages/academicpages.github.io), MIT licence (`LICENSE`).
- Fonts: [Newsreader](https://github.com/productiontype/Newsreader) and
  [Instrument Sans](https://github.com/Instrument/instrument-sans), SIL Open Font License
  (`assets/fonts/OFL-*.txt`).
- LinkedIn and GitHub marks: [Simple Icons](https://simpleicons.org) (CC0).
