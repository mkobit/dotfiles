"""""""""""""""""""""""""""""""""""""""
" => General
"""""""""""""""""""""""""""""""""""""""
" Amount of lines of history for VIM to remember
set history=4000

" Enable filetype plugins
filetype plugin on
filetype indent on

" Auto read when a file is changed from the outside
set autoread
autocmd FocusGained,BufEnter * checktime

" Set utf8 as standard encoding
set encoding=utf8

" No annoying sound on errors
set noerrorbells
set novisualbell
set t_vb=
set timeoutlen=750

" Use Unix as the standard file type
set fileformats=unix,dos,mac

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" => UI
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
let $LANG='en'
set langmenu=en
source $VIMRUNTIME/delmenu.vim
source $VIMRUNTIME/menu.vim

" Turn on the Wild menu
set wildmenu

" Set lines to show above and below the cursor
set scrolloff=5

" show absolute line number for current line, and relative for other lines
set number
set relativenumber

" show command in bottom bar
set showcmd

set ruler

" highlight current line
set cursorline
" highlight matching brackets, braces, and parenthesis
set showmatch
" Height of the command bar
set cmdheight=1
" A buffer becomes hidden when it is abandoned
set hid

" Configure backspace so it acts as it should act
set backspace=eol,start,indent

set whichwrap+=<,>,h,l

" Don't redraw while executing macros (good performance config)
set lazyredraw

" Show matching brackets when text indicator is over them
set showmatch

" Add a bit extra margin to the left
if has("folding")
  set foldcolumn=1
endif

set listchars=eol:↲,tab:»\ ,trail:·,extends:▶,precedes:◀,conceal:┊,nbsp:␣
set list

"""""""""""""""""""""""""""""""""""""""
" => Colors
"""""""""""""""""""""""""""""""""""""""
" Enable syntax highlighting
syntax enable

set autoindent

try
  colorscheme desert
catch
endtry

set background=dark

"""""""""""""""""""""""""""""""""""""""
" => Spaces and Tabs
"""""""""""""""""""""""""""""""""""""""
" Use spaces instead of tabs
set expandtab
" Be smart when using tabs
set smarttab
" 1 tab == 2 spaces
set shiftwidth=2
set tabstop=2
" number of visual spaces per TAB
set tabstop=2
" number of spaces in tab when editing
set softtabstop=2

set autoindent
set smartindent
set wrap

"""""""""""""""""""""""""""""""""""""""
" => Search
"""""""""""""""""""""""""""""""""""""""
" Makes search act like search in modern browsers
set incsearch

" Highlight search results
set hlsearch

" Ignore case when searching
set ignorecase

set smartcase

" For regular expressions turn magic on
set magic

""""""""""""""""""""""""""""""
" => Status line
""""""""""""""""""""""""""""""
" Always show the status line
set laststatus=2

" Format the status line
set statusline=\ %{HasPaste()}%F%m%r%h\ %w\ \ CWD:\ %r%{getcwd()}%h\ \ \ Line:\ %l\ \ Column:\ %c

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" => Moving around, tabs, windows and buffers
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Return to last edit position when opening files (You want this!)
au BufReadPost * if line("'\"") > 1 && line("'\"") <= line("$") | exe "normal! g'\"" | endif

"""""""""""""""""""""""""""""""""""""""
" => Mappings
"""""""""""""""""""""""""""""""""""""""
let mapleader = ","
" Map <Space> to / (search) and Ctrl-<Space> to ? (backwards search)
map <space> /
map <C-space> ?

" Disable highlight when <leader><cr> is pressed
map <silent> <leader><cr> :nohlsearch<cr>

" Move to next or previous buffer
map <leader>l :bnext<cr>
map <leader>h :bprevious<cr>

" Remap VIM 0 to first non-blank character
map 0 ^

" Toggle paste mode on and off
map <leader>pp :setlocal paste!<cr>

"""""""""""""""""""""""""""""""""""""""
" => Normal and Visual Mode Mappings
"""""""""""""""""""""""""""""""""""""""
" Fast saving
nmap <leader>w :w!<cr>
" move vertically by visual line
nnoremap j gj
nnoremap k gk

" Move a line of text up or down with indentation
" from https://vim.fandom.com/wiki/Moving_lines_up_or_down#Mappings_to_move_lines
nmap <M-j> mz:m+<cr>`z
nmap <M-k> mz:m-2<cr>`z
vmap <M-j> :m'>+<cr>`<my`>mzgv`yo`z
vmap <M-k> :m'<-2<cr>`>my`<mzgv`yo`z
nmap <D-d> dd<cr>
nmap <C-d> dd<cr>k

if has("mac") || has("macunix")
  nmap <D-j> <M-j>
  nmap <D-k> <M-k>
  vmap <D-j> <M-j>
  vmap <D-k> <M-k>
endif

"""""""""""""""""""""""""""""""""""""""
" => Insert Mode Mappings
"""""""""""""""""""""""""""""""""""""""
" Alternative escape sequences
inoremap jk <Esc>
inoremap kj <Esc>

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" => Spell checking
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Pressing ,ss will toggle and untoggle spell checking
map <leader>ss :setlocal spell!<cr>

" Shortcuts using <leader>
map <leader>sn ]s
map <leader>sp [s
map <leader>sa zg
map <leader>s? z=

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" => Utility functions
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" Returns true if paste mode is enabled
function! HasPaste()
    if &paste
        return 'PASTE MODE  '
    endif
    return ''
endfunction

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
" => Other settings (no categorization yet)
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
"Disable ftplugin/gitcommit.vim textwidth
augroup filetype_gitcommit
  autocmd!
  autocmd FileType gitcommit setlocal textwidth=0
augroup END
