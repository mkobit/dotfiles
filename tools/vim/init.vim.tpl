" Neovim Configuration
" {{generated_notice}}

" Load Vim settings
set runtimepath^=~/.vim runtimepath+=~/.vim/after
let &packpath=&runtimepath
source ~/.vimrc

" Neovim-specific settings
if has('nvim')
    " Terminal mode
    tnoremap <Esc> <C-\><C-n>
    tnoremap <C-v><Esc> <Esc>
    
    " Enable true colors
    set termguicolors
    
    " Custom Neovim settings
    {{neovim_specific_settings}}
    
    " Include local configuration
    if filereadable(expand("~/.config/nvim/init.local.vim"))
        source ~/.config/nvim/init.local.vim
    endif
endif