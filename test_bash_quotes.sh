#!/bin/bash
cat << "END"
What does bash do to \\ inside double quotes?
END
echo "\$json.Replace('\\u001b', '\u001b')"
