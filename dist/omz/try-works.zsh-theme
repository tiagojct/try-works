# Try-Works (Try-Fire) -- oh-my-zsh theme. Generated from try-works.json.
# Dark.
# Truecolor prompt (needs zsh >= 5.7). Cool sea is the field; the ember
# fire marks only uncommitted work; a red caret/code means the last command failed.

ZSH_THEME_GIT_PROMPT_PREFIX=" %F{#4d7680}(%F{#5f97a0}"
ZSH_THEME_GIT_PROMPT_SUFFIX="%F{#4d7680})%f"
ZSH_THEME_GIT_PROMPT_DIRTY="%F{#c9651d}*"
ZSH_THEME_GIT_PROMPT_CLEAN=""

PROMPT='%F{#8fb6bd}%~%f$(git_prompt_info)
%(?.%F{#4d7680}.%F{#d06a52})❯%f '
RPROMPT='%(?..%F{#d06a52}%?%f)'
