" Work variant specific configuration for Neovim

" Work-specific settings
set expandtab
set tabstop=2
set shiftwidth=2
set softtabstop=2

" Enable line numbers always in work mode
set number
set relativenumber

" Highlight current line
set cursorline

" Color scheme preference for work environment
if has('termguicolors')
  set termguicolors
endif

if has('nvim-0.5')
  try
    colorscheme tokyonight-storm
  catch
    colorscheme default
  endtry
endif

" Git integration for work
if exists('g:loaded_fugitive')
  nnoremap <leader>gs :Git<CR>
  nnoremap <leader>gd :Gdiff<CR>
  nnoremap <leader>gc :Git commit<CR>
  nnoremap <leader>gb :Git blame<CR>
  nnoremap <leader>gl :Gclog<CR>
endif

" Code formatting tools often used at work
augroup WorkFormatting
  autocmd!
  autocmd BufWritePre *.js,*.jsx,*.ts,*.tsx,*.css,*.scss,*.json,*.md,*.yaml,*.html :silent! lua vim.lsp.buf.format()
augroup END


" Load work-specific local configuration if available
if filereadable(expand("~/.config/nvim/work.local.vim"))
  source ~/.config/nvim/work.local.vim
endif
