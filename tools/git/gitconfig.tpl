[user]
    name = {{user_name}}
    email = {{user_email}}

[core]
    editor = {{preferred_editor}}
    excludesfile = ~/.gitignore_global

[color]
    ui = auto

[include]
    path = ~/.gitconfig.local

[pull]
    rebase = true

# Platform-specific settings will be inserted here
{{platform_specific_settings}}