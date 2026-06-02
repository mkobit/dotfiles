cat << 'PATCH' > zellij.patch
--- src/chezmoi/.chezmoitemplates/shell/zellij.sh
+++ src/chezmoi/.chezmoitemplates/shell/zellij.sh
@@ -10,8 +10,13 @@
     # We strip out the `_zellij "$@"` execution and leave only the definitions and aliases.
     if [[ "{{ .shell }}" == "zsh" ]]; then
         eval "$(zellij setup --generate-completion zsh | grep -v '^_zellij "$@"$')"
+        compdef zj=zellij
+        compdef zja=zellij
+    elif [[ "{{ .shell }}" == "bash" ]]; then
+        eval "$(zellij setup --generate-completion {{ .shell }})"
+        complete -F _zellij -o bashdefault -o default zj
+        complete -F _zellij -o bashdefault -o default zja
     else
         eval "$(zellij setup --generate-completion {{ .shell }})"
     fi
 fi
PATCH
patch -p0 < zellij.patch && rm zellij.patch patch_zellij.sh
