# Try-Works (True Lamp) -- oh-my-zsh theme. Generated from try-works.json.
# Light.
# Truecolor prompt (needs zsh >= 5.7). Cool sea is the field; the ember
# fire marks only uncommitted work; a red caret/code means the last command failed.

ZSH_THEME_GIT_PROMPT_PREFIX=" %F{#52646a}(%F{#3f656b}"
ZSH_THEME_GIT_PROMPT_SUFFIX="%F{#52646a})%f"
ZSH_THEME_GIT_PROMPT_DIRTY="%F{#9e5017}*"
ZSH_THEME_GIT_PROMPT_CLEAN=""

PROMPT='%F{#3d6b76}%~%f$(git_prompt_info)
%(?.%F{#3d6b76}.%F{#7d4c40})❯%f '
RPROMPT='%(?..%F{#7d4c40}%?%f)'
