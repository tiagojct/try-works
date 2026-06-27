# Try-Works — product notes

## Who it is for
An audience of roughly one, honestly: an academic-maker who ships websites,
slides, posters, code, and statistical plots, in R and Python and Quarto and
Typst and 11ty, with a Moby-Dick aesthetic. Others may adopt it, but the design
target is that workflow. Naming the user this plainly changes the scope rule: a
surface earns its place only if it is used in that workflow, or clearly will be.
Everything else is maintenance debt wearing a feature's clothes.

## The weekly-use test
From the foundations, after Illich: keep what is touched often and convivial;
question what sits idle. Best inference from the actual workflow:

Core, touched weekly, keep and polish:
- R ggplot2 scales and theme, and Python matplotlib. The modelling work is
  constant; these are the highest-value surfaces.
- Typst slide theme. Decks are frequent.
- The CSS layer and the 11ty web starter, for the personal site.
- The VS Code / Positron theme, since the editor is open daily.

Maintained, occasional but high-value when needed, keep but do not gold-plate:
- Typst poster preset and the print spec. Posters are rare; the value per use is
  high.

Also core, now confirmed in use:
- Tailwind preset, the Obsidian theme, and the Ghostty terminal theme. These are
  in the daily workflow, so they stay first-class and tested alongside the rest.

With every surface confirmed, nothing is pruned. The scope discipline shifts
from cutting to holding the line: no new surfaces beyond the one gap below.

## The gap that outranks anything here
Quarto. Documents, papers, and much of the site run through Quarto, and the
system has no Quarto theme: no brand SCSS for HTML output, no Typst format for
PDF. That is the single highest-value thing to build next, ahead of any further
polish on surfaces above, because it sits in the weekly path and is missing.

## Scope line
Stop adding surfaces. The token core is complete and well-tested. The next move
is the Quarto theme. After that, 1.0: freeze the public surface and commit to
the versioning policy.
