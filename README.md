# 3DBAG Labs

3DBAG Labs is the site for experimental content, demos, and
proofs of concept related to the 3DBAG project. The site is built with
[ProperDocs](https://github.com/3DBAG/properdocs) and the MaterialX theme.

## Getting started

You need Python 3.11 or newer, [`uv`](https://docs.astral.sh/uv/), and
`make` installed.

Clone the repository and enter its directory:

```sh
git clone <repository-url>
cd 3dbag-labs
```

Create the project environment and install its locked dependencies with `uv`:

```sh
uv sync
```

## Make recipes

Build the site into the `site/` directory:

```sh
make build
```

Start the local development server with live reloading:

```sh
make serve
```

The development site is available at <http://localhost:8000>.

The equivalent commands can be run directly through `uv`:

```sh
uv run properdocs build
uv run properdocs serve
```

## Contributing an experiment

Add a card by making these two content changes:

1. Add the card's metadata to [`labs-content.json`](labs-content.json). Each
   card is one object in the top-level array. The object must contain:
   `id`, `date_added`, `title`, `description`, `link`, `image`, `authors`,
   `contact`, `license`, `in_3dbag`, and `archived`.
2. Add the card image to [`docs/assets/images/labs/`](docs/assets/images/labs/),
   then set `image` to its path relative to `docs/`, for example
   `assets/images/labs/my-card.jpg`.

Card content requirements:

- `id` must be a unique integer.
- `date_added` must use `YYYY-MM-DD` format.
- `title` and `description` must not be empty. Keep the description to no more
  than 140 whitespace-separated words.
- `link` must be an `http://` or `https://` URL.
- `authors` must contain at least one name, and `contact` must be an email
  address.
- Set `license`, `in_3dbag`, and `archived` to describe the submitted content.

Image requirements:

- The image must be a readable image file stored inside `docs/` (normally in
  `docs/assets/images/labs/`).
- It must be exactly 600×350 pixels. The card displays the image at that size,
  so crop or resize it before committing it.

Run `make build` before opening a pull request. The build validates the card
metadata, checks that the image exists and has the required dimensions, and
generates the card grid on the site.
