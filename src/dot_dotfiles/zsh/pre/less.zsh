# less(1) d
# https://man7.org/linux/man-pages/man1/less.1.html

# -R : Output "raw" control characters (preserves colors, e.g., from man pages)
# -F : Quit if the entire content fits on one screen
# -X : Do not clear the screen after exiting less
# -i : Search is case-insensitive unless uppercase letters are used
# -M : Show more verbose prompt (file position, etc.)
# -N : Show line numbers
# -~ : Display tildes on lines after end of file
# -S : Chop long lines rather than wrap (useful if you want to avoid line wrapping, e.g., when viewing log files with long lines)
export LESS="-RFXiMN~"
