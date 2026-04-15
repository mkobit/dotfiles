#!/usr/bin/env sh
d="$PWD"
found=0
while [ -n "$d" ]; do
  if [ -d "$d/.obsidian" ]; then
    basename "$d"
    found=1
    break
  fi
  if [ "$d" = "/" ]; then
    break
  fi
  d=$(dirname "$d")
done
if [ "$found" -eq 0 ]; then
  exec false
fi
