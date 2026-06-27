# Try-Works - print specification

Generated from try-works.json. These CMYK values are uncalibrated starting points from a naive separation. Proof against a physical swatch before a print run; the printer's RIP and ICC profile are authoritative.

## Colour management
Profile: PSO Coated v3 (FOGRA51) for coated stock; FOGRA39 where v3 is unavailable.
Ink limit: 300% total area coverage (FOGRA51). Keep the dark sea and rich black under it.

## Rich black
C70 M50 Y40 K100. Cool rich black that reads like pitch. Use plain K for text below ~24 pt to avoid registration fringing.

## CMYK starting values
| token | CMYK |
| --- | --- |
| pitch | C33 M19 Y0 K89 |
| whale | C0 M1 Y3 K5 |
| ember | C0 M50 Y86 K21 |
| flame | C0 M42 Y81 K12 |
| oil | C0 M52 Y86 K40 |
| sea-deep | C55 M18 Y0 K83 |
| sea | C47 M12 Y0 K67 |
| sea-bright | C40 M8 Y0 K50 |
| sea-pale | C24 M4 Y0 K26 |
| paper | C4 M0 Y1 K9 |
| ink | C44 M9 Y0 K83 |
| cold-accent | C0 M49 Y85 K38 |

## Gamut risks
These desaturate in process; proof them or run as spot: sea-bright, sea-pale, data-viz blue #0072B2, data-viz green #009E73, data-viz violet #CC79A7.

If the brand fire must match exactly, run it as a burnt-orange spot (Pantone 1595 C region) and confirm on a swatch book. The amber otherwise reproduces well in process.

## Geometry
Bleed: 3 mm. Safe margin: 5 mm from trim.

- A3: 297x420 mm (trim)
- A2: 420x594 mm (trim)
- A1: 594x841 mm (trim)
- A0: 841x1189 mm (trim)
