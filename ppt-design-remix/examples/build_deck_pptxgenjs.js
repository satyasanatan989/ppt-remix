const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");
const { applyTheme } = require("<pptx-skill-dir>/scripts/apply_theme.js");

const IMG = "./img/";
const FONT = "Times New Roman";
const HEX = { board: "22302B", chalk: "F3F1EA", card: "2A3A34", wall: "C3D3C8", yel: "F3E28F", mint: "7FDCC4", org: "F4A259", cor: "EE8E8E", blu: "A9C8F0", wood: "8A5A3B", muted: "B9C4BE" };
const THEME = {
  name: "Chalkboard Nano",
  headFontFace: FONT, bodyFontFace: FONT,
  colors: { dk1: HEX.board, lt1: HEX.chalk, dk2: HEX.card, lt2: HEX.wall, accent1: HEX.yel, accent2: HEX.mint, accent3: HEX.org, accent4: HEX.cor, accent5: HEX.blu, accent6: HEX.wood, hlink: HEX.mint, folHlink: HEX.blu },
};

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.author = "Prabhash Kumar";
pres.title = "Role of Nanotechnology in Food Packaging";
pres.theme = { headFontFace: FONT, bodyFontFace: FONT };
const C = pres.SchemeColor;
const COL = { chalk: C.background1, yel: C.accent1, mint: C.accent2, org: C.accent3, cor: C.accent4, blu: C.accent5, card: C.text2, board: C.text1 };
const ACC = [COL.mint, COL.yel, COL.org, COL.cor, COL.blu];
const ACCHEX = [HEX.mint, HEX.yel, HEX.org, HEX.cor, HEX.blu];

// ---------- layouts ----------
pres.defineSlideMaster({
  title: "CHALK_CONTENT",
  background: { path: IMG + "bg_content.png" },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: 0.9, y: 0.55, w: 11.53, h: 0.8, fontFace: FONT, fontSize: 30, bold: true, color: COL.yel, align: "center", valign: "middle" }, text: "" } },
  ],
  slideNumber: { x: 12.0, y: 6.3, w: 0.6, h: 0.3, fontFace: FONT, fontSize: 12, color: HEX.muted, align: "right" },
});
pres.defineSlideMaster({
  title: "CHALK_SECTION",
  background: { path: IMG + "bg_section.png" },
  objects: [
    { placeholder: { options: { name: "num", type: "body", x: 3.6, y: 1.15, w: 6.13, h: 1.5, fontFace: FONT, fontSize: 80, bold: true, color: COL.yel, align: "center", valign: "middle" }, text: "" } },
    { placeholder: { options: { name: "title", type: "title", x: 3.6, y: 2.7, w: 6.13, h: 2.1, fontFace: FONT, fontSize: 36, bold: true, color: COL.chalk, align: "center", valign: "middle" }, text: "" } },
  ],
});
pres.defineSlideMaster({ title: "CHALK_BLANK", background: { path: IMG + "bg_content.png" }, objects: [] });

// ---------- helpers ----------
async function icon(name, hex, size = 256) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(fa[name], { color: "#" + hex, size: String(size) }));
  const buf = await sharp(Buffer.from(svg)).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}
let objN = 0;
const nm = (p) => `${p}_${++objN}`;

function content(title, section) {
  const s = pres.addSlide({ masterName: "CHALK_CONTENT", sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  return s;
}
function sectionSlide(num, title, section, doodle) {
  const s = pres.addSlide({ masterName: "CHALK_SECTION", sectionTitle: section });
  s.addText(num, { placeholder: "num" });
  s.addText(title, { placeholder: "title" });
  if (doodle) {
    s.addImage({ path: IMG + doodle[0], x: 0.6, y: 1.4, w: doodle[1], h: doodle[2], objectName: nm("doodle") });
    s.addImage({ path: IMG + "d_leaf.png", x: 10.9, y: 2.6, w: 1.6, h: 1.92, objectName: nm("doodle") });
  }
  return s;
}
// items: string | [bold, rest]
function bullets(s, items, x, y, w, h, size = 16, color = COL.chalk) {
  size = size + 2;
  const runs = [];
  items.forEach((it, i) => {
    const last = i === items.length - 1;
    if (Array.isArray(it)) {
      runs.push({ text: it[0], options: { bold: true, color: COL.yel, paraSpaceAfter: 12 } });
      runs.push({ text: " " + it[1], options: { color, breakLine: !last } });
    } else runs.push({ text: it, options: { color, breakLine: !last, paraSpaceAfter: 12 } });
  });
  s.addText(runs, { x, y, w, h, fontFace: FONT, fontSize: size, valign: "top", margin: 4, isTextBox: true, objectName: nm("bullets") });
}
async function card(s, x, y, w, h, head, body, acc = 0, ic = null, bodySize = 14) {
  bodySize += 2;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.12, fill: { color: COL.card }, line: { color: ACC[acc], width: 1.75, dashType: "solid" }, objectName: nm("card") });
  let ty = y + 0.15;
  if (ic) {
    s.addImage({ data: await icon(ic, ACCHEX[acc]), x: x + 0.2, y: y + 0.2, w: 0.45, h: 0.45, objectName: nm("icon") });
    s.addText(head, { x: x + 0.75, y: y + 0.15, w: w - 0.9, h: 0.55, fontFace: FONT, fontSize: 19, bold: true, color: ACC[acc], valign: "middle", margin: 0, isTextBox: true, objectName: nm("cardHead") });
  } else {
    s.addText(head, { x: x + 0.2, y: ty, w: w - 0.4, h: 0.55, fontFace: FONT, fontSize: 19, bold: true, color: ACC[acc], valign: "middle", margin: 0, isTextBox: true, objectName: nm("cardHead") });
  }
  ty = y + 0.78;
  if (body) s.addText(body, { x: x + 0.2, y: ty, w: w - 0.4, h: h - 0.9, fontFace: FONT, fontSize: bodySize, color: COL.chalk, valign: "top", margin: 0, isTextBox: true, objectName: nm("cardBody") });
}
function img(s, file, x, y, w, h) { s.addImage({ path: IMG + file, x, y, w, h, objectName: nm("diagram") }); }
function note(s, text, x, y, w, h, color = COL.mint, size = 14) {
  s.addText(text, { x, y, w, h, fontFace: FONT, fontSize: size, italic: true, color, valign: "middle", margin: 0, isTextBox: true, objectName: nm("note") });
}
function table(s, rows, x, y, w, colW, size = 13, availH = 4.6) {
  size = 16;
  const head = rows[0].map((t) => ({ text: t, options: { bold: true, color: COL.board, fill: { color: COL.mint }, fontSize: size + 1 } }));
  const body = rows.slice(1).map((r) => r.map((t, j) => ({ text: t, options: { color: j === 0 ? COL.yel : COL.chalk, bold: j === 0, fill: { color: COL.card } } })));
  s.addTable([head, ...body], { x, y, w, colW, fontFace: FONT, fontSize: size, border: { type: "solid", pt: 0.75, color: HEX.mint }, valign: "middle", margin: [4, 8, 4, 8], rowH: Math.min(0.75, availH / rows.length), objectName: nm("table") });
}


