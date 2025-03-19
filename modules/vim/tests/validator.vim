" Vim script validator for testing .vimrc files
" This script is used by the vim_test rule to validate .vimrc files

" Store any errors found during validation
let g:validation_errors = []

" Function to check if a certain option is set
function! CheckOption(option, expected)
  let l:actual = eval('&' . a:option)
  if l:actual != a:expected
    call add(g:validation_errors, 'Option ' . a:option . ' is set to ' . l:actual . ', expected ' . a:expected)
    return 0
  endif
  return 1
endfunction

" Function to check if a mapping exists
function! CheckMapping(mapping)
  let l:maps = execute('map ' . a:mapping)
  if l:maps =~ 'No mapping found'
    call add(g:validation_errors, 'Mapping ' . a:mapping . ' not found')
    return 0
  endif
  return 1
endfunction

" Function to validate the .vimrc file
function! ValidateVimRC()
  " Validate basic settings
  call CheckOption('number', 1)
  call CheckOption('tabstop', 4)
  call CheckOption('expandtab', 1)
  
  " Check for required mappings
  call CheckMapping('<leader>w')
  
  " Report any errors
  if len(g:validation_errors) > 0
    for error in g:validation_errors
      echoerr error
    endfor
    throw 'Validation failed: ' . len(g:validation_errors) . ' errors found'
  endif
endfunction

" Run validation
try
  call ValidateVimRC()
  echo "Validation successful!"
catch
  echoerr v:exception
  exit 1
endtry