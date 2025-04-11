" Linux-specific Neovim settings

" Linux clipboard integration (requires xclip or wl-copy)
if executable('xclip')
  set clipboard=unnamedplus
elseif executable('wl-copy') && executable('wl-paste')
  set clipboard=unnamedplus
endif

" Font settings for GUI Neovim
if exists('g:neovide')
  set guifont=JetBrainsMono\ Nerd\ Font:h12
endif

" Support for system commands
set shell=/bin/bash

" External commands
if executable('rg')
  set grepprg=rg\ --vimgrep\ --smart-case\ --follow
endif

" Path settings for Linux
set path+=/usr/include/,/usr/local/include/

" Terminal improvements
if &term =~ '256color'
  " Enable true color support
  let &t_8f = "\<Esc>[38;2;%lu;%lu;%lum"
  let &t_8b = "\<Esc>[48;2;%lu;%lu;%lum"
endif

" Fix common issues with different terminals
if &term =~ '^xterm'
  " Make shift-insert work
  map <S-Insert> <MiddleMouse>
  map! <S-Insert> <MiddleMouse>
endif