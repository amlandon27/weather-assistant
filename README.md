# Weather-Aware Daily Planning Advisor

CLI that shows today's calendar events with weather forecasts and preparation recommendations.

## Run

The app uses Python stdlib only — no pip install needed.

```bash
PYTHONPATH=src python3 src/main.py
```

Commands: `today`, `help`, `exit`

## Test

```bash
pip install pytest
pytest
```

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
  technical-discovery.md # Added to track decisions made during vibe-coding
  tickets.md          # Implementation broken into five one-line tickets

tests/                # Automated tests proving logic 
data/
  calendar.json       # Used ChatGPT to create file with three events per day between different cities near Houston.
```

## Vibe Report

```text
This was my first time vibe coding and I learned so much.

I didn't feel the AI's vibe drift too much throughout, but I think this is because I spent a lot of time working through the PRD Builder from Karo Ziemiński with ChatGPT. 

I didn't have to use manual coding to fix a logic error. I think maybe this is because I had a detailed PRD and went ticket by ticket with testing (or I missed something, whihch I hope is not the case. I did manually set up the files and folder structure and connect my Cursor to Github. 

My most successful steering prompt was asking Cursor to create and populate a technical-discovery file with key technical decisions we made. At first, I was having it update the PRD with these, but then I researched more and it seemed like it was best practice to leave the PRD pretty set and document these elsewhere.  I also had to steer it to a using specific weather code numbers as a substitute for severe weather warnings, which I initially anticipated the API having, but realized during vibe-coding it didn't. 
```

