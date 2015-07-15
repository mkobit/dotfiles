[user]
	email = mkobit@gmail.com
	name = Mike Kobit
[core]
	editor = atom --wait
	autocrlf = input
[color]
	ui = true
[alias]
	st = status
	cm = commit -m
	aa = add --all
	ci = commit
	lg = log --graph --pretty=format:'%C(yellow)%h%C(cyan)%d%Creset %s %C(white)- %an, %ar%Creset'
	ll = log --stat --abbrev-commit
	co = checkout
	cob = checkout -b
	sync = pull --rebase
	br = branch
[branch]
	autosetuprebase = always
[push]
	default = simple
