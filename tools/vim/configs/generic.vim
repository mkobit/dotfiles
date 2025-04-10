" Generic platform Vim configuration
" Used when the specific platform cannot be determined

" Safe defaults for any platform
set nocompatible
set backspace=indent,eol,start
set encoding=utf-8
set fileencoding=utf-8
set fileformats=unix,dos,mac

" Universal clipboard settings
if has('unnamedplus')
    set clipboard=unnamedplus
else
    set clipboard=unnamed
endif

" Cross-platform directory settings
if exists('$TEMP')
    set directory=$TEMP
    set backupdir=$TEMP
elseif exists('$TMP')
    set directory=$TMP
    set backupdir=$TMP
else
    set directory=/tmp
    set backupdir=/tmp
endif

" Generic file ignore patterns
set wildignore+=*.swp,*.bak,*.pyc,*.class,*.o,*.obj,*.exe
set wildignore+=.git/*,.hg/*,.svn/*