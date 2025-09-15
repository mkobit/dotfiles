" Reduce updatetime for more responsive experience
set updatetime=300

" Don't redraw screen during macro execution
set lazyredraw

" Limit syntax highlighting to avoid slowdowns with long lines
set synmaxcol=500

" Special handling for large files
augroup LargeFile
  autocmd!
  " Disable certain features for files > 10MB
  autocmd BufReadPre * if getfsize(expand("%")) > 10000000 |
    \ setlocal syntax= noswapfile noundofile nocursorline |
    \ endif
augroup END

" Use faster grep tools if available
if executable('rg')
  set grepprg=rg\ --vimgrep\ --no-heading\ --smart-case
elseif executable('ag')
  set grepprg=ag\ --nogroup\ --nocolor\ --vimgrep
endif

" Improve performance when opening files with many completions
set shortmess+=c