const VIDEOS = [
  [4, "How Big Is a Nanometer?", "World Science Festival", "1:29", "IC3AcItKc3U"],
  [6, "How Will Nanotechnology Keep Your Food Safe?", "VPM Science Matters", "0:59", "7U-DLhvmQ7k"],
  [10, "Things Are Different at the Nanoscale", "MNT-EC", "3:23", "yc-oEO0r8do"],
  [13, "How Silver-ion Antimicrobial Technology Fights Bacteria", "BioClad", "0:37", "NYDOZzpH99E"],
  [19, "What is Electrospinning? (Episode 1)", "Nanoscience Instruments", "3:04", "GbiC49VsLI8"],
  [21, "Nanotechnology in Food Packaging (overview)", "Nanopresentation MChem", "10:53", "gl_At1qcEXM"],
  [27, "Freshness Indicator with Colour-Changing Smart Labels", "Bizongo", "1:03", "d0hz5ArpI2k"],
  [28, "Embedded Colour-Changing Labels", "Insignia Technologies", "0:41", "k0kpOoe-42g"],
  [30, "IIT Guwahati Coating Keeps Fruits & Vegetables Fresh", "The Indian Express", "3:33", "Fz-4mfpIuT0"],
  [34, "Silver Nanoparticle Risks and Benefits", "Risk Bites", "4:00", "Yz6LuH-11II"],
];
const yt = (id) => "https://www.youtube.com/watch?v=" + id;

