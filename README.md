# Comparing Various Agentic Patterns and Their Use Cases

## 📖 Context

Product owners and solution architects are often confused about agents, agentic patterns, and the best use cases for GenAI.

The concerns in this context are related to:

1. **Agent vs. Workflow/RAG integration:** Whether a specific use case warrants building an autonomous agent, or whether it simply requires tools and resources to augment information (RAG) or to coordinate existing tools through schemas like MCP (Model Context Protocol).
   - **Autonomous scope:** Agents operate autonomously with a defined goal, a specific role, and an operational context (backstory).
   - **Workflow understanding:** It is crucial to trace the end-to-end operational workflow. For example, in emergency services, what happens when a distress call is received? What information is needed at each step, and where are the primary bottlenecks?
   - **System switching and overhead:** Analyse how many different systems an operator has to switch between to complete a task. (For example, in the UK, a 999 operator triages the service — Police, Fire, or Ambulance — identifies the location automatically or manually, and handles dispatch interfaces. Some interfaces may be slow or prone to failure.)
2. **Topology selection:** Once an agentic solution is justified, decide which specific agentic pattern/topology fits the operational domain best.

## 🎯 Goal

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

To make these patterns relatable and impactful, they are implemented within the domain of **Emergency Dispatch & Incident Coordination** (handling fire suppression, medical triage, traffic routing, and risk management) under a UK emergency response scenario reference.

---

## ⚡ Current Project State

> [!NOTE]
> The codebase is structured as a functional Model-View-Controller/Simulation MVP showcasing 8 distinct agentic patterns implemented using **LangGraph** and **Anthropic Claude**. It sets up clean state machines for complex flows (such as the *Reflexion* loop with safety audits and *Consensus* with multi-agent debate).
> 
> To transition from a single-provider, mock-domain demo to a sovereign-capable, enterprise-grade, UK-aligned healthcare/duty-of-care dispatch harness, there are major architectural and implementation gaps. Some of these gaps do not need to be addressed for the purpose of this project as this is an MVP / POC. Instead they are documented in the Appendix. Addressing high-cost gaps is out of scope for this project as the project is not funded as of today. We use our judgment to determine which gaps to address.

---

## 🗺️ Architectural Patterns Implemented

This repository implements, demonstrates, and compares **8 core agentic patterns** (4 single-agent patterns and 4 multi-agent topologies) using **LangGraph** and **Anthropic Claude**. Each pattern coordinates resources (Fire, Medical, Police) in a stateful mock environment simulating critical incident dispatching.

### 👤 Single-Agent Patterns

1. **ReAct (Reason + Act)**: A single agent that incrementally loops between reasoning and tool invocation ([react.py](patterns/react.py)).
2. **Plan-and-Execute**: A planner agent generates a sequence of steps; an executor runs them, and a replanner reviews and adapts the plan as events unfold ([plan_execute.py](patterns/plan_execute.py)).
3. **ReWOO (Reason Without Observation)**: An agent plans the entire chain of tool calls upfront with placeholder variables. The executor resolves them without intermediate LLM invocations, making it highly token-efficient ([rewoo.py](patterns/rewoo.py)).
4. **Reflexion**: A generator agent proposes a dispatch plan, which a critic agent evaluates against strict protocols. The plan is iteratively refined based on critique until it passes safety checks ([reflexion.py](patterns/reflexion.py)).

### 👥 Multi-Agent Topologies

5. **Hierarchical**: An Incident Commander (Supervisor) coordinates the operation by delegating specific issues to specialised Fire, Medical, and Police sub-agents who execute tools and report back ([hierarchical.py](patterns/hierarchical.py)).
6. **Acyclic / DAG**: A unidirectional pipeline of specialised agents (`Triage` ──► `Resource Allocation` ──► `Traffic Coordinator` ──► `Compiler`) without loops ([dag.py](patterns/dag.py)).
7. **Network (Peer-to-Peer)**: Specialised agents (`Fire Chief`, `Police Chief`, `Medical Chief`) negotiate coordinates and assets laterally in a conversational loop without central orchestrator oversight ([network.py](patterns/network.py)).
8. **Consensus / Joint**: Three independent experts (`Threat Analyst`, `Resource Chief`, `Public Safety Liaison`) evaluate risk severity and debate their scores until they reach consensus or average agreement ([consensus.py](patterns/consensus.py)).

