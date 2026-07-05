# Typst slide theme

A minimal slide theme in plain Typst, no external package.

```
#import "try-works.typ": *
#show: try-works

#title-slide(title: "Try-Works", subtitle: "An identity in two modes")
#slide(title: "The rule")[The sea is the field; the fire is the mark.]
```

Compile the demo:

```
typst compile demo.typ demo.pdf
```

Fraunces, Archivo, and JetBrains Mono must be installed on the system so Typst
can find them. See `../fonts/README.md`.
