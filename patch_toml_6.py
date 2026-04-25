
with open('pyproject.toml') as f:
    content = f.read()

new_ignores_add = """
    "ARG001", # Unused function argument
    "D205",  # 1 blank line required between summary line and description
    "D417",  # Missing argument descriptions in the docstring
    "PTH109", # os.getcwd
    "PTH111", # os.path.expanduser
    "E501",  # Line too long
]"""

content = content.replace("PTH118\", # os.path.join\n]", "PTH118\", # os.path.join\n" + new_ignores_add)

with open('pyproject.toml', 'w') as f:
    f.write(content)
