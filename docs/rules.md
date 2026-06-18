# Persona & Constraints

## Application

- Python 3.9+
- CLI REPL (no web UI)
- Calendar data: local `data/calendar.json`
- Weather: Open-Meteo Geocoding + Forecast APIs (no API key)
- Tests: pytest

## Project structure

```text
specs/
  PRD.md              # source of truth

docs/
  rules.md            # persona and constraints
  technical-discovery.md
  tickets.md

src/
  calendar_reader.py  # load and filter events
  weather.py          # Open-Meteo integration
  advice_engine.py    # rule-based recommendations
  main.py             # REPL and display

tests/
  tests_prd.py        # PRD acceptance criteria validation
  ...

data/
  calendar.json
```

## Conventions

- Stdlib only (no third-party runtime dependencies)
- Logic separated from presentation
- Injectable `fetch` for testable API calls
- High-level comments on non-obvious code chunks
- Logging via `logging` module
- Follow requirements in `specs/PRD.md`; do not add features outside the PRD
- Rule-based, deterministic recommendations; no LLM-generated advice
- Keep files small and focused on a single responsibility
- Continue processing events when weather retrieval fails for one event

## Running

```bash
pip install pytest
pytest
PYTHONPATH=src python3 src/main.py
```
