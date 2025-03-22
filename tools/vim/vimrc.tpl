" Basic Vim Configuration
" {{generated_notice}}

syntax on
set number
set ruler
set tabstop={{tab_size}}
set shiftwidth={{tab_size}}
set expandtab
set smartindent
set autoindent
set incsearch
set hlsearch
set ignorecase
set smartcase
set backup
set backupdir=~/.vim/backup
set directory=~/.vim/swap
set undofile
set undodir=~/.vim/undo
set colorcolumn={{column_width}}
set background={{background_color}}

" Create required directories
if !isdirectory($HOME . "/.vim/backup")
    call mkdir($HOME . "/.vim/backup", "p")
endif
if !isdirectory($HOME . "/.vim/swap")
    call mkdir($HOME . "/.vim/swap", "p")
endif
if !isdirectory($HOME . "/.vim/undo")
    call mkdir($HOME . "/.vim/undo", "p")
endif

" Platform-specific settings
{{platform_specific_settings}}

" Include local configuration
if filereadable(expand("~/.vimrc.local"))
    source ~/.vimrc.local
endif