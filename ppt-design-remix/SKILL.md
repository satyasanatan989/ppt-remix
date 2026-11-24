---
name: ppt-design-remix
description: Reverse-engineer a reference PPT's design (layout, colors, fonts, elements) and its motion (transitions, Morph, animations), then build or upgrade a deck in that style, re-themed for a new topic if wanted.
---

# PPT Design Remix

One skill for the look and the motion of a presentation:

- **Design:** pull a reference deck's design DNA and build a new deck in that style (**Clone**), or keep the structure and re-theme it for a new topic (**Remix**).
- **Motion:** read a reference deck's transitions and animations, explain them, and copy them onto another deck, either exactly or as a learned style.

Use whichever parts the request needs: design only, motion only, or both (the usual case is "make a deck like this one, with animations like that one").

## Files

| Path | Purpose |
|---|---|
| `scripts/extract_design.py deck.pptx` | Theme colors and fonts, slide size, each slide's shape mix and text, the most-used fonts, sizes and fill colors |
| `scripts/contact_sheet.py <png-prefix> out.png` | One 4-column grid of rendered slides for viewing a whole deck |
| `scripts/extract_animations.py deck.pptx --json spec.json --md report.md` | Full motion report: transitions (including Morph and other PowerPoint 2010+ effects in `mc:AlternateContent`, with fallback), Morph object pairs, click steps, every effect (name, direction, trigger, start, duration, target and role, paragraph builds), trigger animations, duplicate shape ids |
| `scripts/apply_animations.py target.pptx spec.json out.pptx --map index\|layout\|recipe\|style` | Replays a motion spec on another deck |
| `scripts/animate.py <unzipped-dir>` | Adds a ready-made professional motion set to decks built with this skill's objectName prefixes (no reference needed) |
| `scripts/add_morph.py in.pptx out.pptx [--dur 2000] [--from-slide 2]` | Adds or restores Morph (with a Fade fallback) and renames each continuing object chain to a shared `!!m<k>` name, so PowerPoint pairs exactly the right objects. Use it when a "morph" template came out of Canva or Google Slides with only Fade |
| `scripts/fix_shape_ids.py in.pptx [out.pptx]` | Fixes duplicate shape ids (a pptxgenjs issue on slides with more than ~24 objects). These cause PowerPoint repair prompts and wrong animation targets |
| `scripts/pptx_anim_common.py` | Shared XML helpers |
| `examples/build_deck_pptxgenjs.js` | Complete 40+ slide deck builder: background-image layouts, cards, tables, video buttons, theme |
| `examples/chalk_diagrams.py`, `examples/chalk_chart.py` | Draw backgrounds, diagrams, doodles and charts as images in the deck's style |
| `examples/report_*.md` | Sample motion reports (a Morph deck and an entrance-animation deck) |

---

## Part A: Design

### Two layers of design DNA

| Layer | Holds | Clone | Remix |
|---|---|---|---|
| **Structure** | slide size, grid and margins, layout types, text hierarchy, alignment, density, shape language, image/text ratio, slide rhythm, signature frame (e.g. board + wooden ledge) | keep | keep |
| **Theme** | palette, icons, image subjects, motifs, textures, font mood | keep | adapt to the topic |

If the user hasn't picked a mode and isn't available to ask, use Remix when the topic differs and say which mode you used.

### A1. Extract and look

```bash
python3 scripts/extract_design.py ref.pptx
soffice --headless --convert-to pdf --outdir r ref.pptx && pdftoppm -png -r 20 r/ref.pdf r/ref
python3 scripts/contact_sheet.py r/ref sheet.png    # view it
```

Template decks (SlidesCarnival, Canva) usually keep their real colors in shape fills, not in the theme, so read the COLORS list. Fonts missing on the render machine cause fake overflow in previews.

### A2. Summarise for the user

For each reference, give its feel, structure, palette (hex values with roles), fonts, signature elements and a remix idea. Ask which style to use, the topic and the output format, unless these are already given.

### A3. Re-theme (Remix)

1. Turn the topic into 3–5 mood words and name the audience.
2. Build a new palette with the same color roles and the same light/dark structure, and check WCAG contrast in code (≥ 4.5:1 for body text).
3. Keep the shape language and swap motif subjects.
4. The user's font choice always wins.
5. Tell the user in a few lines what changed.

### A4. Build (pptxgenjs, LAYOUT_WIDE 13.333 × 7.5 in)

