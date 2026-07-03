# patterns/plan_execute.py
import json
from typing import TypedDict, List, Tuple, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from shared.llm import get_llm

from shared.tools import (
    check_responder_availability,
    query_hospital_status,
    check_weather_and_traffic_hazards,
    dispatch_resource
)

# Define State Schema
class PlanExecuteState(TypedDict):
    incident: str
    plan: List[str]
    past_steps: List[Tuple[str, str]]
    final_report: str


# 1. Planner Node: Generates the initial plan
def planner_node(state: PlanExecuteState):
    print("\n[Plan & Execute] 📋 Planning Phase: Generating step-by-step response plan...")
    model = get_llm()
    
    prompt = (
        f"You are a Tactical Emergency Dispatch Planner. Given the incident below, outline a step-by-step dispatch plan.\n"
        f"Incident: {state['incident']}\n\n"
        "Your plan must be a JSON array of strings, where each string is a single discrete task (e.g., 'Check fire responder availability').\n"
        "Do not include explanation text, return ONLY valid JSON array format, e.g.:\n"
        '["Step 1: Check Fire and Police availability", "Step 2: Check road hazards near location", "Step 3: Dispatch 2 Fire Engines"]'
    )
    
    response = model.invoke([
        SystemMessage(content="You are a precise tactical planner. Reply ONLY with a JSON array of steps."),
        HumanMessage(content=prompt)
    ])
    
    content = response.content.strip()
    # Strip markdown code blocks if any
    if content.startswith("```json"):
        content = content.replace("```json", "").replace("```", "").strip()
    elif content.startswith("```"):
        content = content.replace("```", "").strip()
        
    try:
        plan = json.loads(content)
    except Exception as e:
        print(f"[Plan & Execute Warning] Failed to parse plan JSON. Using default fallback. Error: {e}")
        plan = [
            "Step 1: Check responder availability (Fire, Medical, Police)",
            "Step 2: Check location hazards and delays",
            "Step 3: Query hospital status",
            "Step 4: Dispatch emergency vehicles",
            "Step 5: Write final deployment report"
        ]
        
    print(f"[Plan & Execute] Plan generated with {len(plan)} steps.")
    for i, step in enumerate(plan, 1):
        print(f"  {i}. {step}")
        
    return {"plan": plan, "past_steps": []}

# 2. Executor Node: Runs the current step in the plan using tools
def executor_node(state: PlanExecuteState):
    current_step = state["plan"][0]
    print(f"\n[Plan & Execute] ⚡ Execution Phase: Executing task: '{current_step}'")
    
    model = get_llm()
    tools = [
        check_responder_availability,
        query_hospital_status,
        check_weather_and_traffic_hazards,
        dispatch_resource
    ]
    model_with_tools = model.bind_tools(tools)
    
    # We provide the executor with the context of what was done so far
    history_str = "\n".join([f"Task: {step}\nOutcome: {outcome}" for step, outcome in state["past_steps"]])
    
    prompt = (
        f"Incident: {state['incident']}\n\n"
        f"Completed Tasks & Outcomes:\n{history_str if history_str else 'None'}\n\n"
        f"Your Current Task: {current_step}\n\n"
        "Execute this task using the appropriate tool. If you need to make a tool call, do so.\n"
        "If you do not need to call a tool to complete this task, summarize the result or answer."
    )
    
    # Run a simple single-turn or tool execution call
    messages = [
        SystemMessage(content="You are an Emergency Dispatch Executor. Use your tools to perform the task requested."),
        HumanMessage(content=prompt)
    ]
    
    response = model_with_tools.invoke(messages)
    
    # If the model requested tool calls, we execute them and return the results
    if response.tool_calls:
        # Run tool executions
        outcomes = []
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            print(f"[Plan & Execute] Calling tool '{tool_name}' with args: {tool_args}")
            
            # Map tool names to actual functions
            tool_map = {
                "check_responder_availability": check_responder_availability,
                "query_hospital_status": query_hospital_status,
                "check_weather_and_traffic_hazards": check_weather_and_traffic_hazards,
                "dispatch_resource": dispatch_resource
            }
            
            if tool_name in tool_map:
                try:
                    tool_output = tool_map[tool_name].invoke(tool_args)
                    outcomes.append(f"Tool {tool_name} returned: {tool_output}")
                except Exception as e:
                    outcomes.append(f"Tool {tool_name} failed: {str(e)}")
            else:
                outcomes.append(f"Tool {tool_name} is unknown.")
        
        outcome = "\n".join(outcomes)
    else:
        outcome = response.content
        
    print(f"[Plan & Execute] Outcome: {outcome.strip()}")
    
    return {
        "plan": state["plan"][1:],  # Remove executed step
        "past_steps": state["past_steps"] + [(current_step, outcome)]
    }

