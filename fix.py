with open("src/python/jules_cli/jules_cli/models.py", "r") as f:
    content = f.read()

content = content.replace(
    "def _generate_next_value_(name: str, _start: int, _count: int, _last_values: list[Any]) -> Any:",
    "def _generate_next_value_(name: str, start: int, count: int, last_values: list[str]) -> str:  # type: ignore[override]"
)

with open("src/python/jules_cli/jules_cli/models.py", "w") as f:
    f.write(content)
