# Technical Discovery

Findings and implementation decisions from Tickets #1–#5. These supplement the PRD but are kept here to avoid mixing product intent with implementation detail.

---

## Ticket #1: Calendar Loading

### Calendar Data Contract (`calendar.json`)

The calendar file uses the following structure:

```json
{
  "events": [
    {
      "title": "Sales Meeting",
      "location": "Houston, TX",
      "start": "2026-06-17T09:00:00",
      "end": "2026-06-17T10:00:00"
    }
  ]
}
```

Requirements:

- Root object must contain an `events` array (not a bare top-level array).
- Required fields for display and weather lookup: `title`, `location`, `start`.
- `start` shall be an ISO 8601 datetime string.
- `end` may be present but is unused.
- Default file path: `data/calendar.json`.

### Date Filtering and Display

- Event `start` times are **naive local wall-clock times** (Decision OQ1).
- "Today" is determined by the system date (`date.today()`) on the machine running the CLI.
- Events are filtered by comparing `event.start.date()` to the target date.
- Events are sorted by ascending `start` time.
- Time display format: `9:00 AM` (12-hour, no leading zero on hour).
- Malformed records (missing `title`, `location`, or `start`) are **skipped** (Decision OQ2).

---

## Ticket #2: Weather Retrieval

### Open-Meteo Integration Contract

Weather retrieval uses two Open-Meteo endpoints per event:

1. **Geocoding API** — resolve event location to coordinates.
2. **Forecast API** — retrieve hourly forecast for those coordinates.

Forecast request parameters:

- `hourly=temperature_2m,precipitation_probability`
- `temperature_unit=fahrenheit`
- `timezone=auto`

Event-time matching:

- Match the event `start` time to the hourly bucket `YYYY-MM-DDTHH:00`.
- Display temperature and rain chance rounded to whole numbers (e.g., `72°F`, `20%`).

### Location Geocoding

- Location strings like `"Houston, TX"` are reduced to the city name (text before the comma) for geocoding.
- Open-Meteo Geocoding API is queried with `count=1`.
- The **first** search result is used; there is no disambiguation for ambiguous names.

### Weather Failure Modes

| Condition | Display suffix |
| --- | --- |
| Missing or blank `location` | `Insufficient data to pull weather` |
| Geocode miss, hourly miss, or API/network error | `Weather unavailable` |
| Other events | Continue processing |

### Dependencies

- Local calendar file (`data/calendar.json`)
- Open-Meteo Geocoding API
- Open-Meteo Forecast API (no API key required)

---

## Ticket #3: Recommendations

### Rule Thresholds

| Rule | Condition | Output |
| --- | --- | --- |
| RR-1 Umbrella | Rain probability >= 30% | `Bring an umbrella.` |
| RR-2 Heat | Temperature > 90°F | `Dress appropriately and bring a fan.` |
| RR-3 Jacket | Temperature < 65°F | `It's {temp}°F — bring a jacket.` |
| RR-4 Severe weather | Severe daily `weather_code` (65, 67, 82, 86, 95, 96, 99) | `Plan travel accordingly.` |

Boundary notes:

- Exactly 30% rain triggers RR-1; exactly 90°F does **not** trigger RR-2; exactly 65°F does **not** trigger RR-3.
- Multiple rules can fire for a single event (e.g., rain + heat).

### RR-3 Jacket Output

**Decision (OQ3):** Use temperature-specific messages.

The PRD says "Report exact temperature and remind user to bring a jacket." Implementation uses:

```text
It's 62°F — bring a jacket.
```

Because the message includes the exact temperature, two cold events at different temps produce **different** recommendation strings and are not deduplicated together.

### Deduplication (FR-13)

- Deduplication is by exact string match.
- First occurrence wins; order follows event processing order.
- Fixed-string rules (umbrella, heat, severe weather) dedupe across events; jacket messages dedupe only when the temperature string is identical.

### Failed Weather Handling

Events with failed or missing weather are skipped for recommendation generation. Other events are still evaluated.

### Display Format

When rules fire:

```text
Recommendations

• Bring an umbrella.
• Dress appropriately and bring a fan.
```

When no rules fire:

```text
Recommendations

No special preparation recommended today. Have a great day!
```

### Weather Conditions (replaces Weather Alerts)

Open-Meteo does not provide government-issued severe weather alerts. Instead, the app uses the daily `weather_code` (WMO condition) per event location.

- Fetched via `daily=weather_code` on the Forecast API.
- Matched to the event date (`YYYY-MM-DD`).
- Displayed in a **Weather Conditions** section (one line per unique location):

```text
Weather Conditions

Houston, TX: Rain: Moderate intensity
Galveston, TX: Thunderstorm: Slight or moderate
```

### RR-4 Severe Weather via `weather_code`

RR-4 (`Plan travel accordingly.`) triggers when the daily `weather_code` is in the severe set:

`65, 67, 82, 86, 95, 96, 99` (heavy rain/freezing rain, violent showers, heavy snow showers, thunderstorms).

---

## Ticket #4: CLI REPL

### Commands (FR-14)

| Command | Behavior |
| --- | --- |
| `today` | Display today's plan (events, weather, conditions, recommendations) |
| `help` | Show available commands |
| `exit` | Quit the REPL |

Commands are normalized with `strip().lower()` before matching (e.g., `TODAY` works).

### REPL Behavior

