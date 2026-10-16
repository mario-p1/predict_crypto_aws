# Coding style
Add abstractions only when explicilty asked.
Keep minimal diffs.
Try to keep the comments at minimal level.

# Tooling
Ruff is available for linting and formatting.
`make format` is shorthand for formatting and linting the code after editing files.

# Sandbox
The host `.venv` doesn't work in the sandbox. Before running any `uv` or `make` command, use a venv at another location:
```bash
export UV_PROJECT_ENVIRONMENT=/home/agent/.venvs/predict_crypto_aws
```
