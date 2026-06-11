" Allow backspacing over everything in insert mode
set backspace=indent,eol,start

" Enable persistent undo (maintain undo history between sessions)
set undofile
set undodir=~/.vim/undodir
set undolevels=1000
set undoreload=10000

" Don't create backup files
set nobackup
set nowritebackup
set noswapfile

" Auto-save when focus is lost
autocmd FocusLost * silent! wall

" Automatically read files when changed outside of Vim
set autoread

" Use system clipboard for all operations
set clipboard=unnamed,unnamedplus

" Set a reasonable update time (affects plugins like gitgutter)
set updatetime=300

" Don't redraw screen during macros (performance improvement)
set lazyredraw

" Show matching brackets when cursor is over them
set showmatch
set matchtime=2

" Enable spell checking but turn it off by default
set spelllang=en_us
set nospell
" Toggle spell checking with F7
nnoremap <F7> :setlocal spell!<CR>

" Auto-complete settings
set completeopt=menuone,longest,preview

" Automatically close matching brackets/quotes
inoremap ( ()<Left>
inoremap [ []<Left>
inoremap { {}<Left>
inoremap " ""<Left>
inoremap ' ''<Left>
inoremap ` ``<Left>

" But allow deleting them in pairs too
inoremap <expr> <BS> DeletePairChar()
function! DeletePairChar()
  let pairs = { '(': ')', '[': ']', '{': '}', '"': '"', "'": "'", '`': '`' }
  let chr = getline('.')[col('.') - 2]
  let close = getline('.')[col('.') - 1]
  return has_key(pairs, chr) && pairs[chr] == close ? "\<Right>\<BS>\<BS>" : "\<BS>"
endfunction

" Automatically save when exiting insert mode
autocmd InsertLeave * silent! update

" Automatically strip trailing whitespace on save
autocmd BufWritePre * :%s/\s\+$//e

" Enable word wrapping for text files
autocmd FileType text,markdown,html,tex,adoc setlocal wrap linebreak nolist

" Automatically continue comments on new lines
set formatoptions+=r

" Allow virtual editing in visual block mode
set virtualedit=block

" Make Y behave like D and C (yank to end of line)
nnoremap Y y$

" Preserve selection when indenting in visual mode
vnoremap < <gv
vnoremap > >gv

" Maintain cursor position when joining lines
nnoremap J mzJ`z

" Quickly insert an empty new line without entering insert mode
nnoremap <Leader>o o<Esc>
nnoremap <Leader>O O<Esc>

" Quick save
nnoremap <Leader>w :w<CR>

" Disable Ex mode (avoid accidental activation)
nnoremap Q <nop>

" Disable recording (avoid accidental activation)
" Uncomment if you don't use macros
" nnoremap q <nop>

" Automatically create directories when saving files
augroup BWCCreateDir
  autocmd!
  autocmd BufWritePre * if expand("<afile>")!~#'^\w\+:/' && !isdirectory(expand("%:h")) | execute "silent! !mkdir -p ".shellescape(expand('%:h'), 1) | redraw! | endif
augroup END
