# Generated from try-works.json - do not edit by hand.
# Try-Works: ggplot2 scales and theme. Source the file, then add the scales/theme to a plot.

tryworks_categorical <- c("#E69F00", "#0072B2", "#009E73", "#CC79A7", "#D55E00", "#56B4E9", "#F0E442")
tryworks_sequential  <- c("#e4f5fb", "#b3e0ee", "#7ec4d7", "#48a0b7", "#0a7b93", "#00576c", "#003542")
tryworks_diverging   <- c("#00576e", "#287d93", "#72a9b4", "#bbd7d9", "#f1eee6", "#e7ccae", "#da9b6a", "#c26d32", "#984a1a")
tryworks_shapes      <- c(16, 15, 17, 18, 25, 3, 4)

.tryworks_plot <- list(
  light = list(bg="#ffffff", panel="#ffffff", text="#18272b", grid="#dce5e1", muted="#52646a"),
  dark  = list(bg="#12161b", panel="#12161b", text="#f1efe9", grid="#2c3640", muted="#97a0a4")
)

tryworks_pal_d <- function(n) {
  if (n > length(tryworks_categorical))
    warning("Try-Works categorical has ", length(tryworks_categorical), " colours; ", n, " requested.")
  unname(tryworks_categorical[seq_len(n)])
}

scale_colour_tryworks_d   <- function(...) ggplot2::discrete_scale("colour", "tryworks", tryworks_pal_d, ...)
scale_fill_tryworks_d     <- function(...) ggplot2::discrete_scale("fill", "tryworks", tryworks_pal_d, ...)
scale_colour_tryworks_c   <- function(...) ggplot2::scale_colour_gradientn(colours = tryworks_sequential, ...)
scale_fill_tryworks_c     <- function(...) ggplot2::scale_fill_gradientn(colours = tryworks_sequential, ...)
scale_colour_tryworks_div <- function(...) ggplot2::scale_colour_gradientn(colours = tryworks_diverging, ...)
scale_fill_tryworks_div   <- function(...) ggplot2::scale_fill_gradientn(colours = tryworks_diverging, ...)
scale_color_tryworks_d    <- scale_colour_tryworks_d
scale_color_tryworks_c    <- scale_colour_tryworks_c
scale_color_tryworks_div  <- scale_colour_tryworks_div
scale_shape_tryworks_d    <- function(...) ggplot2::scale_shape_manual(values = tryworks_shapes, ...)

theme_tryworks <- function(base_size = 12, base_family = "Archivo", mode = c("light", "dark")) {
  mode <- match.arg(mode); p <- .tryworks_plot[[mode]]
  ggplot2::theme_minimal(base_size = base_size, base_family = base_family) +
    ggplot2::theme(
      plot.background  = ggplot2::element_rect(fill = p$bg, colour = NA),
      panel.background = ggplot2::element_rect(fill = p$panel, colour = NA),
      panel.grid.major = ggplot2::element_line(colour = p$grid, linewidth = 0.3),
      panel.grid.minor = ggplot2::element_blank(),
      axis.text   = ggplot2::element_text(colour = p$muted),
      axis.title  = ggplot2::element_text(colour = p$text),
      plot.title  = ggplot2::element_text(colour = p$text, family = "Fraunces"),
      plot.subtitle = ggplot2::element_text(colour = p$muted),
      legend.text  = ggplot2::element_text(colour = p$text),
      legend.title = ggplot2::element_text(colour = p$text)
    )
}
