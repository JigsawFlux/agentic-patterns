# patterns/dag.py
import os
import json
from typing import TypedDict, List
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, START, END

from shared.tools import (
    check_responder_availability,
    query_hospital_status,
    check_weather_and_traffic_hazards,
    dispatch_resource
)

# Define State Schema
class DAGState(TypedDict):
    incident: str
    triage_report: str
    dispatch_report: str
    traffic_report: str
    final_report: str

def get_model(temperature=0.1):
    return ChatAnthropic(
        model=os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6"),
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY"),
        temperature=temperature
    )

# 1. Triage Agent Node: Classifies incident and pulls out key metrics
def triage_agent_node(state: DAGState):
    print("\n[DAG Pipeline] 📋 1. Triage Agent: Parsing incident metrics...")
    model = get_model()
    
    prompt = (
        f"Incident Description:\n{state['incident']}\n\n"
        "Identify and format the following information in a structured note:\n"
        "- Severity Level (Low, Medium, High, Critical)\n"
        "- Primary Incidents (e.g. Fire, Medical Trauma, Gas Leak)\n"
        "- Location / Area\n"
        "- Casualties / Injuries reported (Yes/No and count if known)"
    )
    
    response = model.invoke([
        SystemMessage(content="You are an Emergency Triage Specialist. Extract key operational details from incoming calls."),
        HumanMessage(content=prompt)
    ])
    
    report = response.content.strip()
    print(f"[DAG Pipeline] Triage Report:\n{report}")
    return {"triage_report": report}

# 2. Resource Allocator Agent Node: Manages responder allocations and hospital selection
def resource_allocator_node(state: DAGState):
    print("\n[DAG Pipeline] 🚑 2. Resource Allocator: Allocating responders & hospitals...")
    model = get_model()
    tools = [check_responder_availability, query_hospital_status, dispatch_resource]
    model_with_tools = model.bind_tools(tools)
    
    prompt = (
        f"Incident: {state['incident']}\n\n"
        f"Triage Report:\n{state['triage_report']}\n\n"
        "Based on the triage report, check availability for Fire and Medical responders. "
        "Check hospital status. Dispatch the appropriate units (Fire Engine, Ambulances) and select the best hospital "
        "if there are injuries. Summarize the allocations made."
    )
    
    response = model_with_tools.invoke([
        SystemMessage(content="You are the Resource Allocator. Check availability and dispatch responders."),
        HumanMessage(content=prompt)
    ])
    
    log = ""
    if response.tool_calls:
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            print(f"[Resource Allocator] Calling tool '{tool_name}' with args: {tool_args}")
            
            tool_map = {
                "check_responder_availability": check_responder_availability,
                "query_hospital_status": query_hospital_status,
                "dispatch_resource": dispatch_resource
            }
            if tool_name in tool_map:
                try:
                    res = tool_map[tool_name].invoke(tool_args)
                    log += f"- Called {tool_name}({tool_args}): {res}\n"
                except Exception as e:
                    log += f"- Failed {tool_name}({tool_args}): {e}\n"
                    
        summarizer = model.invoke([
            SystemMessage(content="You are the Resource Allocator. Summarize your allocations."),
            HumanMessage(content=f"{prompt}\n\nActions Taken:\n{log}")
        ])
        summary = summarizer.content
    else:
        summary = response.content
        
    print(f"[DAG Pipeline] Resource Allocations:\n{summary}")
    return {"dispatch_report": summary}

