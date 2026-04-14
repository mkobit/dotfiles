.PHONY: lint-templates lint test

lint-templates:
	uv run djlint src/chezmoi/ --reformat

lint:
	uv run ruff check .
	uv run djlint src/chezmoi/ --check

test:
	uv run pytest src/python
