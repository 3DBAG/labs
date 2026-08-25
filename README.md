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
