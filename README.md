# Comparing Various Agentic Patterns and Their Use Cases

## Context

Product owners and solution architects are often confused about agents, agentic patterns, and the best use cases for GenAI.

The concerns in this context are related to:

1. **Agent vs. Workflow/RAG integration:** Whether a specific use case warrants building an autonomous agent, or whether it simply requires tools and resources to augment information (RAG) or to coordinate existing tools through schemas like MCP (Model Context Protocol).
   - **Autonomous scope:** Agents operate autonomously with a defined goal, a specific role, and an operational context (backstory).
   - **Workflow understanding:** It is crucial to trace the end-to-end operational workflow. For example, in emergency services, what happens when a distress call is received? What information is needed at each step, and where are the primary bottlenecks?
   - **System switching and overhead:** Analyse how many different systems an operator has to switch between to complete a task. (For example, in the UK, a 999 operator triages the service — Police, Fire, or Ambulance — identifies the location automatically or manually, and handles dispatch interfaces. Some interfaces may be slow or prone to failure.)
2. **Topology selection:** Once an agentic solution is justified, decide which specific agentic pattern/topology fits the operational domain best.

## Goal

The goal of this project is twofold:

1. **Implement and map topologies:**
   - **Single-agent patterns:**
     - **ReAct** — Reason + Act loop (tool calls interleaved with reasoning).
     - **Plan-and-Execute** — separating the planning phase from the execution phase.
     - **ReWOO** (Reason Without Observation) — planning all tool calls upfront and executing them in batch.
     - **Reflexion** — self-critique and iterative self-improvement loops.
   - **Multi-agent topologies:**
     - **Hierarchical** — Orchestrator delegates tasks to specialised sub-agents.
     - **Acyclic / DAG** — A directed pipeline of specialised nodes with no feedback loops.
     - **Network (Peer-to-Peer)** — Agents communicating laterally without a central manager.
2. **Demonstrate use cases & core tasks:**
   - **Consensus / Joint Debate** — multiple specialist agents debate and converge on a unified evaluation.
   - **Common tasks demonstrated** — external API queries, stateful databases, and human-in-the-loop validation.

To make these patterns relatable and impactful, they are implemented within the domain of **Emergency Dispatch & Incident Coordination** (handling fire suppression, medical triage, traffic routing, and risk management).

A UK emergency response scenario is used as the reference here.

## Agentic Patterns: Emergency Response & Disaster Dispatch

This repository implements, demonstrates, and compares **8 core agentic patterns** (4 single-agent patterns and 4 multi-agent topologies) using **LangGraph** and **Anthropic Claude**. 

Each pattern coordinates resources (Fire, Medical, Police) in a stateful mock environment simulating critical incident dispatching.

---

### 🗺️ Architectural Patterns Implemented

### Single-Agent Patterns
1. **ReAct (Reason + Act)**: A single agent that incrementally loops between reasoning and tool invocation (`patterns/react.py`).
2. **Plan-and-Execute**: A planner agent generates a sequence of steps; an executor runs them, and a replanner reviews and adapts the plan as events unfold (`patterns/plan_execute.py`).
3. **ReWOO (Reason Without Observation)**: An agent plans the entire chain of tool calls upfront with placeholder variables. The executor resolves them without intermediate LLM invocations, making it highly token-efficient (`patterns/rewoo.py`).
4. **Reflexion**: A generator agent proposes a dispatch plan, which a critic agent evaluates against strict protocols. The plan is iteratively refined based on critique until it passes safety checks (`patterns/reflexion.py`).

#### Multi-Agent Topologies
5. **Hierarchical**: An Incident Commander (Supervisor) coordinates the operation by delegating specific issues to specialised Fire, Medical, and Police sub-agents who execute tools and report back (`patterns/hierarchical.py`).
6. **Acyclic / DAG**: A unidirectional pipeline of specialised agents (Triage ──► Resource Allocation ──► Traffic Coordinator ──► Compiler) without loops (`patterns/dag.py`).
7. **Network (Peer-to-Peer)**: Specialised agents (Fire Chief, Police Chief, Medical Chief) negotiate coordinates and assets laterally in a conversational loop without central orchestrator oversight (`patterns/network.py`).
8. **Consensus / Joint**: Three independent experts (Threat Analyst, Resource Chief, Public Safety Liaison) evaluate risk severity and debate their scores until they reach consensus or average agreement (`patterns/consensus.py`).

---

### 🛠️ Setup Instructions

#### 1. Prerequisites
Python 3.10+. Clone the repository and create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### 2. Configure Environment Variables
Copy the example environment configuration:
```bash
cp .env.example .env
```
Open `.env` and fill in your Anthropic API Key:
```env
ANTHROPIC_API_KEY=sk-ant-api03-...
CLAUDE_MODEL=claude-sonnet-4-6
```

