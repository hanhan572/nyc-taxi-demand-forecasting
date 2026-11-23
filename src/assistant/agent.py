"""Natural-language interface to deterministic forecast lookup tools."""
import argparse
import json
import os

from .tools import compare_zones, get_forecast, get_high_demand_zones

TOOL_DEFINITIONS = [
    {
        "type": "function", "name": "get_forecast",
        "description": "Look up the forecast pickup count for one NYC taxi zone at a specific hour.",
        "strict": True,
        "parameters": {"type": "object", "properties": {
            "location_id": {"type": "integer", "description": "NYC TLC pickup location ID"},
            "forecast_hour": {"type": "string", "description": "Exact ISO-8601 hour with timezone offset, e.g. 2026-11-23T18:00:00-05:00"}},
            "required": ["location_id", "forecast_hour"], "additionalProperties": False}
    },
    {
        "type": "function", "name": "compare_zones",
        "description": "Compare forecast pickup counts for 2 to 5 NYC taxi zone IDs at the same hour.",
        "strict": True,
        "parameters": {"type": "object", "properties": {
            "location_ids": {"type": "array", "items": {"type": "integer"}, "description": "2 to 5 distinct NYC TLC location IDs"},
            "forecast_hour": {"type": "string", "description": "Exact ISO-8601 hour with timezone offset"}},
            "required": ["location_ids", "forecast_hour"], "additionalProperties": False}
    },
    {
        "type": "function", "name": "get_high_demand_zones",
        "description": "Get the highest predicted pickup zones for a particular hour.",
        "strict": True,
        "parameters": {"type": "object", "properties": {
            "forecast_hour": {"type": "string", "description": "Exact ISO-8601 hour with timezone offset"},
            "limit": {"type": "integer", "description": "Maximum number of zones, 1 to 10"}},
            "required": ["forecast_hour", "limit"], "additionalProperties": False}
    },
]

_FUNCTIONS = {
    "get_forecast": get_forecast,
    "compare_zones": compare_zones,
    "get_high_demand_zones": get_high_demand_zones,
}


def dispatch_tool(name: str, arguments: dict) -> dict:
    """Execute only allowlisted read-only queries, with clear error reporting."""
    if name not in _FUNCTIONS:
        return {"status": "error", "message": "Unknown tool"}
    if not isinstance(arguments, dict):
        return {"status": "error", "message": "Tool arguments must be an object"}
    try:
        return _FUNCTIONS[name](**arguments)
    except (TypeError, ValueError) as exc:
        return {"status": "error", "message": str(exc)}


def run_assistant(question: str, *, model: str | None = None) -> str:
    """Use OpenAI Responses function calling; requires OPENAI_API_KEY."""
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is missing. Use --demo for the offline prototype.")
    from openai import OpenAI  # optional package, not needed by offline tests

    client = OpenAI()
    model = model or os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    messages = [{"role": "user", "content": question}]
    instructions = (
        "You assist NYC taxi drivers. You MUST use the provided functions for any "
        "numerical demand claim. Forecast figures currently come from SYNTHETIC MOCK "
        "DATA, not a real predictive model: state that clearly. Never fabricate "
        "unavailable forecasts. Ask for a specific hour and zone when necessary. "
        "The mock sample is for Nov 23 2026, 6 PM or 7 PM America/New_York, "
        "zones 161, 236, and 132 only. Do not treat a higher pickup count "
        "as a guarantee of more profitable rides."
    )
    for _ in range(3):  # limit tool-calling turns
        response = client.responses.create(
            model=model, instructions=instructions, input=messages,
            tools=TOOL_DEFINITIONS,
        )
        messages.extend(response.output)
        calls = [item for item in response.output if item.type == "function_call"]
        if not calls:
            return response.output_text or "No textual answer returned."
        for call in calls:
            try:
                args = json.loads(call.arguments)
                result = dispatch_tool(call.name, args)
            except json.JSONDecodeError:
                result = {"status": "error", "message": "Invalid JSON arguments"}
            messages.append({"type": "function_call_output", "call_id": call.call_id,
                             "output": json.dumps(result)})
    return "The assistant reached the tool-call limit before producing a final answer."


def main() -> None:
    parser = argparse.ArgumentParser(description="NYC Taxi Demand Driver Assistant")
    parser.add_argument("question", nargs="?", help="Natural language question (requires OPENAI_API_KEY)")
    parser.add_argument("--demo", action="store_true", help="Run the deterministic offline demo")
    args = parser.parse_args()
    if args.demo:
        print(json.dumps(get_high_demand_zones("2026-11-23T18:00:00-05:00", 3), indent=2))
    elif args.question:
        print(run_assistant(args.question))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
