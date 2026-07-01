import subprocess
print(subprocess.run(["pwsh", "-c", "echo '\\u001b\r'"], capture_output=True))
