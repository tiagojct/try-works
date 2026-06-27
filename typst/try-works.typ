// Try-Works — a Typst slide theme. Colours are generated into colors.typ.
#import "colors.typ": *

#let try-works(body) = {
  set page(paper: "presentation-16-9", margin: 0pt, fill: sea-deep)
  set text(font: "Archivo", fill: whale, size: 24pt)
  show heading: set text(font: "Fraunces")
  body
}
#let title-slide(title: "", subtitle: "") = {
  page(fill: sea-deep)[
    #place(bottom + left, dx: 3cm, dy: -3cm)[
      #text(font: "Fraunces", size: 72pt, weight: 600, fill: whale)[#title]
      #v(0.3em)
      #text(font: "JetBrains Mono", size: 15pt, fill: ember, tracking: 3pt)[#upper(subtitle)]
    ]
  ]
}
#let slide(title: "", body) = {
  page(fill: pitch, margin: (x: 3cm, y: 2.4cm))[
    #text(font: "JetBrains Mono", size: 13pt, fill: ember, tracking: 2pt)[#upper(title)]
    #v(0.5em); #line(length: 100%, stroke: 0.5pt + gull); #v(1em)
    #set text(fill: whale); #body
  ]
}
