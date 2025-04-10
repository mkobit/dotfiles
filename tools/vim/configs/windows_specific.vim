" Windows-specific Vim configuration

" Windows path handling
set directory=$TEMP
set backupdir=$TEMP
set viewdir=$TEMP

" Handle Windows paths with spaces
set shellslash

" Windows-specific file ignores
set wildignore+=*\\tmp\\*,*\\AppData\\*,*.exe,*.dll

" Handle Windows temp directory
if has('win32') || has('win64')
    set undodir=$TEMP
endif

" Windows GUI options
if has('gui_running')
    set guifont=Consolas:h11
    set guioptions-=m  " Remove menu bar
    set guioptions-=T  " Remove toolbar
    set guioptions-=r  " Remove right-hand scroll bar
endif