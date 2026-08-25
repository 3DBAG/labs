.PHONY: build serve

build:
	uv run properdocs build --strict

serve:
	uv run properdocs serve