# 3. Traffic Coordinator Agent Node: Checks routing delays and dispatches police units
def traffic_coordinator_node(state: DAGState):
    print("\n[DAG Pipeline] 👮 3. Traffic Coordinator: Checking roads & dispatching police...")
    model = get_model()
    tools = [check_responder_availability, check_weather_and_traffic_hazards, dispatch_resource]
    model_with_tools = model.bind_tools(tools)
    
    prompt = (
        f"Incident: {state['incident']}\n\n"
        f"Triage Report:\n{state['triage_report']}\n\n"
        f"Dispatch Report:\n{state['dispatch_report']}\n\n"
        "Check weather and traffic hazards for the incident location. "
        "Check availability and dispatch Police cruisers or Traffic Units to establish road blocks, "
        "evacuation routes, or traffic control to assist responders. Summarize your findings and actions."
    )
    
    response = model_with_tools.invoke([
        SystemMessage(content="You are the Traffic Coordinator. Check hazards and dispatch police cruisers."),
        HumanMessage(content=prompt)
    ])
    
    log = ""
    if response.tool_calls:
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            print(f"[Traffic Coordinator] Calling tool '{tool_name}' with args: {tool_args}")
            
            tool_map = {
                "check_responder_availability": check_responder_availability,
                "check_weather_and_traffic_hazards": check_weather_and_traffic_hazards,
                "dispatch_resource": dispatch_resource
            }
            if tool_name in tool_map:
                try:
                    res = tool_map[tool_name].invoke(tool_args)
                    log += f"- Called {tool_name}({tool_args}): {res}\n"
                except Exception as e:
                    log += f"- Failed {tool_name}({tool_args}): {e}\n"
                    
        summarizer = model.invoke([
            SystemMessage(content="You are the Traffic Coordinator. Summarize your actions."),
            HumanMessage(content=f"{prompt}\n\nActions Taken:\n{log}")
        ])
        summary = summarizer.content
    else:
        summary = response.content
        
    print(f"[DAG Pipeline] Traffic Coordination:\n{summary}")
    return {"traffic_report": summary}

# 4. Synthesizer Agent Node: Compiles the final report from the DAG pipeline
def synthesizer_node(state: DAGState):
    print("\n[DAG Pipeline] ✍️ 4. Synthesizer: Merging pipeline data into final dispatch report...")
    model = get_model(temperature=0.3)
    
    prompt = (
        f"Incident: {state['incident']}\n\n"
        f"Triage Stage Details:\n{state['triage_report']}\n\n"
        f"Resource Stage Details:\n{state['dispatch_report']}\n\n"
        f"Traffic Stage Details:\n{state['traffic_report']}\n\n"
        "Draft the official, master Emergency Dispatch Summary in Markdown. "
        "Organize the sections logically following the pipeline stages: Incident Triage, Responder Dispatches, "
        "and Traffic / Routing Advisories."
    )
    
    response = model.invoke([
        SystemMessage(content="You are the Chief Coordinator. Present the pipeline summary report."),
        HumanMessage(content=prompt)
    ])
    
    return {"final_report": response.content}

# Compile Graph
def build_dag_graph():
    workflow = StateGraph(DAGState)
    
    workflow.add_node("triage", triage_agent_node)
    workflow.add_node("allocator", resource_allocator_node)
    workflow.add_node("traffic", traffic_coordinator_node)
    workflow.add_node("synthesizer", synthesizer_node)
    
    workflow.add_edge(START, "triage")
    workflow.add_edge("triage", "allocator")
    workflow.add_edge("allocator", "traffic")
    workflow.add_edge("traffic", "synthesizer")
    workflow.add_edge("synthesizer", END)
    
    return workflow.compile()

def run_pattern(incident: str) -> dict:
    print(f"\n{'='*20} RUNNING MULTI-AGENT: DAG PIPELINE {'='*20}")
    
    app = build_dag_graph()
    
    result = app.invoke({
        "incident": incident,
        "triage_report": "",
        "dispatch_report": "",
        "traffic_report": "",
        "final_report": ""
    })
    
    return {
        "pattern": "Acyclic/DAG",
        "final_report": result["final_report"],
        "history": [
            f"Triage: {result['triage_report']}",
            f"Allocations: {result['dispatch_report']}",
            f"Traffic: {result['traffic_report']}"
        ]
    }
