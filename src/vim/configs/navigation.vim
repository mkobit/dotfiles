""" Enable relative line numbers with current line showing absolute number
""" This makes it easier to use relative motions (e.g., 5j, 3k)
set number
set relativenumber

""" Keep a minimum number of lines visible above/below cursor
""" Prevents cursor from getting too close to screen edges
set scrolloff=5
set sidescrolloff=10

""" Make j and k navigate display lines rather than physical lines
""" More intuitive when working with wrapped text
nnoremap j gj
nnoremap k gk

""" Simple window navigation (won't conflict with tmux if using C-a prefix)
""" Use Alt+hjkl to move between splits
nnoremap <M-h> <C-w>h
nnoremap <M-j> <C-w>j
nnoremap <M-k> <C-w>k
nnoremap <M-l> <C-w>l

""" Basic buffer navigation
""" Simple commands to switch between buffers
nnoremap <Leader>bn :bnext<CR>
nnoremap <Leader>bp :bprevious<CR>
nnoremap <Leader>bd :bdelete<CR>

""" Center screen when jumping to search results
""" Keeps context around search matches
nnoremap n nzz
nnoremap N Nzz

""" Remember last location in file
""" Return to last edit position when opening files
augroup remember_position
  autocmd!
  autocmd BufReadPost *
    \ if line("'\"") > 1 && line("'\"") <= line("$") |
    \   exe "normal! g`\"" |
    \ endif
augroup END
