# patterns/rewoo.py
import json
import re
from typing import TypedDict, List, Dict, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from shared.llm import get_llm

from shared.tools import (
    check_responder_availability,
    query_hospital_status,
    check_weather_and_traffic_hazards,
    check_opel_level,
    assess_news2_score,
    dispatch_resource
)

# Define State Schema
class ReWOOState(TypedDict):
    incident: str
    plan_steps: List[Dict]
    tool_outputs: Dict[str, str]
    final_report: str


# 1. Planner Node: Creates the execution plan upfront without executing tools
def planner_node(state: ReWOOState):
    print("\n[ReWOO] 📋 Planner Phase: Designing entire execution plan upfront...")
    model = get_llm()
    
    prompt = (
        f"You are a Dispatch Planner. Create a tool execution plan to address this incident:\n"
        f"Incident: {state['incident']}\n\n"
        "Define all necessary tool calls upfront in a JSON list. Do NOT execute them. "
        "Use placeholder variables like '#E1' or '#E2' if you need the output of a prior step in a subsequent step's arguments, "
        "or write them out if you can anticipate them.\n\n"
        "Available tools:\n"
        "- check_responder_availability(service: str)  [service must be 'Fire', 'Medical', or 'Police']\n"
        "- query_hospital_status(hospital: str)        [hospital name or 'all']\n"
        "- check_opel_level(hospital_name: str)        [check NHS Operational Pressures Escalation Level]\n"
        "- assess_news2_score(patient_description: str)[NHS NEWS2 triage band for patient routing]\n"
        "- check_weather_and_traffic_hazards(location: str)\n"
        "- dispatch_resource(service: str, vehicle_type: str, units: int, location: str)\n\n"
        "UK vehicle types for dispatch_resource:\n"
        "  Fire: 'Pumping Appliance', 'Aerial Ladder Platform', 'Incident Response Unit'\n"
        "  Medical: 'Double-Crewed Ambulance', 'Rapid Response Vehicle', 'HART Team'\n"
        "  Police: 'Response Car', 'Roads Policing Unit', 'Armed Response Vehicle', 'Police Support Unit Van'\n\n"
        "Respond ONLY with a JSON array of steps in this format:\n"
        "[\n"
        "  {\n"
        '    "id": "E1",\n'
        '    "task": "Check availability of Fire responders",\n'
        '    "tool": "check_responder_availability",\n'
        '    "args": {"service": "Fire"}\n'
        "  },\n"
        "  {\n"
        '    "id": "E2",\n'
        '    "task": "Check traffic hazards on High Holborn",\n'
        '    "tool": "check_weather_and_traffic_hazards",\n'
        '    "args": {"location": "High Holborn"}\n'
        "  },\n"
        "  {\n"
        '    "id": "E3",\n'
        '    "task": "Dispatch Pumping Appliance to incident",\n'
        '    "tool": "dispatch_resource",\n'
        '    "args": {"service": "Fire", "vehicle_type": "Pumping Appliance", "units": 2, "location": "14 Kingsbourne Terrace, WC1B 9ZZ"}\n'
        "  }\n"
        "]\n"
        "Return ONLY the raw JSON array (no markdown code blocks, no explanation text)."
    )
    
    response = model.invoke([
        SystemMessage(content="You are a structured planning agent. Output ONLY a valid JSON list of execution steps."),
        HumanMessage(content=prompt)
    ])
    
    content = response.content.strip()
    if content.startswith("```json"):
        content = content.replace("```json", "").replace("```", "").strip()
    elif content.startswith("```"):
        content = content.replace("```", "").strip()
        
    try:
        plan_steps = json.loads(content)
    except Exception as e:
        print(f"[ReWOO Warning] Failed to parse JSON plan: {e}. Generating fallback plan.")
        plan_steps = [
            {
                "id": "E1",
                "task": "Check Fire availability",
                "tool": "check_responder_availability",
                "args": {"service": "Fire"}
            },
            {
                "id": "E2",
                "task": "Check Medical availability",
                "tool": "check_responder_availability",
                "args": {"service": "Medical"}
            },
            {
                "id": "E3",
                "task": "Query all hospital status",
                "tool": "query_hospital_status",
                "args": {"hospital": "all"}
            },
            {
                "id": "E4",
                "task": "Check hazards on High Holborn",
                "tool": "check_weather_and_traffic_hazards",
                "args": {"location": "High Holborn"}
            },
            {
                "id": "E5",
                "task": "Dispatch Pumping Appliances to incident",
                "tool": "dispatch_resource",
                "args": {"service": "Fire", "vehicle_type": "Pumping Appliance", "units": 2, "location": "14 Kingsbourne Terrace, WC1B 9ZZ"}
            },
            {
                "id": "E6",
                "task": "Dispatch Double-Crewed Ambulance to incident",
                "tool": "dispatch_resource",
                "args": {"service": "Medical", "vehicle_type": "Double-Crewed Ambulance", "units": 2, "location": "14 Kingsbourne Terrace, WC1B 9ZZ"}
            }
        ]
        
    print(f"[ReWOO] Formulated plan with {len(plan_steps)} steps.")
    for step in plan_steps:
        print(f"  [{step['id']}] {step['task']} -> {step['tool']}({step['args']})")
        
    return {"plan_steps": plan_steps, "tool_outputs": {}}

