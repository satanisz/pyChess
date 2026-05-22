PyChess
=======

Pygame chess application and headless engine arena. The project uses a modern
`src/` layout, `python-chess` for deterministic rules, and pluggable engines for
human-vs-engine or engine-vs-engine games.

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

Run the desktop game:

```powershell
.\.venv\Scripts\python -m pychess
```

Run against an engine:

```powershell
.\.venv\Scripts\pychess --black-engine random
.\.venv\Scripts\pychess --white-engine random --black-engine heuristic
```

Run the headless arena:

```powershell
.\.venv\Scripts\pychess-arena --white random --black heuristic --games 10
```

Project plan
------------

The implementation roadmap lives in `docs/executive-plan.md`.
