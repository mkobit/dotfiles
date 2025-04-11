" WSL-specific Neovim settings

" WSL clipboard integration
if has('wsl')
  let g:clipboard = {
        \   'name': 'wslclipboard',
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

" Font settings for GUI Neovim in WSL
if exists('g:neovide')
  set guifont=JetBrainsMono\ Nerd\ Font:h12
endif

" Support for system commands
set shell=/bin/bash

" Path settings for both Windows and WSL
set path+=/usr/include/,/usr/local/include/,/mnt/c/Windows/System32/

" Open URLs in Windows browser from WSL
if has('wsl')
  function! OpenURLUnderCursor()
    let s:uri = expand('<cWORD>')
    let s:uri = substitute(s:uri, '?', '\\?', '')
    let s:uri = shellescape(s:uri, 1)
    call system('cmd.exe /c start "" ' . s:uri)
    redraw!
  endfunction
  nnoremap <leader>o :call OpenURLUnderCursor()<CR>
endif

" External commands in WSL
if executable('rg')
  set grepprg=rg\ --vimgrep\ --smart-case\ --follow
endif

" Fix common issues with WSL terminals
set t_u7=  " Disable terminal capability query