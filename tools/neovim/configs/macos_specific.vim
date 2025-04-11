" macOS-specific Neovim settings

" macOS clipboard integration
set clipboard=unnamed

" Font settings for GUI Neovim
if exists('g:neovide')
  set guifont=JetBrainsMono\ Nerd\ Font:h14
endif

" Support for system commands
set shell=/bin/zsh

" External commands
if executable('rg')
  set grepprg=rg\ --vimgrep\ --smart-case\ --follow
endif

" macOS key bindings
nnoremap <D-s> :write<CR>
nnoremap <D-v> "+p
inoremap <D-v> <C-r>+
vnoremap <D-c> "+y

" macOS GUI settings for Neovim-Qt or VimR
if exists('g:gui_vimr') || exists('g:neovide')
  set mousemodel=popup
endif