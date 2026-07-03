# patterns/network.py
from typing import TypedDict, List
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
class NetworkState(TypedDict):
    incident: str
    discussion: List[str]
    round: int
    final_report: str


# 1. Fire Chief Agent Node
def fire_chief_node(state: NetworkState):
    print("\n[Network P2P] 🔥 Fire Chief: Proposing fire containment plan...")
    model = get_llm(temperature=0.3)
    tools = [check_responder_availability, dispatch_resource]
    model_with_tools = model.bind_tools(tools)
    
    discussion_str = "\n\n".join(state.get("discussion", []))
    
    prompt = (
        f"Incident: {state['incident']}\n\n"
        f"Prior Peer Discussion:\n{discussion_str if discussion_str else 'None'}\n\n"
        "You are the Fire Chief. Review the incident and the discussion. "
        "Check availability and dispatch Pumping Appliances, Aerial Ladder Platforms, or Incident Response Units. "
        "Write your assessment and actions directly to your peers (Police Chief, Medical Chief)."
    )
    
    response = model_with_tools.invoke([
        SystemMessage(content="You are the Fire Chief in a peer-to-peer coordination network."),
        HumanMessage(content=prompt)
    ])
    
    log = ""
    if response.tool_calls:
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            print(f"[Fire Chief] Calling tool '{tool_name}' with args: {tool_args}")
            
            tool_map = {
                "check_responder_availability": check_responder_availability,
                "dispatch_resource": dispatch_resource
            }
            if tool_name in tool_map:
                try:
                    res = tool_map[tool_name].invoke(tool_args)
                    log += f"- Dispatched: {res}\n"
                except Exception as e:
                    log += f"- Failed: {e}\n"
                    
        summarizer = model.invoke([
            SystemMessage(content="You are the Fire Chief. Address your peers with your final dispatch details."),
            HumanMessage(content=f"{prompt}\n\nActions Taken:\n{log}")
        ])
        statement = "Fire Chief: " + summarizer.content
    else:
        statement = "Fire Chief: " + response.content
        
    print(f"[Network P2P] Fire Chief statement posted.")
    return {
        "discussion": state.get("discussion", []) + [statement],
        "round": state.get("round", 0)
    }

# 2. Police Chief Agent Node
def police_chief_node(state: NetworkState):
    print("\n[Network P2P] 👮 Police Chief: Proposing traffic coordination plan...")
    model = get_llm(temperature=0.3)
    tools = [check_responder_availability, check_weather_and_traffic_hazards, dispatch_resource]
    model_with_tools = model.bind_tools(tools)
    
    discussion_str = "\n\n".join(state.get("discussion", []))
    
    prompt = (
        f"Incident: {state['incident']}\n\n"
        f"Prior Peer Discussion:\n{discussion_str}\n\n"
        "You are the Police Chief. Review the Fire Chief's plan and the incident. "
        "Check weather and traffic hazards at the site. Dispatch Roads Policing Units or Response Cars for road closures and route safety. "
        "Provide your inputs directly to the Fire and Medical Chiefs."
    )
    
    response = model_with_tools.invoke([
        SystemMessage(content="You are the Police Chief in a peer-to-peer coordination network."),
        HumanMessage(content=prompt)
    ])
    
    log = ""
    if response.tool_calls:
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            print(f"[Police Chief] Calling tool '{tool_name}' with args: {tool_args}")
            
            tool_map = {
                "check_responder_availability": check_responder_availability,
                "check_weather_and_traffic_hazards": check_weather_and_traffic_hazards,
                "dispatch_resource": dispatch_resource
            }
            if tool_name in tool_map:
                try:
                    res = tool_map[tool_name].invoke(tool_args)
                    log += f"- Dispatched: {res}\n"
                except Exception as e:
                    log += f"- Failed: {e}\n"
                    
        summarizer = model.invoke([
            SystemMessage(content="You are the Police Chief. Address your peers with your final dispatch details."),
            HumanMessage(content=f"{prompt}\n\nActions Taken:\n{log}")
        ])
        statement = "Police Chief: " + summarizer.content
    else:
        statement = "Police Chief: " + response.content
        
    print(f"[Network P2P] Police Chief statement posted.")
    return {"discussion": state.get("discussion", []) + [statement]}