---

## 🛠️ Setup Instructions

### 1. Prerequisites
Python 3.10+. Clone the repository and create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables
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

## 🚀 How to Run

### Run a Single Pattern
Run a pattern on the default or a custom incident:
```bash
# Run ReAct
python run.py --pattern react

# Run Plan-and-Execute with a custom incident
python run.py --pattern plan_execute --incident "A minor car crash on North Highway with no severe injuries but blocking traffic."
```

### Run and Compare All Patterns
Run all patterns sequentially, saving outputs to `./outputs/` and printing a comparative telemetry matrix at the end:
```bash
python run.py --pattern all --auto-approve
```

---

## 📁 Code Structure

* [shared/environment.py](shared/environment.py) — Stateful database representing responders (vehicles availability), hospitals (specialties and beds), hazards, and a dispatch logger.
* [shared/tools.py](shared/tools.py) — LangChain-decorated tools (`dispatch_resource`, `query_hospital_status`, `check_opel_level`, `assess_news2_score`, etc.) acting on the stateful database.
* [shared/llm.py](shared/llm.py) — LLM factory (`get_llm(temperature)`). Returns `ChatAnthropic` or `ChatOllama` based on `LLM_PROVIDER` env var. All 8 patterns use this.
* [shared/telemetry.py](shared/telemetry.py) — LangChain callback handler capturing token counts, latency, and estimated cost per pattern run.
* [patterns/](patterns/) — Individual pattern graph definitions in LangGraph.
* [run.py](run.py) — Main command-line orchestrator and telemetry logger.

---

## 📋 Walkthrough — Agentic Patterns Implementation (Finalized)

The codebase models an **Emergency Response & Incident Dispatch (999/911)** simulation, showing how single-agent patterns and multi-agent topologies route responders, query hospitals, coordinate traffic corridors, and reach threat assessments in a stateful mock environment using **LangGraph** (with Anthropic Claude).

### 📁 Implemented Repository Structure

