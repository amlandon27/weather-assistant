# Tech stack

## Application

- Python 3.9+
- CLI REPL (no web UI)
- Calendar data: local `data/calendar.json`
- Weather: Open-Meteo Geocoding + Forecast APIs (no API key)
- Tests: pytest

## Project structure

```text
src/
  calendar_reader.py   # load and filter events
  weather.py           # Open-Meteo integration
  advice_engine.py     # rule-based recommendations
  main.py              # REPL and display
tests/
  tests_prd.py           # PRD acceptance criteria validation
data/
  calendar.json
```

## Conventions

- Stdlib only (no third-party runtime dependencies)
- Logic separated from presentation
- Injectable `fetch` for testable API calls
- High-level comments on non-obvious code chunks
- Logging via `logging` module

## Running

```bash
pip install -r requirements.txt
pytest
PYTHONPATH=src python3 src/main.py
```
