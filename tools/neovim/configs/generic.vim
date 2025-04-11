" Generic platform Neovim settings
" Used as a fallback when the specific platform cannot be detected

" Basic clipboard settings that work on most systems
set clipboard=unnamed,unnamedplus

" Font settings for most GUI Neovim instances
if exists('g:neovide') || exists('g:gui_vimr') || exists('g:fvim_loaded')
  set guifont=monospace:h12
endif

" Support for system commands - use a shell that's likely to be available
if executable('bash')
  set shell=bash
elseif executable('zsh')
  set shell=zsh
endif

" External commands that might be available
if executable('rg')
  set grepprg=rg\ --vimgrep\ --smart-case\ --follow
elseif executable('grep')
  set grepprg=grep\ -n
endif

" Universal file handling settings
set fileformats=unix,dos,mac
set encoding=utf-8
set fileencoding=utf-8

" Reasonable defaults for file backup locations
set backupdir=~/.local/share/nvim/backup//
set directory=~/.local/share/nvim/swap//
set undodir=~/.local/share/nvim/undo//

" Create directories if they don't exist
if !isdirectory(&backupdir)
  call mkdir(&backupdir, "p")
endif
if !isdirectory(&directory)
  call mkdir(&directory, "p")
endif
if !isdirectory(&undodir)
  call mkdir(&undodir, "p")
endif

" Universal keymappings that work across platforms
nnoremap <C-s> :write<CR>
inoremap <C-s> <Esc>:write<CR>a