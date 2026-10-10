if [[ $- == *i* ]]; then
    source "{{ .chezmoi.destDir }}/.dotfiles/bash/config.bash"
fi
