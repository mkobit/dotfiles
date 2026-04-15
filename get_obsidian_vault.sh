#!/bin/bash
d="$PWD"
while [ "$d" != "/" ] && [ -n "$d" ]; do
  if [ -d "$d/.obsidian" ]; then
    basename "$d"
    break
  fi
  d=$(dirname "$d")
done
