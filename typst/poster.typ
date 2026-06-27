// Generated from try-works.json. Try-Works poster preset (Typst).
// Colours below are screen sRGB; substitute the CMYK in print/SPEC.md at output.

#let tw = (
  pitch: rgb("#12161b"), whale: rgb("#f1efe9"),
  ember: rgb("#c9651d"), flame: rgb("#e0832a"),
  seadeep: rgb("#14242c"), sea: rgb("#2c4953"),
  paper: rgb("#dee7e4"), ink: rgb("#18272b"),
)

// poster(trim, bleed, safe, fill, body): page = trim + 2*bleed, with crop marks
// (top-left and bottom-right shown) and a non-printing safe-area guide.
#let poster(trim: (420mm, 594mm), bleed: 3mm, safe: 5mm, fill: tw.seadeep, body) = {
  set page(width: trim.at(0) + 2*bleed, height: trim.at(1) + 2*bleed, margin: 0pt, fill: fill)
  let m = 4mm
  place(top + left, dx: bleed, dy: 0mm, line(end: (0mm, m), stroke: 0.25pt + tw.whale))
  place(top + left, dx: 0mm, dy: bleed, line(end: (m, 0mm), stroke: 0.25pt + tw.whale))
  place(bottom + right, dx: -bleed, dy: 0mm, line(end: (0mm, -m), stroke: 0.25pt + tw.whale))
  place(bottom + right, dx: 0mm, dy: -bleed, line(end: (-m, 0mm), stroke: 0.25pt + tw.whale))
  place(top + left, dx: bleed + safe, dy: bleed + safe,
    rect(width: trim.at(0) - 2*safe, height: trim.at(1) - 2*safe,
      stroke: (paint: tw.ember, thickness: 0.25pt, dash: "dotted")))
  place(top + left, dx: bleed, dy: bleed,
    block(width: trim.at(0), height: trim.at(1), inset: safe + 10mm, body))
}

// Demo: the fire as the one hot mark on a cold field.
#poster(fill: tw.seadeep)[
  #set text(fill: tw.whale, font: "Fraunces")
  #text(size: 13pt, fill: tw.flame, font: "JetBrains Mono", tracking: 3pt)[A MOBY-DICK DESIGN SYSTEM]
  #v(1fr)
  #text(size: 110pt, weight: 600)[Try-Works]
  #v(6mm)
  #text(size: 22pt)[Look not too long in the face of the fire.]
]
