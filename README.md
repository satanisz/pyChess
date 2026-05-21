PyChess sprite demo
===================

Small pygame experiment packaged with a modern `src/` layout.

Development
-----------

Create an environment and install the project with its development tools:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -e . --group dev
```

Run the checks:

```powershell
.\.venv\Scripts\python -m ruff format .
.\.venv\Scripts\python -m ruff check .
.\.venv\Scripts\python -m pytest
```

Run the demo:

```powershell
.\.venv\Scripts\python -m pychess
```
