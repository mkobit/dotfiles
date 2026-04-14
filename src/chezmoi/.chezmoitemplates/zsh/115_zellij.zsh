{{- $zellij := index . "zellij" | default (dict "enabled" false) -}}
{{- if $zellij.enabled }}
# Zellij aliases
alias zj="zellij"
alias za="zellij attach"
{{- end }}
