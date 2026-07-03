# patterns/hierarchical.py
import json
from typing import TypedDict, List, Annotated
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
class HierarchicalState(TypedDict):
    incident: str
    next_agent: str
    transcript: List[str]
    final_report: str


# 1. Supervisor Node: Orchestrates and routes to specialists
def supervisor_node(state: HierarchicalState):
    print("\n[Hierarchical] 👑 Supervisor Node: Analyzing state and routing task...")
    model = get_llm()
    
    transcript_str = "\n".join(state.get("transcript", []))
    
    prompt = (
        f"Incident: {state['incident']}\n\n"
        f"Operational History so far:\n{transcript_str if transcript_str else 'None'}\n\n"
        "You are the Incident Commander. Direct the next action. Choose from:\n"
        "- 'Fire': If fire, hazmat containment, or building collapse needs assessment or dispatch.\n"
        "- 'Medical': If injuries, burns, or casualties need hospital routing or paramedic dispatch.\n"
        "- 'Police': If traffic blocks, evacuations, or crowd control need management.\n"
        "- 'FINISH': If all departments have reported, dispatched resources, and the incident is fully resolved.\n\n"
        "Respond ONLY with one of the words: 'Fire', 'Medical', 'Police', or 'FINISH'."
    )
    
    response = model.invoke([
        SystemMessage(content="You are a strict emergency coordinator. Respond ONLY with Fire, Medical, Police, or FINISH."),
        HumanMessage(content=prompt)
    ])
    
    next_agent = response.content.strip().replace("'", "").replace('"', "")
    valid_agents = ["Fire", "Medical", "Police", "FINISH"]
    if next_agent not in valid_agents:
        # Fallback if LLM outputs prose
        for va in valid_agents:
            if va in next_agent:
                next_agent = va
                break
        else:
            next_agent = "FINISH"
            
    print(f"[Hierarchical] Supervisor chose next action: '{next_agent}'")
    return {"next_agent": next_agent}

# 2. Fire Specialist Node
def fire_specialist_node(state: HierarchicalState):
    print("\n[Hierarchical] 🔥 Fire Specialist: Managing fire/hazmat assets...")
    model = get_llm()
    tools = [check_responder_availability, dispatch_resource]
    model_with_tools = model.bind_tools(tools)
    
    prompt = (
        f"Incident: {state['incident']}\n\n"
        "You are the Fire Dispatch Specialist. Check Fire resource availability and dispatch necessary Pumping Appliances, "
        "Aerial Ladder Platforms, or Incident Response Units as required. "
        "Report your findings and actions back to the Incident Commander. Write a brief report of your actions."
    )
    
    response = model_with_tools.invoke([
        SystemMessage(content="You are the Fire Dispatch Specialist. Use tools to check availability and dispatch resources."),
        HumanMessage(content=prompt)
    ])
    
    # Simple tool execution run
    log = "[Fire Specialist] Activating Fire department.\n"
    if response.tool_calls:
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            print(f"[Fire Specialist] Calling tool '{tool_name}' with args: {tool_args}")
            
            tool_map = {
                "check_responder_availability": check_responder_availability,
                "dispatch_resource": dispatch_resource
            }
            if tool_name in tool_map:
                try:
                    res = tool_map[tool_name].invoke(tool_args)
                    log += f"- Called {tool_name}({tool_args}): {res}\n"
                except Exception as e:
                    log += f"- Failed {tool_name}({tool_args}): {e}\n"
        
        # Call model again to summarize action
        summarizer = model.invoke([
            SystemMessage(content="You are the Fire Specialist. Summarize your actions."),
            HumanMessage(content=f"{prompt}\n\nActions Taken:\n{log}")
        ])
        summary = summarizer.content
    else:
        summary = response.content
        
    print(f"[Fire Specialist] Complete. Summary: {summary[:150]}...")
    return {"transcript": state.get("transcript", []) + [f"--- Fire Dept Report ---\n{summary}"]}

# 3. Medical Specialist Node
def medical_specialist_node(state: HierarchicalState):
    print("\n[Hierarchical] 🚑 Medical Specialist: Managing hospital routing & ambulance dispatch...")
    model = get_llm()
    tools = [check_responder_availability, query_hospital_status, dispatch_resource]
    model_with_tools = model.bind_tools(tools)
    
    prompt = (
        f"Incident: {state['incident']}\n\n"
        "You are the Medical Dispatch Specialist. Query available hospitals and check Ambulance availability. "
        "Dispatch ambulances and route patients based on hospital specialties. Write a brief report of your actions."
    )
    
    response = model_with_tools.invoke([
        SystemMessage(content="You are the Medical Dispatch Specialist. Use tools to route patients and dispatch ambulances."),
        HumanMessage(content=prompt)
    ])
    
    log = "[Medical Specialist] Activating Medical department.\n"
    if response.tool_calls:
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            print(f"[Medical Specialist] Calling tool '{tool_name}' with args: {tool_args}")
            
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
            SystemMessage(content="You are the Medical Specialist. Summarize your actions."),
            HumanMessage(content=f"{prompt}\n\nActions Taken:\n{log}")
        ])
        summary = summarizer.content
    else:
        summary = response.content
        
    print(f"[Medical Specialist] Complete. Summary: {summary[:150]}...")
    return {"transcript": state.get("transcript", []) + [f"--- Medical Dept Report ---\n{summary}"]}

