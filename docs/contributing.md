---
layout: base.njk
title: Contributing
order: 6
tags: docs
---

# Contributing

Contributions are welcome. If you've fixed a bug or built a feature, open a PR and we'll review it.

## Development Setup

Set up your local development environment:

```shell
uv sync --dev --frozen
```

Run checks before opening a PR:

```shell
uv run ruff format --check gourd/ tests/
uv run ruff check gourd/ tests/
uv run ruff check --select FA102,UP007,UP045 gourd/ tests/
uv run ty check gourd/ tests/
uv run pytest
```

Follow code style guidelines in [CODESTYLE.md](../CODESTYLE.md).

## Working on the Docs

The docs site is built with [Eleventy](https://www.11ty.dev/) and deployed automatically to GitHub Pages on every push to `main`.

**Prerequisites:** Node.js 20+

Install dependencies:

```shell
npm install
```

Local development server (live-reloads on file changes):

```shell
npm run dev
```

Then open http://localhost:8080.

Build the site:

```shell
npm run build
```

Output goes to `_site/` (gitignored).

## Reporting Bugs and Requesting Features

Please file bugs and feature requests at <https://github.com/clueboard/gourd/issues>.