- Prompt: `> `
- Unknown commands print an error and the loop continues.
- `exit` or EOF (Ctrl+D) ends the session; no goodbye message is printed.
- No startup banner — the REPL waits for input immediately.
- `today` uses `date.today()` unless a `target_date` is injected (tests only).

### Testability

`run_repl()` and `handle_command()` accept injectable dependencies:

- `input_fn` — replaces `input()` for scripted commands
- `output_fn` — captures printed output
- `fetch` — mocks Open-Meteo API calls

This keeps REPL logic testable without stdin or network access.

### Entry Point

```bash
pytest
PYTHONPATH=src python3 src/main.py
```

---

## Ticket #5: PRD Validation

### Test Organization

| File | Scope |
| --- | --- |
| `tests_calendar_reader.py` | Calendar loading, filtering, display |
| `tests_weather.py` | Open-Meteo integration, `weather_code` |
| `tests_advice.py` | Recommendation rules |
| `tests_repl.py` | REPL commands and loop |
| `tests_prd.py` | PRD acceptance criteria (AC-1–AC-6) and requirements (FR-8–FR-10) |
| `conftest.py` | Shared mock fetch helpers |

37 tests total; run with `pytest` (configured via `pytest.ini`).

### PRD Acceptance Criteria Coverage

| Criterion | Validated by |
| --- | --- |
| AC-1 | Event appears on `today` command |
| AC-2 | 4:00 PM event uses 4:00 PM hourly forecast (not 9:00 AM) |
| AC-3 | Rain >= 30% triggers umbrella (including exactly 30%) |
| AC-4 | Temp > 90°F triggers heat rule |
| AC-5 | Temp < 65°F triggers jacket recommendation |
| AC-6 | Duplicate recommendations appear once |

### Additional Requirement Tests

- **FR-8:** Blank `location` → `Insufficient data to pull weather`
- **FR-9:** Weather failure on one event does not block others
- **FR-10:** Exact empty-calendar message format
- **Boundaries:** 90°F does not trigger heat; 65°F does not trigger jacket

### Test Infrastructure

- `pytest.ini` — `pythonpath = src`, discovers `tests_*.py`
- `conftest.py` — `make_mock_fetch`, `make_forecast_response`, `make_geocode_response`
- Unit tests do not call live Open-Meteo APIs
- `requirements.txt` — `pytest` only (runtime uses stdlib)

### FR-11 Note

PRD references "Weather Alerts"; implementation uses **Weather Conditions** from daily `weather_code` (see Ticket #3). No separate alert provider.

---

## Decisions

| Decision | Outcome |
| --- | --- |
| Calendar file format | `{"events": [...]}` with required `title`, `location`, `start` |
| Location lookup | City name (text before comma); first geocode result |
| Weather failure copy | `Weather unavailable` |
| Display rounding | Whole °F and whole % rain chance |
| Open-Meteo integration | Geocoding API + Forecast API; no API key required |
| Jacket recommendation copy | `It's {temp}°F — bring a jacket.` (temperature-specific) |
| Rule thresholds | Rain >= 30%; heat > 90°F; cold < 65°F |
| Recommendation deduplication | Exact string match; first occurrence kept |
| Weather conditions | Daily `weather_code` per location; replaces NWS-style alerts |
| RR-4 severe weather | Triggered by severe daily `weather_code` values |
| REPL commands | `today`, `help`, `exit`; case-insensitive |
| REPL exit | `exit` command or EOF; no farewell message |
| REPL testability | Injectable `input_fn`, `output_fn`, `fetch` |
| Event timezone | Naive local wall-clock time at event location (OQ1) |
| Malformed calendar records | Skip invalid entries; continue processing valid events (OQ2) |
| PRD validation | `tests_prd.py` maps AC-1–AC-6 and FR-8–FR-10 |
| Test strategy | Mocked API fetch; no network in unit tests |

---

## Assumptions

### A4 — Confirmed (OQ1)

Event `start` datetimes are naive **local wall-clock times** and are matched directly to Open-Meteo hourly buckets in the event location's local timezone (`timezone=auto`). They are not treated as UTC.

### A5

"Today" is determined by the system date (`date.today()`) on the machine running the CLI.

### A6 — Confirmed (OQ2)

Malformed calendar entries (missing `title`, `location`, or `start`, or invalid `start` format) are **skipped**. Valid events continue to be processed. Blank `location` on an otherwise valid event is still handled at weather lookup time (`Insufficient data to pull weather`).

### A7

Recommendation rules evaluate only events with successfully retrieved weather data.

---

## Open Questions

All open questions resolved.

### OQ1 — Resolved

Event `start` times are naive **local wall-clock times** at the event location, not UTC.

### OQ2 — Resolved

Malformed calendar records are **skipped** rather than causing a parse error.

### OQ3 — Resolved

Use temperature-specific jacket messages: `It's {temp}°F — bring a jacket.`

### OQ4 — Resolved

Use Open-Meteo daily `weather_code` (WMO condition) instead of government advisories. Display in a **Weather Conditions** section; RR-4 uses severe code values.

---

## Risks (Implementation Notes)

| Risk | Severity | Mitigation |
| --- | --- | --- |
| Weather API unavailable | Medium | Display `Weather unavailable` for the affected event; continue other events |
| Missing event fields | Low | Skip malformed records; blank `location` shows insufficient-data message |
| Ambiguous location names | Medium | Geocode city name (text before comma); use first search result |
| Rule implementation drift | Medium | `tests_prd.py` + module tests cover all rules and boundaries |
