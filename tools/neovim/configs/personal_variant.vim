" Personal variant specific configuration for Neovim

" Personal settings
set expandtab
set tabstop=4
set shiftwidth=4
set softtabstop=4

" Enable line numbers
set number
set relativenumber

" Highlight current line
set cursorline

" Color scheme preference for personal environment
if has('termguicolors')
  set termguicolors
endif

if has('nvim-0.5')
  try
    colorscheme tokyonight-night
  catch
    colorscheme default
  endtry
endif

" Additional personal key mappings
nnoremap <leader>pi :PlugInstall<CR>
nnoremap <leader>pu :PlugUpdate<CR>

" Personal writing environment settings
augroup personal_writing
  autocmd!
  autocmd FileType markdown,text setlocal spell spelllang=en_us
  autocmd FileType markdown,text setlocal wrap
  autocmd FileType markdown,text setlocal linebreak
  autocmd FileType markdown,text setlocal textwidth=80
  autocmd FileType markdown,text setlocal conceallevel=2
augroup END

" Personal abbreviations
iabbrev @@ your.personal.email@example.com
iabbrev sig -- <cr>Your Name<cr>your.personal.email@example.com

" Load personal-specific local configuration if available
if filereadable(expand("~/.config/nvim/personal.local.vim"))
  source ~/.config/nvim/personal.local.vim
endif