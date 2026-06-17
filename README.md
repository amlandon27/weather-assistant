# Weather-Aware Daily Planning Advisor

CLI that shows today's calendar events with weather forecasts and preparation recommendations.

## Project Structure

```text
src/                  # Codebase — modular, single-responsibility files
  calendar_reader.py  # load and filter events
  weather.py          # Open-Meteo integration
  advice_engine.py    # rule-based recommendations
  main.py             # REPL and display

specs/
  PRD.md              # Knowledge base — source of truth

docs/
  rules.md            # Constraints
  technical-discovery.md
  tickets.md

tests/                # Guardrails — automated tests proving logic works
data/
  calendar.json
```

## Run

```bash
pip install -r requirements.txt
PYTHONPATH=src python3 src/main.py
```

Commands: `today`, `help`, `exit`

## Test

```bash
pytest
```

