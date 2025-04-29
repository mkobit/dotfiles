""" Disable vi compatibility mode for improved features
set nocompatible
""" Enable syntax highlighting
syntax on
""" Enable filetype detection, plugins, and indentation
filetype plugin indent on

""" Map jk and kj to escape in insert mode
""" This provides alternative ways to exit insert mode without reaching for Esc
inoremap jk <Esc>
inoremap kj <Esc>
