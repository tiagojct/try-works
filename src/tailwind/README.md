# try-works-tailwind

The Try-Works system as a Tailwind preset: colours, font sizes, spacing, radii.

```js
// tailwind.config.js
const tw = require("try-works-tailwind");
module.exports = {
  theme: {
    extend: {
      colors: tw.colors,
      fontSize: tw.fontSize,
      spacing: tw.spacing,
      borderRadius: tw.borderRadius,
    },
  },
};
```

```html
<h1 class="text-poster text-whale">Loomings</h1>
<p class="text-fire">one hot mark</p>
<section class="bg-sea-deep text-whale p-8">…</section>
```

Colour names: `fire` (ember default, flame, oil), `sea` (swell default, deep,
bright, pale), `whale`, `bone`, `gull`, `pitch`, `hold`, `deck`, `iron`, and the
code-tier `kelp`, `brick`, `dusk`, `tide`, `shoal`. For both modes via
`data-mode`, use the CSS custom properties in `css/try-works.css`.
