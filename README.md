# Project Title

This repository contains the Sienge MCP integration project. It provides tools and an MCP server wrapper to interact with the Sienge API.

## How to Run

To run the `main.py` script, open a terminal in the project root and execute:

```bash
python main.py
```

> If you use a virtual environment, activate it first (for example `python -m venv venv` then `venv\Scripts\activate` on Windows).

## How to Test

This project uses `pytest` for tests. To run the test suite (including `test_main.py`), run:

```bash
pytest test_main.py
```

> To run all tests, use `pytest` without arguments.

## Requirements

Install dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```

## Notes

- The project contains multiple modules and an MCP server implementation under `src/sienge_mcp/`.
- On Windows, use backslashes for paths and activate virtualenv using `venv\Scripts\activate`.