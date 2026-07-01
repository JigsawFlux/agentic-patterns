# Agentic Patterns: Emergency Response & Disaster Dispatch

This repository implements, demonstrates, and compares **8 core agentic patterns** (4 single-agent patterns and 4 multi-agent topologies) using **LangGraph** and **Anthropic Claude**. 

Each pattern coordinates resources (Fire, Medical, Police) in a stateful mock environment simulating critical incident dispatching.

---

## 🗺️ Architectural Patterns Implemented

### Single-Agent Patterns
1. **ReAct (Reason + Act)**: A single agent that incrementally loops between reasoning and tool invocation (`patterns/react.py`).
2. **Plan-and-Execute**: A planner agent generates a sequence of steps; an executor runs them, and a replanner reviews and adapts the plan as events unfold (`patterns/plan_execute.py`).
3. **ReWOO (Reason Without Observation)**: An agent plans the entire chain of tool calls upfront with placeholder variables. The executor resolves them without intermediate LLM invocations, making it highly token-efficient (`patterns/rewoo.py`).
4. **Reflexion**: A generator agent proposes a dispatch plan, which a critic agent evaluates against strict protocols. The plan is iteratively refined based on critique until it passes safety checks (`patterns/reflexion.py`).

### Multi-Agent Topologies
5. **Hierarchical**: An Incident Commander (Supervisor) coordinates the operation by delegating specific issues to specialized Fire, Medical, and Police sub-agents who execute tools and report back (`patterns/hierarchical.py`).
6. **Acyclic / DAG**: A unidirectional pipeline of specialized agents (Triage ──► Resource Allocation ──► Traffic Coordinator ──► Compiler) without loops (`patterns/dag.py`).
7. **Network (Peer-to-Peer)**: Specialized agents (Fire Chief, Police Chief, Medical Chief) negotiate coordinates and assets laterally in a conversational loop without central orchestrator oversight (`patterns/network.py`).
8. **Consensus / Joint**: Three independent experts (Threat Analyst, Resource Chief, Public Safety Liaison) evaluate risk severity and debate their scores until they reach consensus or average agreement (`patterns/consensus.py`).

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

* [`shared/environment.py`](shared/environment.py) — Stateful database representing responders (vehicles availability), hospitals (specialties and beds), hazards, and a dispatch logger.
* [`shared/tools.py`](shared/tools.py) — LangChain-decorated tools (`dispatch_resource`, `query_hospital_status`, etc.) acting on the stateful database.
* [`patterns/`](patterns/) — Individual pattern graph definitions in LangGraph.
* [`run.py`](run.py) — Main command-line orchestrator and telemetry logger.