- Render the signature frame as one full-slide background PNG and use it in `defineSlideMaster`.
- Use one layout each for content, section and blank slides. The title goes in a placeholder; everything else gets an `objectName` with a prefix: `card`, `icon`, `cardHead`, `cardBody`, `bullets`, `diagram`, `table`, `note`, `doodle`, `videoBtn`, `timeline`, `dot`, `secCircle`, `secNum`, `secName`, `cNum`, `cNumT`, `cText`.
- Use 16–18 pt body text on 13.3-inch slides (never below the user's minimum).
- With no web photos available, draw diagrams in the deck's own style with matplotlib (transparent PNG, `path.sketch`).
- Native charts don't render in many phone viewers, so draw the chart as an image or warn the user. Use real subscript runs, not unusual Unicode subscripts.
- pptxgenjs gotchas:
  - In a bold-label paragraph, put the paragraph options on the **first run only**.
  - Give tables `rowH = availableHeight / rows`.
  - Hyperlinks go in run options: `hyperlink: { url, tooltip }`.
- **Always run `scripts/fix_shape_ids.py` on the built deck.**

### A5. Video links (optional)

Search YouTube in a browser for key concepts. Prefer short institutional or educator videos. Add a "► Watch: Title (m:ss)" pill on each relevant slide plus a "Video Resources" slide. Tell the user to test the links and that the class needs internet access.

---

## Part B: Motion

### B1. Read a reference's motion

`python3 scripts/extract_animations.py ref.pptx --json spec.json --md report.md`. Explain it in plain words: the transition style (for example "Morph by object, 2 s, Fade fallback"), what Morph animates between slides, and the entrance pattern (effect per element type, order, auto or click, gap). Report any duplicate ids.

### B2. Apply motion

| Need | Command |
|---|---|
| Same design and slide count, exact copy | `--map index` |
| Match slides by layout name | `--map layout` |
| One slide's choreography everywhere | `--map recipe --recipe N` |
| **A different deck** (most common) | `--map style --skip-title` learns the effect per role (text/picture/shape/table/group), paragraph builds, median gap, auto vs click and the main transition, then applies them to any layout. Backgrounds stay static |
| A single transition everywhere (e.g. Morph) | `--transitions-only --transition-from N` |

Shapes map by exact name first, then by role in order (`--loose` allows cross-role). Unmatched effects are skipped and counted.

**Lost Morph:** Canva, Google Slides and PowerPoint-2010-format exports replace Morph with plain Fade. Signs of this: a file or template named "…Morph…", big images and elements placed partly off-slide, and the same pictures repeated on consecutive slides. Run `add_morph.py`, show the user the pair list from `extract_animations.py`, and remind them that Morph only plays in PowerPoint 2019/365.

### B3. No motion reference?

For decks built in Part A, use the built-in motion set:

```bash
mkdir ux && cd ux && unzip -q ../deck.pptx && cd ..
python3 scripts/animate.py ux
cd ux && zip -qXrD ../deck_animated.pptx '[Content_Types].xml' _rels docProps ppt
```

This gives Fade transitions (Push-up for section slides), cards that Float In with their parts, bullets that build line by line, diagrams that Fade, doodles that Zoom and a timeline that Wipes, all auto-sequenced. Offer an On-Click variant.

### How the timing XML works

- `p:timing › tnLst › par › cTn[tmRoot] › seq › cTn[mainSeq]` holds the click groups. `evt="onBegin"` + `<p:tn val="2"/>` means the group auto-starts; `delay="indefinite"` alone means it waits for a click. Inside are offset groups (start ms), then effect pars (`presetClass`, `presetID`, `presetSubtype`: 1 top · 2 right · 4 bottom · 8 left, `nodeType`: click/with/after, `grpId`).
- Targets are `p:spTgt spid` (the shape's `p:cNvPr id`) plus an optional `p:txEl/p:pRg`. `bldLst/bldP` declares text builds (`build="p"`).
- The transition comes before the timing: a plain `p:transition`, or `mc:AlternateContent` (Choice `Requires=p14|p15|p159` plus Fallback). Copy the whole wrapper.
- Keep cTn ids 1 and 2, and renumber the others uniquely per slide.
- Entrance preset IDs: 1 Appear · 2 Fly In · 10 Fade · 16 Split · 21 Wheel · 22 Wipe · 23 Zoom · 26 Bounce · 37 Rise Up · 42 Float In · 47 Float Down · 53 Fade+Zoom · 55 Expand. Emphasis: 6 Grow/Shrink · 8 Spin · 9 Transparency.

---

## Verify (always)

1. Run `validate.py` from the pptx skill, then render to PNG and look at every slide (contact sheets). Check for overflow, overlaps, buttons hitting content, contrast and leftover placeholders.
2. After motion work, re-extract the output and compare with what you expected (a same-design round-trip must match exactly). Convert to .odp and grep `presentation:preset-id` to confirm the effects parse.
3. Before delivering, verify factual or regulatory claims with a web search.

## Tell the user

- Morph needs PowerPoint 2019/365; elsewhere it falls back to Fade. Morph only looks good when objects with the same name, image or text exist on consecutive slides. Name shapes `!!name` to force pairs.
- Google Slides and phone viewers ignore animations, so present from PowerPoint.
- Name any fallback fonts and the count of skipped effects.

## Rules

- Copy only the design system and the motion. Never copy a reference's logos, characters, photos, text or branding.
- Ask before overwriting existing animations in a user's deck.
- Keep the spec and the build script next to the output so the style can be reused.
