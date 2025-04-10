" WSL-specific Vim configuration

" WSL clipboard integration with Windows
if system('uname -r') =~ 'Microsoft'
    let g:clipboard = {
          \   'name': 'WslClipboard',
          \   'copy': {
          \      '+': 'clip.exe',
          \      '*': 'clip.exe',
          \    },
          \   'paste': {
          \      '+': 'powershell.exe -c [Console]::Out.Write($(Get-Clipboard -Raw).tostring().replace("`r", ""))',
          \      '*': 'powershell.exe -c [Console]::Out.Write($(Get-Clipboard -Raw).tostring().replace("`r", ""))',
          \   },
          \   'cache_enabled': 0,
          \ }
endif

" WSL-specific path handling
set wildignore+=*/mnt/c/WINDOWS/*,*/mnt/c/Program\ Files/*

" Improve interop with Windows paths
set shellslash
set shell=/bin/bash

" Fix for WSL terminal issues
set t_u7=
set t_RV=