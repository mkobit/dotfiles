# SSH Config Template
# This template will be populated with values from the build

# Global Options
Host *
    AddKeysToAgent {{add_keys_to_agent}}
    HashKnownHosts {{hash_known_hosts}}
    ServerAliveInterval {{server_alive_interval}}
    IdentitiesOnly {{identities_only}}
{{#use_keychain}}
    UseKeychain yes
{{/use_keychain}}

# Include local configuration
Include {{local_config_path}}

# Host-specific configurations will be inserted here
{{host_configurations}}