---

### 🚀 How to Run

#### Run a Single Pattern
Run a pattern on the default or a custom incident:
```bash
# Run ReAct
python run.py --pattern react

# Run Plan-and-Execute with a custom incident
python run.py --pattern plan_execute --incident "A minor car crash on North Highway with no severe injuries but blocking traffic."
```

#### Run and Compare All Patterns
Run all patterns sequentially, saving outputs to `./outputs/` and printing a comparative telemetry matrix at the end:
```bash
python run.py --pattern all --auto-approve
```

---

### 📁 Code Structure

* [`shared/environment.py`](shared/environment.py) — Stateful database representing responders (vehicles availability), hospitals (specialties and beds), hazards, and a dispatch logger.
* [`shared/tools.py`](shared/tools.py) — LangChain-decorated tools (`dispatch_resource`, `query_hospital_status`, etc.) acting on the stateful database.
* [`patterns/`](patterns/) — Individual pattern graph definitions in LangGraph.
* [`run.py`](run.py) — Main command-line orchestrator and telemetry logger.

## Walkthrough — Agentic Patterns Implementation (Finalized)

We have successfully updated the documentation and verified all **8 core agentic patterns** in the [agentic-patterns](.) repository. The codebase models an **Emergency Response & Incident Dispatch (999/911)** simulation, showing how single-agent patterns and multi-agent topologies route responders, query hospitals, coordinate traffic corridors, and reach threat assessments in a stateful mock environment using **LangGraph** (with Anthropic Claude).

---

### 📁 Implemented Repository Structure

The [agentic-patterns](.) folder now contains the following:

```
agentic-patterns/
├── .env.example
├── .env                  # Configured with ANTHROPIC_API_KEY and CLAUDE_MODEL
├── requirements.txt      # LangGraph, python-dotenv, tabulate
├── run.py                 # CLI runner to execute and compare patterns
├── shared/
│   ├── __init__.py
│   ├── environment.py    # Stateful mock database of responders/hospitals
│   └── tools.py          # LLM tools (dispatch, check_status, weather, query_db)
├── patterns/
│   ├── __init__.py
│   ├── react.py          # Single-Agent: ReAct
│   ├── plan_execute.py   # Single-Agent: Plan-and-Execute
│   ├── rewoo.py          # Single-Agent: ReWOO (Reason Without Observation)
│   ├── reflexion.py      # Single-Agent: Reflexion (Self-Critique)
│   ├── hierarchical.py   # Multi-Agent: Hierarchical (Orchestrator-Subagents)
│   ├── dag.py            # Multi-Agent: Acyclic / DAG Pipeline
│   ├── network.py        # Multi-Agent: Peer-to-Peer Network
│   └── consensus.py      # Multi-Agent: Consensus / Joint Debate
└── outputs/               # Saved Markdown reports for each pattern run
```

---

### ⚡ Telemetry & Verification Results

All 8 patterns were executed on the following incident:
> **Incident:** *"Report of a 3-story building fire at 45 Pine St (WC1A Bloomsbury, London) with smoke inhalation casualties and heavy traffic gridlock."*


Below is the comparative summary of execution times and report complexities for each pattern:

| Pattern | Paradigm / Topology | Verification Status | Report Size (chars) | Steps / Messages | Key Characteristics |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **ReAct** | Reason + Act Loop | ✅ Success | ~2,750 | 4 | Simple, direct loop interleaved with tool calls. |
| **Plan-and-Execute** | Plan -> Do -> Replan | ✅ Success | ~20,560 | 24 | Highly detailed; dynamically replans based on feedback. |
| **ReWOO** | Front-loaded Planning | ✅ Success | ~6,880 | 6 | Plans all tools upfront; executes them in one batch. |
| **Reflexion** | Generate & Critique | ✅ Success (Refined Loop) | ~16,400 | 3 (Iterative) | Self-criticizes draft against strict safety protocols, refines until `PASS`. |
| **Hierarchical** | Supervisor & Specialists | ✅ Success | ~17,790 | 4 | Supervisor routes tasks laterally to Fire/Med/Police. |
| **Acyclic / DAG** | Directed Unidirectional | ✅ Success | ~13,310 | 3 | Triage ──► Allocation ──► Traffic ──► Compiler. |
| **Network / P2P** | Direct Agent Dialogue | ✅ Success (Multi-turn) | ~24,840 | 6 (2 rounds) | Chiefs negotiate directly in multi-turn conversation. |
| **Consensus** | Expert Debate & Vote | ✅ Success | ~10,620 | 3 | Multi-agent panel debates and votes on threat score. |