(async () => {
  // ===== 1 Title =====
  pres.addSection({ title: "Opening" });
  let s = pres.addSlide({ masterName: "CHALK_BLANK", sectionTitle: "Opening" });
  s.addText("FOOD SCIENCE & TECHNOLOGY SEMINAR", { x: 2.4, y: 1.15, w: 8.53, h: 0.45, fontFace: FONT, fontSize: 16, color: COL.mint, align: "center", charSpacing: 3, isTextBox: true, objectName: "kicker" });
  s.addText("Role of Nanotechnology\nin Food Packaging", { x: 1.9, y: 1.7, w: 9.53, h: 2.3, fontFace: FONT, fontSize: 50, bold: true, color: COL.yel, align: "center", valign: "middle", isTextBox: true, objectName: "deckTitle" });
  s.addText("Principles and Applications", { x: 2.4, y: 4.05, w: 8.53, h: 0.6, fontFace: FONT, fontSize: 24, italic: true, color: COL.chalk, align: "center", isTextBox: true, objectName: "deckSubtitle" });
  s.addText("Presented by: Prabhash Kumar  |  B.Tech Food Science & Technology", { x: 2.4, y: 5.2, w: 8.53, h: 0.45, fontFace: FONT, fontSize: 16, color: COL.chalk, align: "center", isTextBox: true, objectName: "presenter" });
  img(s, "d_box.png", 0.75, 3.8, 2.3, 2.3);
  img(s, "d_molecule.png", 10.4, 0.7, 2.2, 1.47);
  img(s, "d_np.png", 10.8, 4.1, 1.8, 1.8);
  img(s, "d_squiggle.png", 0.9, 0.75, 1.9, 0.76);

  // ===== 2 Contents =====
  s = content("Contents", "Opening");
  const secs = [["01", "Introduction"], ["02", "Principles"], ["03", "Nanomaterials & Fabrication"], ["04", "Applications"], ["05", "Safety & Regulation"], ["06", "Future & Conclusion"]];
  for (let i = 0; i < 6; i++) {
    const col = i % 3, row = Math.floor(i / 3);
    const x = 1.2 + col * 3.75, y = 1.75 + row * 2.3;
    s.addShape(pres.shapes.OVAL, { x, y, w: 1.25, h: 1.25, fill: { type: "none" }, line: { color: ACC[i % 5], width: 2 }, objectName: nm("secCircle") });
    s.addText(secs[i][0], { x, y, w: 1.25, h: 1.25, fontFace: FONT, fontSize: 30, color: ACC[i % 5], align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: nm("secNum") });
    s.addText(secs[i][1], { x: x + 1.4, y: y + 0.2, w: 2.2, h: 0.85, fontFace: FONT, fontSize: 18, bold: true, color: COL.chalk, valign: "middle", margin: 0, isTextBox: true, objectName: nm("secName") });
  }

  // ===== Section 01 =====
  pres.addSection({ title: "Introduction" });
  sectionSlide("01", "INTRODUCTION", "Introduction", ["d_np.png", 2.2, 2.2]);

  s = content("What is Nanotechnology?", "Introduction");
  bullets(s, [
    ["Definition:", "design, production and use of materials with at least one dimension in the 1–100 nm range."],
    ["Scale:", "1 nanometre (nm) = 10⁻⁹ m, i.e. one-billionth of a metre."],
    ["Key idea:", "at this size, materials show new physical, chemical and biological properties not seen in the bulk form."],
    ["In packaging:", "nanoparticles, nanofibres, nanoplatelets or nanocoatings are added to films, containers and labels."],
  ], 0.95, 1.6, 4.9, 4.7, 16);
  img(s, "nano_scale.png", 6.0, 1.75, 6.4, 3.02);
  note(s, "Nanoparticles sit between viruses and single molecules on the size scale.", 6.1, 5.05, 6.2, 0.6);

  s = content("Functions of Food Packaging", "Introduction");
  await card(s, 0.95, 1.6, 2.75, 2.45, "Containment", "Holds the product and allows handling, storage and transport.", 0, "FaBoxOpen");
  await card(s, 3.85, 1.6, 2.75, 2.45, "Protection", "Shields food from O₂, moisture, light, microbes, dust and physical damage.", 1, "FaShieldAlt");
  await card(s, 6.75, 1.6, 2.75, 2.45, "Communication", "Label carries brand, nutrition, FSSAI licence number and dates.", 2, "FaComments");
  await card(s, 9.65, 1.6, 2.75, 2.45, "Convenience", "Easy opening, portion control, microwaveable and ready-to-eat formats.", 3, "FaHandHolding");
  s.addText([{ text: "Limits of conventional plastics: ", options: { bold: true, color: COL.cor } }, { text: "permeable to O₂, CO₂ and water vapour; weak at thin gauges; passive (cannot fight microbes or signal spoilage); mostly non-biodegradable.", options: { color: COL.chalk } }],
    { x: 0.95, y: 4.4, w: 11.45, h: 1.3, fontFace: FONT, fontSize: 16, valign: "middle", margin: 0, isTextBox: true, objectName: "limits" });

  s = content("Why Nanotechnology in Packaging?", "Introduction");
  const why = [["FaWind", "Better barrier", "Lower O₂ and moisture transmission"], ["FaDumbbell", "Stronger films", "Same strength with less material"], ["FaBacterium", "Antimicrobial", "Inhibits spoilage and pathogens"], ["FaMicrochip", "Smart sensing", "Shows freshness in real time"], ["FaClock", "Longer shelf life", "Slower oxidation and spoilage"], ["FaLeaf", "Greener options", "Makes biopolymer films usable"]];
  for (let i = 0; i < 6; i++) {
    const col = i % 3, row = Math.floor(i / 3);
    await card(s, 0.95 + col * 3.85, 1.6 + row * 2.3, 3.6, 2.05, why[i][1], why[i][2], i % 5, why[i][0], 15);
  }

  s = content("Evolution of Food Packaging", "Introduction");
  const evo = [["Passive", "Simple barrier: glass, tin, paper, plastic"], ["Modified atmosphere", "Vacuum and gas-flushed packs (N₂, CO₂)"], ["Active", "Interacts with food: scavengers, absorbers, emitters"], ["Intelligent", "Monitors and communicates food condition"], ["Nano-enabled", "Nanomaterials boost barrier, activity and sensing"]];
  s.addShape(pres.shapes.LINE, { x: 1.9, y: 3.6, w: 9.6, h: 0, line: { color: HEX.chalk, width: 2.5 }, objectName: "timeline" });
  for (let i = 0; i < 5; i++) {
    const x = 1.9 + i * 2.4;
    s.addShape(pres.shapes.OVAL, { x: x - 0.25, y: 3.35, w: 0.5, h: 0.5, fill: { color: ACC[i] }, line: { color: ACC[i] }, objectName: nm("dot") });
    s.addText(evo[i][0], { x: x - 1.15, y: 2.2, w: 2.3, h: 0.95, fontFace: FONT, fontSize: 20, bold: true, color: ACC[i], align: "center", valign: "bottom", margin: 0, isTextBox: true, objectName: nm("evoHead") });
    s.addText(evo[i][1], { x: x - 1.15, y: 4.05, w: 2.3, h: 1.4, fontFace: FONT, fontSize: 16, color: COL.chalk, align: "center", valign: "top", margin: 0, isTextBox: true, objectName: nm("evoBody") });
  }
  note(s, "Nanotechnology does not replace active/intelligent packaging — it makes them work better.", 1.2, 5.65, 10.9, 0.5, COL.mint, 16);

  // ===== Section 02 =====
  pres.addSection({ title: "Principles" });
  sectionSlide("02", "PRINCIPLES", "Principles", ["d_molecule.png", 2.4, 1.6]);

  s = content("Principle 1: High Surface Area to Volume Ratio", "Principles");
  img(s, "sav.png", 0.95, 1.75, 6.0, 3.19);
  bullets(s, [
    "Smaller particles → a larger share of atoms sit on the surface.",
    "More surface means higher reactivity and stronger contact with the polymer matrix.",
    ["Result:", "small loadings (often 1–5 wt%) can change film properties markedly."],
    "Also why nano-Ag, ZnO and TiO₂ are far more antimicrobial than their bulk forms.",
  ], 7.2, 1.7, 5.2, 4.6, 16);

  s = content("Principle 2: Size-Dependent Properties", "Principles");
  const p2 = [["FaEye", "Optical", "Particles much smaller than visible-light wavelengths (400–700 nm) scatter little light, so films stay transparent."], ["FaDumbbell", "Mechanical", "Stiff nanofillers with huge interfacial area transfer stress from the polymer, raising modulus and strength."], ["FaFire", "Thermal", "Well-dispersed fillers restrict chain movement and can raise heat resistance and delay degradation."], ["FaAtom", "Chemical / catalytic", "Quantum and surface effects increase reactivity, e.g. photocatalysis by nano-TiO₂ under UV light."]];
  for (let i = 0; i < 4; i++) {
    const col = i % 2, row = Math.floor(i / 2);
    await card(s, 0.95 + col * 5.8, 1.6 + row * 2.4, 5.6, 2.2, p2[i][1], p2[i][2], i, p2[i][0], 15);
  }

  s = content("Principle 3: The Tortuous Path (Barrier)", "Principles");
  img(s, "tortuous.png", 0.95, 1.55, 7.0, 3.32);
  bullets(s, [
    "Nanoclay platelets are impermeable to gases.",
    "Gas and water molecules must travel around them, taking a longer, winding route.",
    "Longer path → slower diffusion → lower O₂ and water-vapour transmission rates.",
    ["Best when:", "platelets are well exfoliated, have high aspect ratio and lie parallel to the film surface."],
  ], 8.15, 1.6, 4.3, 4.75, 15);

  s = content("Nielsen Model: How Much Barrier Gain?", "Principles");
  img(s, "nielsen.png", 0.95, 1.5, 7.2, 4.6);
  s.addText([{ text: "P" }, { text: "c", options: { subscript: true } }, { text: " / P" }, { text: "p", options: { subscript: true } }, { text: " = (1 − φ) / (1 + (α/2)·φ)" }], { x: 8.4, y: 1.7, w: 4.0, h: 0.7, fontFace: FONT, fontSize: 20, bold: true, color: COL.yel, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "formula" });
  bullets(s, [
    ["φ", "= volume fraction of platelets"],
    ["α", "= aspect ratio (length / thickness)"],
    "Higher α gives a much bigger drop in permeability at the same loading.",
    "Model assumes ideal, aligned, fully exfoliated platelets; real films perform below it.",
  ], 8.4, 2.6, 4.0, 3.7, 15);

  s = content("Principle 4: Antimicrobial Mechanisms", "Principles");
  img(s, "antimicrobial.png", 0.95, 1.55, 6.6, 3.96);
  bullets(s, [
    ["Ion release:", "Ag⁺ ions bind thiol (–SH) groups of enzymes and proteins."],
    ["ROS generation:", "ZnO and TiO₂ produce reactive oxygen species (•OH, O₂•⁻, H₂O₂), causing oxidative stress."],
    ["Membrane damage:", "direct contact disrupts the cell wall and causes leakage."],
    ["DNA damage:", "interference with replication."],
    ["Chitosan NPs:", "positive charges bind the negatively charged cell surface."],
  ], 7.75, 1.55, 4.7, 4.85, 14);

  s = content("Principle 5: Dispersion & Interface", "Principles");
  bullets(s, [
    ["Dispersion is everything:", "agglomerated nanoparticles behave like ordinary micro-fillers and lose their benefits."],
    ["Compatibility problem:", "natural clay is hydrophilic, while PE, PP and PET are hydrophobic."],
    ["Solution — organoclay:", "clay is modified with quaternary-ammonium surfactants so polymer chains can enter the galleries."],
    ["Compatibilisers:", "e.g. maleic-anhydride-grafted polymers improve filler–matrix bonding."],
    ["Processing:", "shear, temperature and residence time during extrusion decide the final structure."],
  ], 0.95, 1.6, 6.6, 4.8, 16);
  await card(s, 7.9, 1.75, 4.5, 2.0, "Poor dispersion", "Clumps → defects, weak spots, opacity, little barrier gain.", 3, "FaExclamationTriangle", 15);
  await card(s, 7.9, 4.0, 4.5, 2.0, "Good dispersion", "Uniform platelets → transparency, strength and a high barrier.", 0, "FaCheckCircle", 15);

  // ===== Section 03 =====
  pres.addSection({ title: "Nanomaterials & Fabrication" });
  sectionSlide("03", "NANOMATERIALS & FABRICATION", "Nanomaterials & Fabrication", ["d_np.png", 2.2, 2.2]);

  s = content("Nanomaterials Used in Food Packaging", "Nanomaterials & Fabrication");
  table(s, [
    ["Nanomaterial", "Type", "Main function in packaging"],
    ["Montmorillonite nanoclay", "Layered silicate", "Gas & moisture barrier, stiffness, heat resistance"],
    ["Silver nanoparticles (AgNPs)", "Metal", "Broad-spectrum antimicrobial"],
    ["Zinc oxide (ZnO) NPs", "Metal oxide", "Antimicrobial, UV-blocking"],
    ["Titanium dioxide (TiO₂) NPs", "Metal oxide", "Photocatalytic antimicrobial, UV-blocking, ethylene oxidation"],
    ["Silicon dioxide (SiO₂) NPs", "Oxide", "Barrier, mechanical reinforcement, coatings"],
    ["Cellulose nanocrystals / nanofibres", "Bio-based", "Reinforcement and barrier in biopolymer films"],
    ["Chitosan nanoparticles", "Bio-based", "Antimicrobial, edible films"],
    ["Carbon nanotubes", "Carbon", "Sensors, conductivity, mechanical strength"],
    ["Titanium nitride (TiN) NPs", "Ceramic", "Processing aid in PET bottles (EU-authorised)"],
  ], 0.95, 1.55, 11.45, [3.6, 2.15, 5.7], 13);

  s = content("Types of Polymer–Clay Nanocomposites", "Nanomaterials & Fabrication");
  img(s, "structures.png", 1.15, 1.55, 11.0, 4.03);
  note(s, "Exfoliated structures give the largest gains in barrier and strength; phase-separated ones behave like conventional composites.", 1.2, 5.65, 10.95, 0.65, COL.mint, 15);

  s = content("Fabrication Methods", "Nanomaterials & Fabrication");
  const fab = [["Solution casting", "Polymer and nanofiller dispersed in solvent, cast and dried. Simple; common in labs."], ["Melt intercalation", "Filler mixed into molten polymer by extrusion. Solvent-free; preferred by industry."], ["In-situ polymerisation", "Monomer polymerises between clay layers, giving good exfoliation."], ["Electrospinning", "High voltage draws polymer solution into nanofibres (mats, active layers)."], ["Layer-by-layer assembly", "Alternating charged layers build ultra-thin, high-barrier coatings."], ["Nano-coating", "Thin layers (e.g. SiOₓ, AlOₓ) applied by vapour deposition or sol-gel."]];
  for (let i = 0; i < 6; i++) {
    const col = i % 3, row = Math.floor(i / 3);
    await card(s, 0.95 + col * 3.85, 1.6 + row * 2.4, 3.6, 2.2, fab[i][0], fab[i][1], i % 5, null, 14);
  }

  s = content("Spotlight: Electrospinning", "Nanomaterials & Fabrication");
  img(s, "electrospin.png", 0.95, 1.6, 7.0, 3.32);
  bullets(s, [
    "Polymer solution is pumped through a needle held at high voltage.",
    "Electric force overcomes surface tension → Taylor cone → thin, whipping jet.",
    "Solvent evaporates and nanofibres collect as a porous mat.",
    ["Used for:", "encapsulating essential oils, antioxidants and antimicrobials in active packaging layers."],
  ], 8.15, 1.6, 4.3, 4.75, 15);

  // ===== Section 04 =====
  pres.addSection({ title: "Applications" });
  sectionSlide("04", "APPLICATIONS", "Applications", ["d_box.png", 2.2, 2.2]);

  s = content("Three Ways Nanotech Is Applied", "Applications");
  await card(s, 0.95, 1.6, 3.6, 4.6, "Improved packaging", "Nanofillers improve the packaging material itself.\n\n• Gas & moisture barrier\n• Strength, stiffness\n• Heat & UV resistance\n• Lighter, thinner films", 0, "FaLayerGroup", 15);
  await card(s, 4.88, 1.6, 3.6, 4.6, "Active packaging", "Packaging that interacts with the food or headspace.\n\n• Antimicrobial surfaces\n• O₂ / ethylene scavengers\n• Moisture absorbers\n• Controlled release", 1, "FaFlask", 15);
  await card(s, 8.8, 1.6, 3.6, 4.6, "Intelligent packaging", "Packaging that monitors and communicates.\n\n• Nanosensors for spoilage\n• Freshness & TTI labels\n• Nano-barcodes, RFID\n• Anti-counterfeiting", 2, "FaMicrochip", 15);

  s = content("Improved Packaging: Barrier Properties", "Applications");
  bullets(s, [
    ["Oxygen barrier:", "slows lipid oxidation, rancidity, colour and vitamin loss."],
    ["CO₂ retention:", "keeps carbonation in beer and soft drinks in plastic bottles."],
    ["Water-vapour barrier:", "keeps snacks crisp and stops dry foods caking."],
    ["Aroma barrier:", "holds flavour in and keeps outside odours out."],
    ["Typical use:", "nanoclay–nylon or nanoclay–PET layers in multilayer films and bottles for meat, cheese, juices and beer."],
  ], 0.95, 1.6, 6.6, 4.8, 16);
  img(s, "tortuous.png", 7.75, 2.1, 4.7, 2.23);
  note(s, "Same tortuous-path principle, applied at scale.", 7.85, 4.55, 4.5, 0.5, COL.mint, 14);

  s = content("Improved Packaging: Mechanical, Thermal & UV", "Applications");
  await card(s, 0.95, 1.6, 3.6, 3.4, "Mechanical", "Higher tensile strength and stiffness allow down-gauging: thinner films, less plastic, same performance.", 0, "FaDumbbell", 15);
  await card(s, 4.88, 1.6, 3.6, 3.4, "Thermal", "Better heat resistance for hot-fill, retort and microwave packs; improved dimensional stability.", 2, "FaFire", 15);
  await card(s, 8.8, 1.6, 3.6, 3.4, "UV protection", "Nano-ZnO / TiO₂ block UV while staying clear, protecting riboflavin in milk and oils from photo-oxidation.", 1, "FaSun", 15);
  note(s, "Nanoclays can also improve flame retardancy of polymer packaging.", 0.95, 5.35, 11.45, 0.5, COL.mint, 15);

  s = content("Active Packaging: Antimicrobial", "Applications");
  bullets(s, [
    ["How it works:", "nano-Ag, ZnO, TiO₂ or chitosan NPs are embedded in films, coatings or container walls."],
    ["Two modes:", "release (ions or volatiles migrate to the food surface) or contact (surface kills microbes on touch)."],
    ["Targets:", "E. coli, Salmonella, Listeria, S. aureus, moulds and yeasts."],
    ["Benefit:", "slows surface spoilage, so less preservative is needed in the food."],
  ], 0.95, 1.6, 6.3, 4.8, 16);
  const foods = [["FaDrumstickBite", "Meat & poultry"], ["FaCheese", "Cheese"], ["FaBreadSlice", "Bread"], ["FaAppleAlt", "Fresh produce"]];
  for (let i = 0; i < 4; i++) {
    const col = i % 2, row = Math.floor(i / 2);
    const x = 7.65 + col * 2.4, y = 1.75 + row * 2.3;
    s.addShape(pres.shapes.OVAL, { x: x + 0.45, y, w: 1.3, h: 1.3, fill: { color: COL.card }, line: { color: ACC[i], width: 2 }, objectName: nm("foodCircle") });
    s.addImage({ data: await icon(foods[i][0], ACCHEX[i]), x: x + 0.78, y: y + 0.33, w: 0.64, h: 0.64, objectName: nm("foodIcon") });
    s.addText(foods[i][1], { x, y: y + 1.4, w: 2.2, h: 0.45, fontFace: FONT, fontSize: 15, color: COL.chalk, align: "center", margin: 0, isTextBox: true, objectName: nm("foodLabel") });
  }

  s = content("Active Packaging: Scavengers & Absorbers", "Applications");
  img(s, "scavenger.png", 0.95, 1.6, 5.9, 3.54);
  bullets(s, [
    ["Oxygen scavengers:", "nano-iron oxidises and binds O₂; nano-TiO₂ scavenges O₂ photocatalytically under UV."],
    ["Ethylene scavengers:", "nano-TiO₂ photocatalysis and Pd-based nanomaterials remove ethylene, delaying ripening."],
    ["Moisture absorbers:", "nanoclays and silica control humidity in the pack."],
    ["Large surface area", "of nanomaterials makes scavenging faster and more efficient."],
  ], 7.05, 1.6, 5.4, 4.8, 15);

  s = content("Active Packaging: Controlled Release", "Applications");
  bullets(s, [
    ["Nanoencapsulation:", "actives are trapped in nanoemulsions, nanoliposomes, cyclodextrins or electrospun fibres."],
    ["Antimicrobials:", "essential-oil compounds such as thymol, carvacrol and cinnamaldehyde."],
    ["Antioxidants:", "tocopherols, plant polyphenols, rosemary extract."],
    ["Slow release:", "keeps an effective dose at the food surface over storage, instead of one quick burst."],
    ["Also masks", "the strong odour and volatility of essential oils."],
  ], 0.95, 1.6, 7.0, 4.8, 16);
  await card(s, 8.2, 1.75, 4.2, 4.3, "Why encapsulate?", "• Protects actives from heat, light and O₂\n• Improves solubility in films\n• Controls release rate\n• Lower dose needed\n• Less effect on taste", 1, "FaVial", 15);

  s = content("Intelligent Packaging: Nanosensors", "Applications");
  img(s, "sensor.png", 0.95, 1.6, 7.2, 3.03);
  bullets(s, [
    "Detect spoilage gases (NH₃, amines, H₂S, CO₂), pH change or pathogens.",
    ["Gold NPs:", "change colour when they aggregate — easy to read."],
    ["Carbon nanotubes:", "change electrical resistance when exposed to gases."],
    ["Electronic nose / tongue:", "nanosensor arrays recognise odour or taste patterns."],
  ], 8.35, 1.6, 4.1, 4.8, 15);
  note(s, "Gives a real indication of freshness instead of relying only on the printed date.", 0.95, 4.95, 7.2, 0.6, COL.mint, 15);

  s = content("Intelligent Packaging: Indicators & Tracking", "Applications");
  const ind = [["FaThermometerHalf", "Time–temperature indicators", "Show cumulative heat exposure across the cold chain with a colour change."], ["FaTint", "Freshness indicators", "Respond to metabolites from spoilage, e.g. pH dyes reacting to amines in fish."], ["FaBarcode", "Nano-barcodes", "Nanoscale codes for traceability and brand authentication."], ["FaWifi", "RFID & printed electronics", "Nano-ink antennas allow wireless tracking through the supply chain."]];
  for (let i = 0; i < 4; i++) {
    const col = i % 2, row = Math.floor(i / 2);
    await card(s, 0.95 + col * 5.8, 1.6 + row * 2.4, 5.6, 2.2, ind[i][1], ind[i][2], i, ind[i][0], 15);
  }

  s = content("Bio-based Nanocomposites", "Applications");
  bullets(s, [
    ["Problem:", "biopolymers (PLA, starch, chitosan, gelatin, PHA) are eco-friendly but have weak barrier, low strength and high moisture sensitivity."],
    ["Solution:", "reinforce them with cellulose nanocrystals, nanoclay or chitosan NPs."],
    ["Results:", "better tensile strength, lower water-vapour permeability, improved heat stability."],
    ["Sustainability:", "compostable or biodegradable packs that can replace some petroleum plastics."],
  ], 0.95, 1.6, 7.0, 4.8, 16);
  await card(s, 8.2, 1.75, 4.2, 2.0, "Matrices", "PLA · Starch · Chitosan · Gelatin · PHA · Alginate", 0, "FaSeedling", 15);
  await card(s, 8.2, 4.0, 4.2, 2.0, "Nanofillers", "Cellulose nanocrystals · Nanoclay · ZnO · Chitosan NPs", 1, "FaCubes", 15);

  s = content("Edible Nano-coatings", "Applications");
  img(s, "coating.png", 0.95, 1.6, 5.6, 3.6);
  bullets(s, [
    "Thin, edible layers applied by dipping or spraying, mainly on fruits and vegetables.",
    ["Nanoemulsions", "carry essential oils or antioxidants evenly over the surface."],
    ["Nanolaminates", "(layer-by-layer) build very thin, multi-functional coatings."],
    ["Effects:", "lower respiration rate, less moisture loss, delayed browning and decay."],
  ], 6.8, 1.6, 5.65, 4.8, 16);

  s = content("Applications by Food Category", "Applications");
  table(s, [
    ["Food category", "Main problem", "Nano-solution"],
    ["Meat, poultry & seafood", "Microbial spoilage, oxidation", "AgNP/ZnO antimicrobial films, O₂ scavengers, amine sensors"],
    ["Dairy (milk, cheese)", "Light-induced oxidation, mould", "Nano-TiO₂/ZnO UV block, antimicrobial coatings"],
    ["Fruits & vegetables", "Ripening, moisture loss, decay", "Ethylene scavengers, edible nano-coatings"],
    ["Bakery", "Mould, staling", "Antimicrobial films, moisture control"],
    ["Beverages (beer, juice)", "O₂ entry, CO₂ loss", "Nanoclay barrier layers in PET bottles"],
    ["Snacks & dry foods", "Moisture uptake, rancidity", "High-barrier nanocomposite films, nano-coatings"],
  ], 0.95, 1.6, 11.45, [3.0, 3.35, 5.1], 14);

  s = content("Commercial & Reported Examples", "Applications");
  table(s, [
    ["Example", "Nanomaterial", "Purpose"],
    ["Nanoclay–nylon (polyamide) films", "Montmorillonite", "O₂ and moisture barrier for meat and cheese packs"],
    ["Multilayer PET beer & juice bottles", "Nanoclay barrier layer", "Keep O₂ out and CO₂ in"],
    ["PET bottles with TiN", "Titanium nitride NPs (~20 nm)", "Processing aid; EU-authorised with no migration allowed"],
    ["Antimicrobial food containers", "Silver nanoparticles", "Surface antimicrobial action"],
    ["SiOₓ / AlOₓ coated films", "Nanometre-thin oxide coatings", "Transparent high-barrier films"],
  ], 0.95, 1.6, 11.45, [3.8, 3.4, 4.25], 14, 4.1);
  note(s, "Product names and availability vary by country; regulatory approval differs between the EU, US and India.", 0.95, 5.95, 11.45, 0.45, COL.mint, 14);

  // ===== Section 05 =====
  pres.addSection({ title: "Safety & Regulation" });
  sectionSlide("05", "SAFETY & REGULATION", "Safety & Regulation", ["d_molecule.png", 2.4, 1.6]);

  s = content("Migration & Toxicity Concerns", "Safety & Regulation");
  img(s, "migration.png", 0.95, 1.6, 6.6, 3.21);
  bullets(s, [
    ["Migration:", "nanoparticles or their ions may move from package into food."],
    ["Health questions:", "accumulation in organs, ROS-driven cell damage, effects on gut microbiota."],
    ["Environment:", "release during disposal, recycling or composting."],
    ["Knowledge gaps:", "limited long-term data; nano-specific risk assessment is needed."],
  ], 7.75, 1.6, 4.7, 4.8, 15);

  s = content("Characterisation & Testing", "Safety & Regulation");
  table(s, [
    ["Test / technique", "What it tells us"],
    ["TEM / SEM", "Particle size, shape and dispersion in the film"],
    ["XRD", "Clay layer spacing → intercalated or exfoliated"],
    ["FTIR", "Chemical interactions between filler and polymer"],
    ["DSC / TGA", "Thermal transitions and stability"],
    ["OTR (e.g. ASTM D3985)", "Oxygen transmission rate"],
    ["WVTR (e.g. ASTM E96, F1249)", "Water-vapour transmission rate"],
    ["Migration test + ICP-MS / sp-ICP-MS", "Metal / nanoparticle release into food simulants"],
  ], 0.95, 1.6, 11.45, [4.4, 7.05], 14);

  s = content("Regulatory Framework", "Safety & Regulation");
  await card(s, 0.95, 1.6, 3.6, 4.35, "European Union", "• Reg. (EC) 1935/2004: framework for food-contact materials\n• Reg. (EU) 10/2011: nanoforms need specific authorisation\n• Reg. (EC) 450/2009: active & intelligent materials\n• EFSA guidance on nano risk assessment", 0, "FaGlobeAsia", 14);
  await card(s, 4.88, 1.6, 3.6, 4.35, "United States", "• FDA has no nano-specific packaging law\n• Case-by-case review under existing food-contact rules\n• 2014 FDA guidance on whether a product involves nanotechnology", 1, "FaGavel", 14);
  await card(s, 8.8, 1.6, 3.6, 4.35, "India", "• FSS (Packaging) Regulations, 2018 apply to all food packaging\n• Guidelines for Evaluation of Nano-based Agri-input and Food Products (2020), prepared by DBT with FSSAI and other ministries", 2, "FaCheckCircle", 14);
  note(s, "Example: EU lists TiN nanoparticles only for PET bottles, up to 20 mg/kg, with no migration permitted.", 0.95, 6.0, 11.45, 0.45, COL.mint, 14);

  // ===== Section 06 =====
  pres.addSection({ title: "Future & Conclusion" });
  sectionSlide("06", "FUTURE & CONCLUSION", "Future & Conclusion", ["d_np.png", 2.2, 2.2]);

  s = content("Challenges & Limitations", "Future & Conclusion");
  const ch = [["FaMoneyBillWave", "Cost", "Nanomaterials and processing add cost for low-margin foods."], ["FaIndustry", "Scale-up", "Lab-level dispersion is hard to repeat in industrial extrusion."], ["FaExclamationTriangle", "Safety data", "Migration and long-term toxicity are not fully understood."], ["FaUsers", "Consumer trust", "Low awareness and concern about “nano” in food."], ["FaRecycle", "Recycling", "Nanofillers may complicate existing plastic recycling streams."], ["FaSearch", "Detection & standards", "Measuring nanoparticles in food is difficult; methods are not harmonised."]];
  for (let i = 0; i < 6; i++) {
    const col = i % 3, row = Math.floor(i / 3);
    await card(s, 0.95 + col * 3.85, 1.6 + row * 2.4, 3.6, 2.2, ch[i][1], ch[i][2], (i + 3) % 5, ch[i][0], 14);
  }

  s = content("Future Trends", "Future & Conclusion");
  bullets(s, [
    ["Green synthesis:", "nanoparticles made with plant extracts and microbes instead of harsh chemicals."],
    ["Fully biodegradable nanocomposites", "from agri-waste cellulose, starch and chitosan."],
    ["Smart + connected packs:", "sensors linked to smartphones, IoT and blockchain traceability."],
    ["Printed electronics", "and low-cost nano-inks for RFID and freshness labels."],
    ["Safer-by-design nanomaterials", "with low migration and clear standard test methods."],
    ["Harmonised regulation", "and clear labelling to build consumer trust."],
  ], 0.95, 1.6, 7.6, 4.8, 16);
  img(s, "d_box.png", 9.0, 1.9, 3.0, 3.0);
  note(s, "Packaging that protects, informs and degrades.", 8.75, 5.1, 3.5, 0.8, COL.yel, 16);

  s = content("Conclusion", "Future & Conclusion");
  const concl = ["Nanotechnology works at 1–100 nm, where materials gain new properties.", "Key principles: high surface area, tortuous-path barrier, antimicrobial action and size-dependent effects.", "Applications span improved, active and intelligent packaging, plus bio-nanocomposites and edible coatings.", "It extends shelf life, improves safety and can reduce food and plastic waste.", "Safe use needs migration testing, sound risk assessment and clear regulation."];
  for (let i = 0; i < 5; i++) {
    const y = 1.6 + i * 0.95;
    s.addShape(pres.shapes.OVAL, { x: 0.95, y: y + 0.05, w: 0.6, h: 0.6, fill: { type: "none" }, line: { color: ACC[i], width: 2 }, objectName: nm("cNum") });
    s.addText(String(i + 1), { x: 0.95, y: y + 0.05, w: 0.6, h: 0.6, fontFace: FONT, fontSize: 18, bold: true, color: ACC[i], align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: nm("cNumT") });
    s.addText(concl[i], { x: 1.75, y, w: 10.6, h: 0.7, fontFace: FONT, fontSize: 17, color: COL.chalk, valign: "middle", margin: 0, isTextBox: true, objectName: nm("cText") });
  }

  s = content("Video Resources", "Future & Conclusion");
  s.addText(VIDEOS.map((v, i, a) => ({ text: `Slide ${v[0]}  ·  ${v[1]}  (${v[2]}, ${v[3]})`, options: { hyperlink: { url: yt(v[4]), tooltip: "Open on YouTube" }, color: i % 2 ? COL.mint : COL.yel, breakLine: i < a.length - 1, paraSpaceAfter: 9 } })),
    { x: 1.2, y: 1.55, w: 11.0, h: 4.6, fontFace: FONT, fontSize: 18, valign: "top", margin: 0, isTextBox: true, objectName: "videoList" });
  note(s, "Click any line to open the video on YouTube (internet connection needed during the class).", 1.2, 6.0, 11.0, 0.45, COL.chalk, 14);

  s = content("References", "Future & Conclusion");
  s.addText([
    "Duncan, T.V. (2011). Applications of nanotechnology in food packaging and food safety: barrier materials, antimicrobials and sensors. J. Colloid Interface Sci., 363(1), 1–24.",
    "Sozer, N. & Kokini, J.L. (2009). Nanotechnology and its applications in the food sector. Trends Biotechnol., 27(2), 82–89.",
    "Rhim, J.W., Park, H.M. & Ha, C.S. (2013). Bio-nanocomposites for food packaging applications. Prog. Polym. Sci., 38(10–11), 1629–1652.",
    "Silvestre, C., Duraccio, D. & Cimmino, S. (2011). Food packaging based on polymer nanomaterials. Prog. Polym. Sci., 36(12), 1766–1782.",
    "Nielsen, L.E. (1967). Models for the permeability of filled polymer systems. J. Macromol. Sci. A, 1(5), 929–942.",
    "EFSA Scientific Committee (2018, updated 2021). Guidance on risk assessment of nanoscience and nanotechnology applications in the food and feed chain. EFSA Journal.",
    "Commission Regulation (EU) No 10/2011 on plastic materials and articles intended to come into contact with food.",
    "Dept. of Biotechnology, Govt. of India (2020). Guidelines for Evaluation of Nano-based Agri-input and Food Products in India.",
  ].map((t, i, a) => ({ text: t, options: { bullet: { type: "number" }, breakLine: i < a.length - 1, paraSpaceAfter: 5 } })),
    { x: 0.95, y: 1.5, w: 11.45, h: 4.85, fontFace: FONT, fontSize: 13, color: COL.chalk, valign: "top", margin: 2, isTextBox: true, objectName: "refs" });

  s = pres.addSlide({ masterName: "CHALK_BLANK", sectionTitle: "Future & Conclusion" });
  s.addText("Thank You!", { x: 2.4, y: 1.7, w: 8.53, h: 1.8, fontFace: FONT, fontSize: 72, bold: true, color: COL.yel, align: "center", valign: "middle", isTextBox: true, objectName: "thanks" });
  s.addText("Questions & Discussion", { x: 2.4, y: 3.55, w: 8.53, h: 0.7, fontFace: FONT, fontSize: 26, italic: true, color: COL.mint, align: "center", isTextBox: true, objectName: "qna" });
  img(s, "d_np.png", 0.9, 3.9, 2.0, 2.0);
  img(s, "d_leaf.png", 10.7, 3.7, 1.7, 2.04);
  img(s, "d_squiggle.png", 5.4, 4.6, 2.5, 1.0);

  for (const v of VIDEOS) {
    const sl = pres._slides[v[0] - 1];
    sl.addText([{ text: `►  Watch: ${v[1]} (${v[3]})`, options: { hyperlink: { url: yt(v[4]), tooltip: "Open on YouTube" }, color: COL.board, bold: true } }],
      { shape: pres.shapes.ROUNDED_RECTANGLE, rectRadius: 0.18, x: 0.95, y: 6.27, w: 6.6, h: 0.38, fill: { color: COL.cor }, line: { color: COL.cor }, fontFace: FONT, fontSize: 13, align: "left", valign: "middle", margin: [0, 10, 0, 10], objectName: nm("videoBtn") });
  }

  await pres.writeFile({ fileName: "Nanotechnology_in_Food_Packaging.pptx" });
  await applyTheme("Nanotechnology_in_Food_Packaging.pptx", THEME);
  console.log("written");
})();
