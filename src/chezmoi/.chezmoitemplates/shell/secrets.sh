if [ -f {{ .chezmoi.destDir }}/.config/shell/secrets.sh ]; then
  source {{ .chezmoi.destDir }}/.config/shell/secrets.sh
fi
