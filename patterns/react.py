# patterns/react.py
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from shared.llm import get_llm

from shared.tools import (
    check_responder_availability,
    query_hospital_status,
    check_weather_and_traffic_hazards,
    check_opel_level,
    assess_news2_score,
    dispatch_resource
)

# Define the State Schema
class ReActState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    incident: str

# Define the tools list for this pattern
tools = [
    check_responder_availability,
    query_hospital_status,
    check_weather_and_traffic_hazards,
    check_opel_level,
    assess_news2_score,
    dispatch_resource
]
tool_node = ToolNode(tools)

# Define the model node
def call_model(state: ReActState):
    print("\n[ReAct Agent] 🤔 Reasoning & Deciding Next Action...")
    messages = state["messages"]
    
    model = get_llm(temperature=0.1)
    
    # Bind the tools
    model_with_tools = model.bind_tools(tools)
    response = model_with_tools.invoke(messages)
    
    return {"messages": [response]}

# Conditional routing logic
def should_continue(state: ReActState):
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        tool_name = last_message.tool_calls[0]["name"]
        print(f"[ReAct Agent] 🔀 Decision: Execute tool '{tool_name}'")
        return "tools"
    print("[ReAct Agent] 🔀 Decision: Process Complete (No tool calls)")
    return END

# Graph Construction function
def build_react_graph():
    workflow = StateGraph(ReActState)
    
    # Add Nodes
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", tool_node)
    
    # Connect Edges
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            END: END
        }
    )
    workflow.add_edge("tools", "agent")
    
    return workflow.compile()

def run_pattern(incident: str) -> dict:
    print(f"\n{'='*20} RUNNING SINGLE-AGENT: REACT {'='*20}")
    
    app = build_react_graph()
    
    system_prompt = (
        "You are a 999 Emergency Dispatch Officer coordinating a multi-agency response in London.\n"
        "Follow this procedure:\n"
        "1. Check the availability of Fire, Medical, and Police responders.\n"
        "2. Check for road hazards or traffic delays affecting response routes.\n"
        "3. If casualties are reported, use assess_news2_score to determine clinical urgency, "
        "then query hospital status and check OPEL levels to select the appropriate receiving hospital.\n"
        "   - Burns casualties must go to Northgate University Hospital NHS Foundation Trust (only Burns Unit in network).\n"
        "   - Severe trauma: Northgate (Major Trauma Centre) or St. Aldric's (Trauma Unit) depending on OPEL level.\n"
        "   - Minor injuries: Holborn Community Health Centre.\n"
        "4. Dispatch appropriate units using exact UK vehicle type names "
        "(e.g. 'Pumping Appliance', 'Double-Crewed Ambulance', 'Response Car').\n"
        "5. Conclude with a structured summary: resources dispatched, hospital routing, hazard alerts, "
        "and field instructions.\n\n"
        "Do not stop until all dispatching and coordination is complete."
    )
    
    initial_state = {
        "incident": incident,
        "messages": [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Incident Details:\n{incident}")
        ]
    }
    
    result = app.invoke(initial_state)

    # Walk back to find the last AIMessage with content (avoids returning raw ToolMessage JSON)
    from langchain_core.messages import AIMessage
    final_message = ""
    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage) and msg.content and not msg.tool_calls:
            final_message = msg.content
            break
    
    history = []
    for msg in result["messages"]:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            history.append(f"Tool Call: {msg.tool_calls[0]['name']}")
        else:
            history.append(msg.content)
            
    return {
        "pattern": "ReAct",
        "final_report": final_message,
        "history": history
    }