# 2. Executor Node: Executes the plans sequentially without intermediate LLM decisions.
# It resolves reference variables like #E1, #E2 if they are present in the arguments.
def executor_node(state: ReWOOState):
    print("\n[ReWOO] ⚡ Execution Phase: Running all tools in sequence...")
    outputs = {}
    
    # Tool map
    tool_map = {
        "check_responder_availability": check_responder_availability,
        "query_hospital_status": query_hospital_status,
        "check_weather_and_traffic_hazards": check_weather_and_traffic_hazards,
        "check_opel_level": check_opel_level,
        "assess_news2_score": assess_news2_score,
        "dispatch_resource": dispatch_resource
    }
    
    for step in state["plan_steps"]:
        step_id = step["id"]
        tool_name = step["tool"]
        args = step["args"]
        
        # Resolve variables (e.g. #E1) in arguments
        resolved_args = {}
        for k, v in args.items():
            if isinstance(v, str) and v.startswith("#"):
                ref_id = v[1:]
                if ref_id in outputs:
                    # Simple heuristic: insert the referenced output
                    resolved_args[k] = outputs[ref_id]
                else:
                    resolved_args[k] = v
            else:
                resolved_args[k] = v
                
        print(f"[ReWOO] Executing [{step_id}]: {tool_name}({resolved_args})")
        
        if tool_name in tool_map:
            try:
                output = tool_map[tool_name].invoke(resolved_args)
                outputs[step_id] = output
            except Exception as e:
                outputs[step_id] = f"Error executing tool: {str(e)}"
        else:
            outputs[step_id] = f"Error: Tool '{tool_name}' not found."
            
        print(f"  -> Result: {outputs[step_id].strip()}")
        
    return {"tool_outputs": outputs}

# 3. Solver Node: Takes plan and outputs to construct final response
def solver_node(state: ReWOOState):
    print("\n[ReWOO] ✍️ Solver Phase: Compiling final summary report...")
    model = get_llm()
    
    # Format the plan and execution results for the solver
    run_log = []
    for step in state["plan_steps"]:
        step_id = step["id"]
        task = step["task"]
        tool_name = step["tool"]
        args = step["args"]
        output = state["tool_outputs"].get(step_id, "No output")
        run_log.append(f"Step {step_id}: {task}\nTool Call: {tool_name}({args})\nOutput: {output}\n")
        
    log_str = "\n".join(run_log)
    
    prompt = (
        f"Incident: {state['incident']}\n\n"
        f"Execution Log:\n{log_str}\n\n"
        "Review the original incident and the results of all planned tool executions. "
        "Write a structured, final emergency response summary in Markdown. "
        "Clearly detail what resources were dispatched, to where, hospital selections, and hazard alerts."
    )
    
    response = model.invoke([
        SystemMessage(content="You are an Emergency Response Coordinator compiling a final operation report."),
        HumanMessage(content=prompt)
    ])
    
    return {"final_report": response.content}

# Compile Graph
def build_rewoo_graph():
    workflow = StateGraph(ReWOOState)
    
    workflow.add_node("planner", planner_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("solver", solver_node)
    
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "executor")
    workflow.add_edge("executor", "solver")
    workflow.add_edge("solver", END)
    
    return workflow.compile()

def run_pattern(incident: str) -> dict:
    print(f"\n{'='*20} RUNNING SINGLE-AGENT: REWOO {'='*20}")
    
    app = build_rewoo_graph()
    
    result = app.invoke({
        "incident": incident,
        "plan_steps": [],
        "tool_outputs": {},
        "final_report": ""
    })
    
    return {
        "pattern": "ReWOO",
        "final_report": result["final_report"],
        "history": [f"Step {step['id']} ({step['tool']}): {result['tool_outputs'].get(step['id'], 'N/A')}" for step in result["plan_steps"]]
    }