# 4. Police Specialist Node
def police_specialist_node(state: HierarchicalState):
    print("\n[Hierarchical] 👮 Police Specialist: Managing crowd control & road closures...")
    model = get_llm()
    tools = [check_responder_availability, check_weather_and_traffic_hazards, dispatch_resource]
    model_with_tools = model.bind_tools(tools)
    
    prompt = (
        f"Incident: {state['incident']}\n\n"
        "You are the Police Dispatch Specialist. Check Roads Policing Unit and Response Car availability, "
        "check for location traffic/hazards, and dispatch Roads Policing Units or Response Cars to manage traffic "
        "and evacuations. Write a brief report of your actions."
    )
    
    response = model_with_tools.invoke([
        SystemMessage(content="You are the Police Dispatch Specialist. Use tools to manage traffic closures."),
        HumanMessage(content=prompt)
    ])
    
    log = "[Police Specialist] Activating Police department.\n"
    if response.tool_calls:
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            print(f"[Police Specialist] Calling tool '{tool_name}' with args: {tool_args}")
            
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
            SystemMessage(content="You are the Police Specialist. Summarize your actions."),
            HumanMessage(content=f"{prompt}\n\nActions Taken:\n{log}")
        ])
        summary = summarizer.content
    else:
        summary = response.content
        
    print(f"[Police Specialist] Complete. Summary: {summary[:150]}...")
    return {"transcript": state.get("transcript", []) + [f"--- Police Dept Report ---\n{summary}"]}

# Conditional Router
def supervisor_router(state: HierarchicalState):
    next_agent = state.get("next_agent", "FINISH")
    if next_agent == "Fire":
        return "fire_specialist"
    elif next_agent == "Medical":
        return "medical_specialist"
    elif next_agent == "Police":
        return "police_specialist"
    else:
        return "synthesizer"

# Synthesizer Node
def synthesizer_node(state: HierarchicalState):
    print("\n[Hierarchical] ✍️ Synthesizer Phase: Merging department reports into a final master report...")
    model = get_llm(temperature=0.4)
    
    transcript_str = "\n\n".join(state["transcript"])
    
    prompt = (
        f"Incident: {state['incident']}\n\n"
        f"Department Actions & Reports:\n{transcript_str}\n\n"
        "Draft the official, master Emergency Dispatch and Operations Summary in Markdown. "
        "Make sure to group the response by department (Fire, Medical, Police) and include final dispatch figures, "
        "hospital destinations, routing delay alerts, and instructions to the command post."
    )
    
    response = model.invoke([
        SystemMessage(content="You are the Incident Commander. Present the final multi-department dispatch report."),
        HumanMessage(content=prompt)
    ])
    
    return {"final_report": response.content}

# Compile Graph
def build_hierarchical_graph():
    workflow = StateGraph(HierarchicalState)
    
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("fire_specialist", fire_specialist_node)
    workflow.add_node("medical_specialist", medical_specialist_node)
    workflow.add_node("police_specialist", police_specialist_node)
    workflow.add_node("synthesizer", synthesizer_node)
    
    workflow.add_edge(START, "supervisor")
    workflow.add_conditional_edges(
        "supervisor",
        supervisor_router,
        {
            "fire_specialist": "fire_specialist",
            "medical_specialist": "medical_specialist",
            "police_specialist": "police_specialist",
            "synthesizer": "synthesizer"
        }
    )
    # Loop specialists back to supervisor
    workflow.add_edge("fire_specialist", "supervisor")
    workflow.add_edge("medical_specialist", "supervisor")
    workflow.add_edge("police_specialist", "supervisor")
    workflow.add_edge("synthesizer", END)
    
    return workflow.compile()

def run_pattern(incident: str) -> dict:
    print(f"\n{'='*20} RUNNING MULTI-AGENT: HIERARCHICAL {'='*20}")
    
    app = build_hierarchical_graph()
    
    result = app.invoke({
        "incident": incident,
        "next_agent": "",
        "transcript": [],
        "final_report": ""
    })
    
    return {
        "pattern": "Hierarchical",
        "final_report": result["final_report"],
        "history": result["transcript"]
    }
