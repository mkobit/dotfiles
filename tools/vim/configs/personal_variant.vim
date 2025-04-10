" Personal environment specific Vim configuration

" Personal-specific settings
autocmd BufNewFile,BufRead */personal/* setlocal tabstop=4 shiftwidth=4

" Personal color scheme preference
if has('syntax') && (&t_Co > 2 || has('gui_running'))
    colorscheme darkblue
endif

" Personal-specific mappings
nnoremap <leader>j :e ~/personal/journal.md<CR>
nnoremap <leader>n :e ~/personal/notes/index.md<CR>
nnoremap <leader>b :e ~/personal/blog/ideas.md<CR>

" Personal-specific plugins would be loaded here
" if filereadable(expand("~/.vim/personal_plugins.vim"))
"     source ~/.vim/personal_plugins.vim
" endif

" Personal-specific abbreviations
iabbrev @p personal@example.com
iabbrev sig --<CR>Your Name<CR>Personal Website