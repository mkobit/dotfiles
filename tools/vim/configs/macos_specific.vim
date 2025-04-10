" macOS-specific Vim configuration

" Use macOS clipboard
set clipboard=unnamed

" macOS specific key mappings
nnoremap <D-s> :w<CR>
nnoremap <D-v> "+p
vnoremap <D-c> "+y
inoremap <D-v> <C-r>+

" Fix Alt key issues in macOS Terminal
if !has('gui_running')
    let c='a'
    while c <= 'z'
        exec "set <A-".c.">=\e".c
        exec "imap \e".c." <A-".c.">"
        let c = nr2char(1+char2nr(c))
    endw
    set ttimeout ttimeoutlen=50
endif

" Handle macOS file paths
set wildignore+=*/Applications/*,*/Library/*,*/.DS_Store