

# (N)ullglob: Don't error if no files match
# (n)umeric: Sort numerically to ensure deterministic sourcing
for file in ./scripts/*.zsh*(Nn); do
    [[ -r "$file" ]] && source "$file"
done
