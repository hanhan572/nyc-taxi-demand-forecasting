# NYC Taxi Driver Assistant (Royce)

## Scope

A small, testable query assistant for the NYC Taxi Demand Forecasting project.
**All numbers in this initial version are synthetic examples** (`source: mock`),
not the result of XGBoost and not real TLC passenger counts.

## Architecture

`Driver question -> OpenAI Responses function calling -> query tools -> mock forecast data -> natural language response`

- `tools.py`: data interface + deterministic forecast lookups.
- `agent.py`: optional LLM layer / function-call dispatcher.
- `../../tests/test_assistant.py`: offline tests.

## Run from repository root

```bash
python3 -m pip install pytest
python3 -m pytest tests/test_assistant.py -q
python3 -m src.assistant.agent --demo
```

To test real OpenAI function calling (API costs may apply):

```bash
python3 -m pip install openai
export OPENAI_API_KEY="YOUR_KEY"  # set in shell, do not commit
python3 -m src.assistant.agent "Which taxi zones are predicted busiest on Nov 23, 2026 at 6 PM New York time?"
```

Default model can be changed with `OPENAI_MODEL`. Never commit `.env` or secrets.

## Interface contracts

- `get_forecast(location_id: int, forecast_hour: str) -> dict`
- `compare_zones(location_ids: list[int], forecast_hour: str) -> dict`
- `get_high_demand_zones(forecast_hour: str, limit: int = 3) -> dict`

Hours must be valid ISO-8601 strings with a time-zone offset. Returned data explicitly records `source: mock`.

## Future integration

Replace the mock data lookup with the agreed `model_forecasts` database query
without changing the tool signatures. Schema details to confirm with Haoran:
`location_id`, `forecast_hour`, `predicted_pickups`, `model_version`.
Evelyn/Steven supply upstream zone/hour features and ML forecasts; Haoyan
can call the assistant after its API is exposed.

## Known limitations

- Only zones 161, 236 and 132; only two sample hours on Nov 23, 2026.
- Forecasts are synthetic; nothing is being trained or pulled from PostgreSQL.
- Offline tests verify deterministic tool behavior; live API integration needs
  a valid key and network access and has not been verified by these tests.
