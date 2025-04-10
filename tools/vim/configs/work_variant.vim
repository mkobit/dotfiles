" Work environment specific Vim configuration

" Work-specific settings
autocmd BufNewFile,BufRead */work/* setlocal tabstop=2 shiftwidth=2

" Work color scheme
if has('syntax') && (&t_Co > 2 || has('gui_running'))
    colorscheme blue
endif

" Work-specific mappings
nnoremap <leader>j :e ~/work/journal.md<CR>
nnoremap <leader>t :e ~/work/todo.md<CR>
nnoremap <leader>p :e ~/work/projects.md<CR>

" Work-specific plugins would be loaded here
" if filereadable(expand("~/.vim/work_plugins.vim"))
"     source ~/.vim/work_plugins.vim
" endif

" Work-specific abbreviations
iabbrev @w work@example.com
iabbrev sig --<CR>Your Name<CR>Work Title<CR>Company Name