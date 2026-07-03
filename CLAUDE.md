# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in ANTHROPIC_API_KEY and CLAUDE_MODEL
```

## Running Patterns

```bash
# Run a single pattern
python run.py --pattern react
python run.py --pattern plan_execute
python run.py --pattern rewoo
python run.py --pattern reflexion
python run.py --pattern hierarchical
python run.py --pattern dag
python run.py --pattern network
python run.py --pattern consensus

# Run with a custom incident
python run.py --pattern react --incident "A gas leak at 12 Baker St with 3 casualties."

# Run all 8 patterns sequentially (saves outputs to ./outputs/ and prints a comparison table)
python run.py --pattern all --auto-approve
```

The `--auto-approve` flag skips the interactive `request_human_approval` tool prompt. Without it, you'll be prompted in the terminal to approve or deny dispatch actions.

## Architecture

The project implements and compares 8 agentic patterns using **LangGraph** and **Anthropic Claude**, all applied to a UK emergency response simulation (fire, medical, and police dispatch).

### Shared Layer

- **`shared/environment.py`** — A singleton `EmergencyEnvironment` instance (`env`) holding in-memory state: vehicle availability per service (Fire/Medical/Police), hospital status (beds, specialties, burn unit), and road hazards. The `env.__init__()` call in `run.py` resets state between pattern runs to keep comparisons fair.

- **`shared/tools.py`** — Six LangChain `@tool`-decorated functions that wrap `env`: `check_responder_availability`, `query_hospital_status`, `check_opel_level`, `assess_news2_score`, `check_weather_and_traffic_hazards`, and `dispatch_resource`. These are imported by every pattern. `request_human_approval` provides a human-in-the-loop gate (bypassed by `AUTO_APPROVE=true`).

- **`shared/llm.py`** — LLM factory. `get_llm(temperature)` reads `LLM_PROVIDER` env var and returns the appropriate `BaseChatModel` (`ChatAnthropic` or `ChatOllama`). All 8 pattern files use this instead of importing `ChatAnthropic` directly.

- **`shared/telemetry.py`** — `TelemetryCallback(BaseCallbackHandler)` captures per-call token counts, latency, and estimated cost. Passed as a callback to each pattern run; results appear in the comparison table printed by `run.py`.

### Pattern Layer (`patterns/`)

Each pattern file defines a LangGraph `StateGraph`, a typed state schema, graph nodes, and a `run_pattern(incident: str) -> dict` entry point that returns `{"pattern": ..., "final_report": ..., "history": [...]}`.

All 8 patterns use `get_llm()` from `shared/llm.py` rather than importing `ChatAnthropic` directly.

**Single-agent patterns:**
- **`react.py`** — Standard ReAct loop: `agent` node ↔ `ToolNode` (LangGraph prebuilt). Conditional edge routes back to tools if `tool_calls` exist, otherwise ends.
- **`plan_execute.py`** — Separate planner → executor → replanner nodes. The replanner decides whether to continue execution or finish.
- **`rewoo.py`** — Planner front-loads all tool calls with `#E1`, `#E2` placeholder variables. Executor resolves them sequentially without LLM calls between steps. Token-efficient.
- **`reflexion.py`** — Generator node drafts a plan (invoking tools manually within the node), Critic node evaluates against hardcoded safety protocols (fire count, burn-unit routing, hazard check), loops back to Generator unless critique is exactly `"PASS"` or 3 iterations reached, then Synthesizer formats final output.

**Multi-agent topologies:**
- **`hierarchical.py`** — Supervisor routes to Fire/Medical/Police specialist nodes by outputting a single keyword (`Fire`, `Medical`, `Police`, or `FINISH`). Each specialist runs a tool-calling loop and appends to a shared `transcript`.
- **`dag.py`** — Linear pipeline: `Triage` → `ResourceAllocation` → `TrafficCoordinator` → `Compiler`. No loops or feedback edges.
- **`network.py`** — Fire Chief, Police Chief, and Medical Chief agents pass messages to each other directly in a multi-turn conversational loop (no central orchestrator).
- **`consensus.py`** — Three independent expert agents (Threat Analyst, Resource Chief, Public Safety Liaison) each score risk severity; their scores are aggregated until consensus or a max-round limit.

### Outputs

Each `run_pattern` call saves a Markdown report to `outputs/report_<pattern_name>.md`. The `outputs/` directory is gitignored-safe — the repo includes pre-generated sample reports.
