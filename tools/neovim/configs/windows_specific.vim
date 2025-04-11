" Windows-specific Neovim settings

" Windows clipboard
set clipboard=unnamed

" Font settings for GUI Neovim on Windows
if exists('g:neovide') || exists('g:fvim_loaded')
  set guifont=JetBrains\ Mono:h11
endif

" Support for system commands
if has('win32') || has('win64')
  set shell=cmd.exe
  set shellcmdflag=/c
endif

" Windows-specific file paths
set backupdir=~\AppData\Local\nvim-data\backup
set directory=~\AppData\Local\nvim-data\swap
set undodir=~\AppData\Local\nvim-data\undo

" Use forward slashes instead of backslashes
set shellslash

" Fix line endings
set fileformats=dos,unix

" External commands on Windows
if executable('rg.exe')
  set grepprg=rg.exe\ --vimgrep\ --smart-case\ --follow
endif

" Windows-specific key bindings
nnoremap <C-z> <Nop>  " Disable suspend on Windows
nmap <C-a> ggVG  " Select all with Ctrl-A

" PowerShell specific settings
if executable('pwsh.exe')
  " Optional: Use PowerShell as shell
  " set shell=pwsh.exe
  " set shellcmdflag=-command
endif