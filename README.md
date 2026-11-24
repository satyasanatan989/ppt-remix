# 🎨 REA-Powerpoint

**Steal the look *and* the motion of any PowerPoint — then rebuild it for your own topic.**

A [Claude skill](https://docs.claude.com) that reverse-engineers a reference `.pptx` (layout, colors, fonts, shapes, transitions, Morph, animations) and builds a new deck in that style.

## What it does

| | |
|---|---|
| 🧬 **Clone** | Extract a deck's design DNA and build a new one in the same style |
| 🔁 **Remix** | Keep the structure, re-theme palette/imagery for a new topic |
| 🎬 **Motion copy** | Read transitions, Morph pairs and animations, replay them on another deck |
| ✨ **Auto-animate** | Add a professional motion set to any deck, no reference needed |
| 🛠️ **Fixers** | Repair duplicate shape IDs (PowerPoint "repair" prompts), restore Morph from Canva/Google Slides exports |

## Install

Copy the `ppt-design-remix/` folder into your Claude skills directory (e.g. `~/.claude/skills/`), or zip it and upload it in Claude → Settings → Skills.

## Use

> "Make a 10-slide deck about renewable energy that looks and moves like `reference.pptx`."

## Requirements

Python 3, `python-pptx`, `lxml`, LibreOffice (`soffice`) and `pdftoppm` for previews, Node + `pptxgenjs` for the example builder.

## Layout

```
ppt-design-remix/
├── SKILL.md       # the skill instructions
├── scripts/       # extract_design, extract_animations, apply_animations, add_morph, ...
└── examples/      # deck builder + sample motion reports
```

## License

MIT