---

### 📝 Generated Output Reports

The compiled Markdown reports for each pattern are saved in the [outputs/](outputs) folder:
1. **ReAct Report:** [outputs/report_react.md](outputs/report_react.md)
2. **Plan-and-Execute Report:** [outputs/report_plan-and-execute.md](outputs/report_plan-and-execute.md)
3. **ReWOO Report:** [outputs/report_rewoo.md](outputs/report_rewoo.md)
4. **Reflexion Report (REV 3 Final):** [outputs/report_reflexion.md](outputs/report_reflexion.md) *(shows Iterations 1, 2, and 3 with full critique and compliance verification)*
5. **Hierarchical Report:** [outputs/report_hierarchical.md](outputs/report_hierarchical.md)
6. **Acyclic / DAG Report:** [outputs/report_acyclic_dag.md](outputs/report_acyclic_dag.md)
7. **Network / P2P Report:** [outputs/report_network_p2p.md](outputs/report_network_p2p.md)
8. **Consensus Report:** [outputs/report_consensus.md](outputs/report_consensus.md)

---

### 🎯 Verification Accomplishments
* **Reflexion Loop Fix:** We tightened `should_continue` in `patterns/reflexion.py` to check for exact `PASS` responses. On iteration 1, the critic withheld approval for a data discrepancy; the agent successfully modified the draft in iteration 2 and received a `PASS` to complete the loop.
* **Network & Consensus Success:** Successfully ran multi-turn peer-to-peer dialogues and expert consensus threat evaluations to completion.
* **Codebase Alignment:** Corrected spelling mistakes and cleaned formatting in the repository's [implementation-plan.md](implementation-plan.md).

---

## 📌 Appendix: Roadmap / TODO (Gap Analysis)

> **Status note:** This repository is an **MVP** — it currently proves the *architectural patterns* work end-to-end, using a paid frontier model (Anthropic Claude) against a simplified mock environment. It does **not yet** prove the project's second, arguably more important goal: that these patterns remain viable and safe when run on **low-cost, sovereign, or on-prem hardware** (e.g. Ollama-hosted open models), applied to a **genuine health / duty-of-care domain** rather than a generic dispatch simulation. The items below track that gap and are intended to be closed incrementally with GitHub Copilot's help.

### 1. Provider abstraction (break the Anthropic lock-in)
- [ ] Introduce a `shared/llm.py` factory that returns a chat model based on an `LLM_PROVIDER` env var (`anthropic`, `ollama`, `bedrock`, etc.), instead of each `patterns/*.py` file hardcoding `ChatAnthropic`.
- [ ] Update `.env.example` with `LLM_PROVIDER`, `OLLAMA_MODEL`, `OLLAMA_BASE_URL` options.
- [ ] Refactor all 8 pattern files to use the factory instead of instantiating `ChatAnthropic` directly.

### 2. Cost & resource telemetry
- [ ] Capture token usage (input/output) per LLM call and per pattern run.
- [ ] Add estimated $ cost per run (model-price-aware) to the comparison table in `run.py`.
- [ ] Add wall-clock latency per LLM call (not just total pattern time) to help compare local vs. hosted models.

### 3. Local / sovereign model proof point
- [ ] Run each pattern against a local Ollama model (e.g. Llama 3.1 8B, Qwen2.5) on the same incident used for the Claude runs.
- [ ] Publish a side-by-side comparison: accuracy/safety pass-rate vs. cost vs. latency, Claude vs. local model.
- [ ] Document a reproducible "sovereign deployment" recipe (Ollama install, model pull, air-gapped run instructions).

### 4. Domain model aligned to UK health / duty-of-care
- [ ] Replace or extend the generic fire/police/hospital dispatch simulation with a UK-relevant duty-of-care scenario (e.g. safeguarding referral triage, mental health crisis response, adult social care duty desk), using believable terminology (NHS 111/999 triage codes, NEWS2 scores, safeguarding levels).
- [ ] Model realistic risk/priority categories and escalation thresholds relevant to duty-of-care decision-making.

### 5. Safety & governance harness
- [ ] Persist the dispatch/decision log to durable storage (file or SQLite) instead of the in-memory `dispatched_log`, so audit trails survive a run.
- [ ] Record human-in-the-loop approvals (or `--auto-approve` bypasses) with identity/timestamp in the audit log, rather than silently skipping.
- [ ] Add a documented data-handling/PII stance given the health-adjacent domain.

### 6. Open-source hygiene
- [ ] Add a `LICENSE` file (MIT/Apache-2.0) at the repo root.
- [ ] Add an "Ethics & Safety" section to this README describing the humanitarian intent, data-handling stance, and limitations of this MVP.

