# Contributing to pyobs-core

Thanks for your interest in contributing. Bug reports, questions and pull requests are welcome.

## Reporting issues

Please use the [issue tracker](https://github.com/pyobs/pyobs-core/issues). For a bug, include what you did, what you expected, what happened instead, and the version you are running. For larger changes, open an issue first so we can agree on the approach before you spend time on code.

## Development setup

```bash
uv sync
```

## Making a change

1. Fork the repository and create a branch from `develop`.
2. Keep the change focused. Unrelated cleanups belong in a separate pull request.
3. Add or update tests and documentation where it makes sense.
4. Run the checks before you push:

   - `uv run ruff check .`
   - `uv run black --check .`
   - `uv run pyrefly check`
   - `uv run pytest`

5. Open a pull request against `develop`, not `main`. CI runs on every pull request.

## Releases

Releases are cut by the maintainers from `main`. Notable changes are listed in [CHANGELOG.md](CHANGELOG.md).

## License

By contributing, you agree that your contributions are licensed under the MIT License of this project.
