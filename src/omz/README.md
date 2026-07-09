# Try-Works for oh-my-zsh

A two-line prompt in the Try-Works palette: **Try-Fire** (`try-works.zsh-theme`,
dark) and **True Lamp** (`try-works-cold.zsh-theme`, light). Truecolor, so the
brand hues render exactly in any terminal; pairs with the Try-Works terminal
preset (Ghostty / iTerm).

The whole prompt is cool sea; the ember fire lights in one place only, the
git-dirty mark (`*`). A failed command turns the caret and the exit code red.
Line one is the working directory and git branch; line two is the caret.

Generated from `try-works.json`; edit the json and run `make generate`, never
the theme file.

## Install

Copy a theme into oh-my-zsh's custom themes directory and select it in `~/.zshrc`:

    cp try-works.zsh-theme "${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/themes/"
    # then in ~/.zshrc:
    ZSH_THEME="try-works"

Use `try-works-cold` instead for the light terminal. Needs zsh 5.7+ for
truecolor prompt escapes (macOS ships 5.9). Git segment uses oh-my-zsh's own
`git_prompt_info`, so no extra plugin is required.
