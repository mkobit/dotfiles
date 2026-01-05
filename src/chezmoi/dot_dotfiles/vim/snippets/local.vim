" Load local settings if available
if filereadable(expand("~/.vimrc.local"))
  source ~/.vimrc.local
endif