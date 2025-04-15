# SSH Config Template

# Global Options
Host *
    AddKeysToAgent {{add_keys_to_agent}}
    HashKnownHosts {{hash_known_hosts}}
    ServerAliveInterval {{server_alive_interval}}
    IdentitiesOnly {{identities_only}}
{{#use_keychain}}
    UseKeychain yes
{{/use_keychain}}

# Note: This is a generated file, do not edit
# Generated config paths will be absolute, so they can be used from any location

# Host-specific configurations will be inserted here
{{host_configurations}}