# 3. Medical Chief Agent Node
def medical_chief_node(state: NetworkState):
    print("\n[Network P2P] 🚑 Medical Chief: Proposing hospital routing plan...")
    model = get_llm(temperature=0.3)
    tools = [check_responder_availability, query_hospital_status, dispatch_resource]
    model_with_tools = model.bind_tools(tools)
    
    discussion_str = "\n\n".join(state.get("discussion", []))
    
    prompt = (
        f"Incident: {state['incident']}\n\n"
        f"Prior Peer Discussion:\n{discussion_str}\n\n"
        "You are the Medical Chief. Review your peers' plans. "
        "Check hospital status and ambulance availability. Dispatch ambulances. "
        "Coordinate routing based on safety/road hazards reported by the Police Chief. "
        "Provide your medical plan directly to the other chiefs."
    )
    
    response = model_with_tools.invoke([
        SystemMessage(content="You are the Medical Chief in a peer-to-peer coordination network."),
        HumanMessage(content=prompt)
    ])
    
    log = ""
    if response.tool_calls:
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            print(f"[Medical Chief] Calling tool '{tool_name}' with args: {tool_args}")
            
            tool_map = {
                "check_responder_availability": check_responder_availability,
                "query_hospital_status": query_hospital_status,
                "dispatch_resource": dispatch_resource
            }
            if tool_name in tool_map:
                try:
                    res = tool_map[tool_name].invoke(tool_args)
                    log += f"- Dispatched: {res}\n"
                except Exception as e:
                    log += f"- Failed: {e}\n"
                    
        summarizer = model.invoke([
            SystemMessage(content="You are the Medical Chief. Address your peers with your final dispatch details."),
            HumanMessage(content=f"{prompt}\n\nActions Taken:\n{log}")
        ])
        statement = "Medical Chief: " + summarizer.content
    else:
        statement = "Medical Chief: " + response.content
        
    print(f"[Network P2P] Medical Chief statement posted.")
    return {
        "discussion": state.get("discussion", []) + [statement],
        "round": state.get("round", 0) + 1
    }

# Router: Loops back for second round if needed, otherwise compiles
def route_network(state: NetworkState):
    if state.get("round", 0) >= 2:
        print("[Network P2P] 🔀 Decision: Round limit reached (2 rounds). Compiling final agreement.")
        return "compiler"
    print("[Network P2P] 🔀 Decision: Starting negotiation round 2.")
    return "fire_chief"

# 4. Compiler Node: Summarizes agreed multi-agent plan
def compiler_node(state: NetworkState):
    print("\n[Network P2P] ✍️ Compiler Node: Summarizing final negotiated plan...")
    model = get_llm(temperature=0.2)
    
    discussion_str = "\n\n".join(state["discussion"])
    
    prompt = (
        f"Incident: {state['incident']}\n\n"
        f"Peer Coordination Debate & Statements:\n{discussion_str}\n\n"
        "You are a Joint Liaison Officer. Summarize the agreed-upon, collaborative dispatch plan. "
        "Formulate a structured Markdown report that merges the inputs from the Fire Chief, Police Chief, "
        "and Medical Chief into a single unified emergency response directive."
    )
    
    response = model.invoke([
        SystemMessage(content="You are the Joint Liaison Officer compilation agent."),
        HumanMessage(content=prompt)
    ])
    
    return {"final_report": response.content}

# Compile Graph
def build_network_graph():
    workflow = StateGraph(NetworkState)
    
    workflow.add_node("fire_chief", fire_chief_node)
    workflow.add_node("police_chief", police_chief_node)
    workflow.add_node("medical_chief", medical_chief_node)
    workflow.add_node("compiler", compiler_node)
    
    workflow.add_edge(START, "fire_chief")
    workflow.add_edge("fire_chief", "police_chief")
    workflow.add_edge("police_chief", "medical_chief")
    
    workflow.add_conditional_edges(
        "medical_chief",
        route_network,
        {
            "fire_chief": "fire_chief",
            "compiler": "compiler"
        }
    )
    workflow.add_edge("compiler", END)
    
    return workflow.compile()

def run_pattern(incident: str) -> dict:
    print(f"\n{'='*20} RUNNING MULTI-AGENT: PEER-TO-PEER NETWORK {'='*20}")
    
    app = build_network_graph()
    
    result = app.invoke({
        "incident": incident,
        "discussion": [],
        "round": 0,
        "final_report": ""
    })
    
    return {
        "pattern": "Network/P2P",
        "final_report": result["final_report"],
        "history": result["discussion"]
    }