# 3. Replanner Node: Decides whether to update the remaining plan or finish
def replanner_node(state: PlanExecuteState):
    # If there are no more steps, compile final report
    if not state["plan"]:
        print("\n[Plan & Execute] 🔄 Replanning Phase: No tasks remaining. Drafting final report...")
        return {"final_report": "complete"}
    
    print("\n[Plan & Execute] 🔄 Replanning Phase: Reviewing progress and updating plan...")
    model = get_llm()
    
    history_str = "\n".join([f"Task: {step}\nOutcome: {outcome}" for step, outcome in state["past_steps"]])
    plan_str = "\n".join([f"- {step}" for step in state["plan"]])
    
    prompt = (
        f"Incident: {state['incident']}\n\n"
        f"History of executed tasks and outcomes:\n{history_str}\n\n"
        f"Current remaining plan:\n{plan_str}\n\n"
        "Assess whether the remaining plan is still correct. If there is a change in the environment "
        "(e.g. a resource is unavailable, or a hazard was discovered), you may update the remaining plan.\n"
        "Output the final remaining plan as a JSON array of strings. If no changes are needed, "
        "output the current remaining plan as is in JSON format.\n"
        "Return ONLY the JSON array (no explanation)."
    )
    
    response = model.invoke([
        SystemMessage(content="You are a Plan Evaluator. Output ONLY a valid JSON list of remaining steps."),
        HumanMessage(content=prompt)
    ])
    
    content = response.content.strip()
    if content.startswith("```json"):
        content = content.replace("```json", "").replace("```", "").strip()
    elif content.startswith("```"):
        content = content.replace("```", "").strip()
        
    try:
        new_plan = json.loads(content)
        print(f"[Plan & Execute] Plan updated. {len(new_plan)} steps remaining.")
        return {"plan": new_plan}
    except Exception as e:
        print(f"[Plan & Execute Warning] Replanner failed to parse JSON: {e}. Keeping current remaining plan.")
        return {"plan": state["plan"]}

# Route to end or execution
def should_continue(state: PlanExecuteState):
    if state.get("final_report") == "complete":
        return "synthesizer"
    return "executor"

# 4. Synthesizer Node: Produces the final deployment summary
def synthesizer_node(state: PlanExecuteState):
    print("\n[Plan & Execute] ✍️ Synthesizer Phase: Drafting final deployment report...")
    model = get_llm()
    
    history_str = "\n".join([f"Task: {step}\nOutcome: {outcome}" for step, outcome in state["past_steps"]])
    
    prompt = (
        f"Incident: {state['incident']}\n\n"
        f"Summary of Actions and Tool Outputs:\n{history_str}\n\n"
        "Draft a highly professional, structured Markdown report detailing the emergency response deployment.\n"
        "Include the incident overview, specific responder assets dispatched, hospital triage routing, "
        "hazard management, and final operational directions."
    )
    
    response = model.invoke([
        SystemMessage(content="You are a Chief Emergency Coordinator. Summarize the response deployment."),
        HumanMessage(content=prompt)
    ])
    
    return {"final_report": response.content}

# Compile Graph
def build_plan_execute_graph():
    workflow = StateGraph(PlanExecuteState)
    
    workflow.add_node("planner", planner_node)
    workflow.add_node("executor", executor_node)
    workflow.add_node("replanner", replanner_node)
    workflow.add_node("synthesizer", synthesizer_node)
    
    workflow.add_edge(START, "planner")
    workflow.add_edge("planner", "executor")
    workflow.add_edge("executor", "replanner")
    
    workflow.add_conditional_edges(
        "replanner",
        should_continue,
        {
            "executor": "executor",
            "synthesizer": "synthesizer"
        }
    )
    workflow.add_edge("synthesizer", END)
    
    return workflow.compile()

def run_pattern(incident: str) -> dict:
    print(f"\n{'='*20} RUNNING SINGLE-AGENT: PLAN-AND-EXECUTE {'='*20}")
    
    app = build_plan_execute_graph()
    
    result = app.invoke({
        "incident": incident,
        "plan": [],
        "past_steps": [],
        "final_report": ""
    })
    
    return {
        "pattern": "Plan-and-Execute",
        "final_report": result["final_report"],
        "history": [f"Step: {step}\nResult: {res}" for step, res in result["past_steps"]]
    }
