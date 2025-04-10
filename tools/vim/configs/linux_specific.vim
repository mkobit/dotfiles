" Linux-specific Vim configuration

" Use X11 clipboard when available
if has('unnamedplus')
    set clipboard=unnamedplus
endif

" Linux terminal specific settings
if !has('gui_running')
    set t_Co=256
endif

" Handle Linux paths
set wildignore+=*/tmp/*,*/var/tmp/*,*/.git/*,*/node_modules/*

" Fix for common terminal issues on Linux
set ttymouse=xterm2
set mouse=a