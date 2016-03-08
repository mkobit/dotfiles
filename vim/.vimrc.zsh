" " Colors
" enable syntax processing
syntax enable

" Use case insensitive search, except when using capital letters

" Allow backspacing over autoindent, line breaks and start of insert action
set backspace=indent,eol,start
  
set autoindent

filetype plugin on

" " Spaces and Tabs 
" number of visual spaces per TAB
set tabstop=4
" number of spaces in tab when editing
set softtabstop=4
" tabs are spaces
set expandtab


" " UI Config
" show line numbers
set number
" show command in bottom bar
set showcmd
set ruler
set laststatus=2
" highlight current line
set cursorline
" highlight matching brackets, braces, and parenthesis
set showmatch
" visual autocomplete for command menu
set wildmenu

" " Search
" search as characters are entered
set incsearch
" highlight matches
set hlsearch
set ignorecase
set smartcase

" " Movement
" move vertically by visual line
nnoremap j gj
nnoremap k gk