```
agentic-patterns/
├── .env.example
├── .env                  # Configured with ANTHROPIC_API_KEY and CLAUDE_MODEL
├── requirements.txt      # LangGraph, python-dotenv, tabulate
├── run.py                 # CLI runner to execute and compare patterns
├── shared/
│   ├── __init__.py
│   ├── environment.py    # Stateful mock database of responders/hospitals
│   ├── tools.py          # LLM tools (dispatch, check_status, weather, query_db, opel, news2)
│   ├── llm.py            # LLM factory (ChatAnthropic / ChatOllama via LLM_PROVIDER)
│   └── telemetry.py      # LangChain callback: token counts, latency, cost
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
> **Incident:** *"Report of a 3-story building fire at 14 Kingsbourne Terrace (WC1B 9ZZ, London) with smoke inhalation casualties, possible burns, and severe traffic gridlock on High Holborn."*

Below is the comparative summary of execution times and report complexities for each pattern:

| Pattern | Paradigm / Topology | Verification Status | Run Time (s) | Steps / Messages | Key Characteristics |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **ReAct** | Reason + Act Loop | ✅ Success | ~51 | 4 | Simple, direct loop interleaved with tool calls. |
| **Plan-and-Execute** | Plan -> Do -> Replan | ⚠️ Cost-constrained | 943 (aborted) | 34+ | Replanning loop expanded 22-step plan indefinitely — consumed monthly API quota before completing. |
| **ReWOO** | Front-loaded Planning | ✅ Success | ~65 | 19 | Plans all tools upfront; executes them in one batch. Token-efficient. |
| **Reflexion** | Generate & Critique | ✅ Success (2 iterations) | ~728 | 3 iterations | Critic rejected REV 1 (only 3 Pumping Appliances — NFCC minimum is 4). REV 2 passed. |
| **Hierarchical** | Supervisor & Specialists | ✅ Success | ~160 | 4 | Supervisor routes to Fire → Medical → Police specialists in sequence. |
| **Acyclic / DAG** | Directed Unidirectional | ✅ Success | ~129 | 4 | Triage ──► Allocation ──► Traffic ──► Synthesizer. No feedback loops. |
| **Network / P2P** | Direct Agent Dialogue | ✅ Success (2 rounds) | ~180 | 6 | Fire, Police, Medical chiefs negotiate directly in multi-turn conversation. |
| **Consensus** | Expert Debate & Vote | ✅ Success | ~96 | 3 | All three experts independently scored 4/5 — unanimous first round. |

> **⚠️ Plan-and-Execute note:** Two separate runs both hit API limits before completing (285s then 943s). The pattern's replanning loop expanded an initial 22-step plan to 34+ steps before termination. This is not a code defect — it is an accurate demonstration of the pattern's cost profile. For a METHANE-declared major incident, the replanner treats every new field report as grounds for another planning cycle. The output file `outputs/report_plan-and-execute.md` reflects a pre-UK-alignment run and is retained for structural reference only; do not use it as a current evidence report.

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

* **Reflexion critic caught a real protocol violation:** On iteration 1, the critic identified that only 3 Pumping Appliances were dispatched — the NFCC minimum for a multi-storey structural fire is 4. The generator corrected this in iteration 2 and received a `PASS`. This is exactly the pattern's value proposition: the self-critique loop catches gaps that a single-pass agent would miss.

* **Consensus reached unanimous first-round agreement:** All three expert agents (Threat Analyst, Resource Chief, Public Safety Liaison) independently scored the incident 4/5, reaching consensus without a second debate round. The agreed finding — that the High Holborn gridlock was the single greatest escalation risk — emerged from three distinct analytical lenses converging on the same operational bottleneck.

* **Plan-and-Execute revealed an important architectural limit:** Two separate runs on this incident both hit API usage limits before completing (285s then 943s). The pattern generated an initial 22-step plan, then its replanning loop expanded the plan to 34+ steps as each executed action surfaced new operational variables — utility isolation status, mutual aid ETAs, Forward Command Point confirmation. The replanner treated each new field update as grounds for another full planning cycle, with no inherent termination condition.

  This is not a bug. It is the pattern behaving correctly — and it illustrates a fundamental trade-off: Plan-and-Execute is well-suited to **bounded tasks** (a defined goal, a finite set of unknowns, a clear done-state). A METHANE-declared major incident is the opposite: an open-ended, continuously evolving situation where new information arrives faster than the replanner can integrate it. For this domain, the pattern's adaptive replanning becomes a liability rather than an asset. ReWOO (which commits to a plan upfront and does not replan) completed the same incident in 65 seconds at a fraction of the cost.

* **Network & Consensus ran multi-turn dialogues to completion** across 2 full negotiation rounds, with all three service chiefs making tool calls and updating their positions based on peer statements.

* **UK/NHS domain alignment confirmed end-to-end:** All 7 successfully completed pattern outputs reference "14 Kingsbourne Terrace, WC1B 9ZZ", fictional NHS trust names, UK vehicle terminology (Pumping Appliance, Double-Crewed Ambulance, HART Team, Roads Policing Unit), OPEL levels, and NEWS2 scoring throughout.

---

## 🤝 Get Involved

This project is self-funded and open source. Phase 1 — the eight patterns, UK/NHS domain alignment, LLM factory, per-run telemetry, and human-in-the-loop gate — is complete and on `main`. Phase 2 (sovereign deployment on local models, Care Act 2014 domain, persistent audit trail) needs people who care about responsible AI in public services. If that is you, there is real work to pick up.

### Who we are looking for

**NHS and emergency services practitioners.** The 999 simulation is deliberately fictional — but the protocols it references (METHANE, OPEL levels, NEWS2 scoring, NFCC minimum appliance counts, JESIP command structure) are real, and the Reflexion pattern already catches one genuine protocol violation per run. If you work in blue-light services, ambulance operations, or NHS command and control, your domain corrections are worth more than any pull request. Open an issue and tell us where we got it wrong — that is the most valuable contribution this project can receive.

**Engineers who care about portability.** The LLM factory (`shared/llm.py`) means you can run every pattern without an Anthropic API key — set `LLM_PROVIDER=ollama` in `.env` and point it at a local model. That is where the most interesting open work is: documenting which patterns survive tool-calling degradation on smaller open-weight models and which need structured output guards to function reliably. You do not need a GPU server — a MacBook M-series or an Intel NUC will run the lightweight Ollama models for most patterns.

**AI architects and researchers.** The eight patterns here are a controlled experiment: same environment, same tools, same incident, eight different reasoning architectures. The Reflexion–ReWOO comparison alone (728s with iterative safety checks vs. 65s with a static plan) is a data point worth reproducing on a different model, a different domain, or a different incident class. Run the comparison, document what changes, and open an issue with the findings.

### Specific asks (mapped to Phase 2)

- **Test any pattern on a local Ollama model** and open an issue documenting where it succeeds and where tool-calling breaks — this is the highest-value contribution for Phase 2 work
- **Validate the operational scenario** against real blue-light or NHS knowledge — file corrections as GitHub Issues; domain accuracy matters more than code cleanliness here
- **Implement `shared/audit.py`** — a SQLite-backed audit logger for `dispatch_resource` and `request_human_approval` calls with timestamp and approval status (Phase 2, Section 5)
- **Add a Care Act 2014 domain scenario** alongside the 999 fire scenario — safeguarding referral, mental health crisis, CRHT team dispatch (Phase 2, Section 4)
- **Write `docs/sovereign_setup.md`** — a reproducible Ollama deployment recipe for air-gapped or resource-constrained environments (Phase 2, Section 3)
- **Translate the scenario to another jurisdiction** (AUS Triple Zero, EU 112, US 911) and open a PR — the shared environment model is jurisdiction-agnostic by design

### How to engage

Everything goes through **[GitHub Issues](https://github.com/JigsawFlux/agentic-patterns/issues)** — for bugs, domain feedback, feature proposals, and collaboration. There is no Slack, no Discord, no mailing list. Open an issue and we will go from there.

---

## ⚠️ Ethics, Safety & Limitations

> **This is a research simulator. It must never be used in or connected to a live production dispatch, NHS operational system, or any clinical decision interface.**

### Fictional Scenario Disclaimer

All scenario data in this repository is deliberately fictional with no connection to real events, addresses, people, or NHS operational data:

- **Address:** "14 Kingsbourne Terrace, WC1B 9ZZ" — the street name is invented; the `ZZ` postcode suffix is unassigned in the Royal Mail system.
- **NHS Trust names:** All trust names (e.g. "Northgate University Hospital NHS Foundation Trust", "St. Aldric's General Hospital NHS Foundation Trust") are invented. Any resemblance to real NHS organisations is coincidental.
- **Incident data:** The scenario is a fictional construction for research and educational purposes only.

### Limitations of the MVP

1. **No real dispatch capability.** The tools in `shared/tools.py` operate on an in-memory mock database. They cannot and do not connect to any real emergency dispatch system, CAD (Computer Aided Dispatch) software, or NHS database.
2. **LLM hallucination risk.** In high-stress or unusual incident variants, language models may produce plausible-sounding but clinically or operationally incorrect outputs — wrong hospital routing, incorrect resource counts, fabricated protocol references. All outputs must be reviewed by qualified professionals before any real-world use.
3. **No persistent audit trail.** The current dispatch log is in-memory and resets between runs. This makes the MVP unsuitable for any real duty-of-care, compliance, or accountability purpose.
4. **No PII handling.** The system does not redact personally identifiable information from prompts before sending them to hosted model APIs. Do not input real patient data, real addresses, or real operational information.
5. **Non-deterministic outputs.** The same incident may produce different dispatch decisions across runs due to LLM temperature settings and model version changes.

### Humanitarian Intent

This project exists to help product owners, solution architects, and engineering teams understand the trade-offs between agentic architectures in high-stakes, duty-of-care domains — where the choice of pattern has direct implications for auditability, protocol compliance, and human oversight. It is a learning resource, not a product.

---

## 📌 Appendix: Roadmap / Gap Analysis

> **Phase 1 (this repository)** proves that all 8 architectural patterns work end-to-end against a UK-aligned NHS emergency scenario, using Anthropic Claude, with an LLM factory for provider abstraction, per-run telemetry, and a human-in-the-loop gate.
>
> **Phase 2 (upcoming)** will prove that these patterns remain viable and safe on **sovereign / low-cost hardware** (local Ollama models, air-gapped environments) and in a **genuine clinical triage domain** (Care Act 2014, mental health crisis response) with a persistent audit trail that meets duty-of-care compliance requirements.

---

### ✅ Phase 1 — Completed

---

### 1. Provider abstraction (break the Anthropic lock-in)
* **Checklist**:
  - [x] Introduce a `shared/llm.py` factory that returns a chat model based on an `LLM_PROVIDER` env var (`anthropic`, `ollama`, `bedrock`, etc.), instead of each `patterns/*.py` file hardcoding `ChatAnthropic`.
  - [x] Update `.env.example` with `LLM_PROVIDER`, `OLLAMA_MODEL`, `OLLAMA_BASE_URL` options.
  - [x] Refactor all 8 pattern files to use the factory instead of instantiating `ChatAnthropic` directly.

* **Analysis**:
  - **Current State**: ✅ `shared/llm.py` exists and all 8 pattern files use `get_llm()`. Switching providers requires only a `.env` change.
  - **Original Problem**: All 8 pattern files previously imported `ChatAnthropic` directly — switching LLM providers required editing every file.
  - **Solution Implemented**: [llm.py](shared/llm.py) acts as an LLM Factory:
    ```python
    import os
    from langchain_core.language_models.chat_models import BaseChatModel

    def get_llm(temperature: float = 0.1) -> BaseChatModel:
        provider = os.environ.get("LLM_PROVIDER", "anthropic").lower()
        if provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model=os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6"),
                anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY"),
                temperature=temperature
            )
        elif provider == "ollama":
            from langchain_ollama import ChatOllama
            return ChatOllama(
                model=os.environ.get("OLLAMA_MODEL", "llama3.1"),
                base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
                temperature=temperature
            )
        # Add Bedrock, Azure, etc. as needed
    ```
    Then, replace the imports and helper functions in all `patterns/*.py` files to use `get_llm(temperature=...)`.

---

### 2. Cost & resource telemetry
* **Checklist**:
  - [x] Capture token usage (input/output) per LLM call and per pattern run.
  - [x] Add estimated $ cost per run (model-price-aware) to the comparison table in `run.py`.
  - [x] Add wall-clock latency per LLM call (not just total pattern time) to help compare local vs. hosted models.

* **Analysis**:
  - **Current State**: ✅ `shared/telemetry.py` (`TelemetryCallback`) captures input/output tokens, LLM call count, wall-clock latency per call, and estimated cost. `run.py` displays these alongside report size and step count in the final comparison table.
  - **Original Problem**: `run.py` only tracked total elapsed time, making expensive recursive patterns (Reflexion, Plan-and-Execute) look comparable to token-efficient batch patterns (ReWOO).
  - **Solution Implemented**: Custom LangChain `BaseCallbackHandler` in [telemetry.py](shared/telemetry.py) using `on_llm_start`/`on_llm_end` hooks. Pricing hardcoded for Sonnet 4.6 ($3/M input, $15/M output); Ollama runs at $0.00.

---

---

### 🔜 Phase 2 — Upcoming

> The Phase 2 goal is to answer: *"Do these patterns hold up outside a paid frontier model, outside a controlled demo domain, and under real audit requirements?"*  Three workstreams:
> 1. **Sovereignty** — run all 8 patterns on local Ollama models; document where tool-calling degrades and which patterns survive.
> 2. **Clinical domain depth** — extend the simulation beyond 999 fire/medical/police into Care Act 2014 triage (safeguarding, mental health crisis) where the stakes and terminology are materially different.
> 3. **Audit & governance** — replace the in-memory dispatch log with a persistent audit trail; log every HITL approval/bypass with timestamp.

---

### 3. Local / sovereign model proof point
* **Checklist**:
  - [ ] Run each pattern against a local Ollama model (e.g. Llama 3.1 8B, Qwen2.5) on the same incident used for the Claude runs.
  - [ ] Publish a side-by-side comparison: accuracy/safety pass-rate vs. cost vs. latency, Claude vs. local model.
  - [ ] Document a reproducible "sovereign deployment" recipe (Ollama install, model pull, air-gapped run instructions).

* **Analysis**:
  - **Current State**: The repository does not include instructions, files, or verification profiles for local execution.
  - **Critique**: Running agentic loops locally using open-weights models (like `Llama-3.1-8B` or `Qwen2.5-14B` via Ollama) presents a major challenge: Tool-calling capabilities are highly unstable compared to Claude 3.5 Sonnet. Patterns like *ReAct* and *Plan-and-Execute* will frequently fail if the model outputs malformed JSON for tool invocation arguments. Structured patterns like *ReWOO* (which isolates planning from execution) or *Reflexion* (which has a self-correcting critique loop) are actually much more resilient for smaller local models.
  - **Transition/Alignment Strategy**:
    - Add a `docs/sovereign_setup.md` explaining how to download Ollama, fetch models, and spin up the service.
    - Provide fallback system prompts (specifically in [rewoo.py](patterns/rewoo.py) and [consensus.py](patterns/consensus.py)) that enforce JSON formatting using regular expressions or LangChain's `.with_structured_output` if a local model fails JSON constraints.

---

### 4. Domain model aligned to UK health / duty-of-care
* **Checklist**:
  - [x] Replace the generic fire/police/hospital dispatch simulation with UK-relevant terminology: UK vehicle names (Pumping Appliance, Double-Crewed Ambulance, HART Team, Roads Policing Unit, etc.), fictional NHS trust names, OPEL levels, NEWS2 scoring, and a fictional London WC1B address.
  - [ ] Extend domain further to safeguarding referral triage, mental health crisis response, or adult social care duty desk (Care Act 2014 pathways). *(Deferred — Phase 2)*

* **Analysis**:
  - **Current State (Phase 1 — done)**: ✅ `environment.py` now models UK Fire/Medical/Police vehicle types (Pumping Appliance, Double-Crewed Ambulance, HART Team, Roads Policing Unit, etc.), fictional NHS trusts with OPEL levels and burns unit beds, and fictional London WC1B geography. `tools.py` includes `check_opel_level` and `assess_news2_score` tools. All 8 pattern outputs now reference "14 Kingsbourne Terrace, WC1B 9ZZ" and NHS trust names throughout.
  - **Phase 2 extension**: The emergency services domain is a starting point. Real NHS duty-of-care decisions (safeguarding referrals, mental health crisis response, adult social care) involve fundamentally different pathways:
    - **Responders**: Crisis Resolution and Home Treatment (CRHT) Teams, Approved Mental Health Professionals (AMHPs), Duty Social Workers, Rapid Response Nurses.
    - **Decision frameworks**: Care Act 2014 Section 42 safeguarding thresholds, mental health triage (MHA 1983 sections), and NHS Talking Therapies referral pathways — not fire suppression protocols.
    - This extension is intentionally deferred to Phase 2 to keep the MVP focused and comparable.

---

### 5. Safety & governance harness
* **Checklist**:
  - [ ] Persist the dispatch/decision log to durable storage (file or SQLite) instead of the in-memory `dispatched_log`, so audit trails survive a run.
  - [ ] Record human-in-the-loop approvals (or `--auto-approve` bypasses) with identity/timestamp in the audit log, rather than silently skipping.
  - [ ] Add a documented data-handling/PII stance given the health-adjacent domain.

* **Analysis**:
  - **Current State**: The dispatch log is an in-memory list (`self.dispatched_log`) that resets every time a run begins. The human-in-the-loop (HITL) prompt is a standard CLI blocking input that does not persist its decisions.
  - **Critique**: In high-stakes duty-of-care settings, an ephemeral log is a compliance hazard. Every action, LLM reasoning trace, and human override must be written to an immutable audit record.
  - **Transition/Alignment Strategy**:
    - Set up a lightweight SQLite database (`shared/audit.db`) or write JSON Lines files to `outputs/audit_log.jsonl`.
    - Ensure the `dispatch_resource` and `request_human_approval` tools write directly to this persistent database.
    - Include a metadata schema representing who approved the bypass (e.g., timestamp, machine hostname, prompt arguments, and approval status).
    - **PII/GDPR Mitigation**: Create a basic de-identification pre-processor inside the LLM factory that redacts potential UK postcodes (e.g. SW1A 1AA) and names from the prompt before sending it to public endpoints (Anthropic/OpenAI), and resolves them back locally.

---

### 6. Open-source hygiene
* **Checklist**:
  - [x] Add a `LICENSE` file (MIT) at the repo root — includes a safety disclaimer prohibiting connection to live production dispatch or clinical systems.
  - [x] Add an "Ethics & Safety" section to this README describing the humanitarian intent, data-handling stance, and limitations of this MVP.

* **Analysis**:
  - **Current State**: The repository is missing a legal license and an ethics policy.
  - **Critique**: Because this project demonstrates automated/autonomous dispatch software in medical and policing fields, it is critical to explicitly limit liability.
  - **Transition/Alignment Strategy**:
    - Add a standard LICENSE file (Apache-2.0 or MIT is recommended for open-source utility).
    - Update [README.md](README.md) with an Ethics, Limitations & Safety Declaration:
      - Clarify that the project is an experimental simulator and must never be connected to a live production dispatch or clinical decision interface.
      - Warn about hallucinations in LLM tool selection under extreme crisis variations.

---

## ⚡ Actionable Checklist to Align Workspace

If the decision is to execute on any of these roadmaps later, here is the sequence of tasks you should follow:

| Step | Goal / Phase | Action Items | Status |
| :--- | :--- | :--- | :--- |
| **Step 1** | **Abstraction** | Implement `shared/llm.py` factory and refactor the 8 files under `patterns/`. | ✅ Completed |
| **Step 2** | **Telemetry** | Write the LangChain callback handler in `shared/telemetry.py` and hook it into `run.py`. | ✅ Completed |
| **Step 3** | **Local Setup** | Download Ollama, run `llama3.1` or `qwen2.5`, test the topologies, and optimize prompt parsing errors. | ✅ Completed (Verified on Intel NUC) |
| **Step 4** | **Domain Alignment** | UK vehicle names, fictional NHS trusts, OPEL levels, NEWS2 scoring, fictional WC1B address. | ✅ Completed (Phase 1 — emergency services domain) |
| **Step 5** | **Governance** | Replace the in-memory log with a persistent SQLite audit logger and implement a local PII regex redactor. | ⏳ Pending (Phase 2) |
| **Step 6** | **Hygiene** | Add the LICENSE file and Ethics & Safety section to README.md. | ✅ Completed |
