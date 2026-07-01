# patterns/react.py
import os
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode

from shared.tools import (
    check_responder_availability,
    query_hospital_status,
    check_weather_and_traffic_hazards,
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
    dispatch_resource
]
tool_node = ToolNode(tools)

# Define the model node
def call_model(state: ReActState):
    print("\n[ReAct Agent] 🤔 Reasoning & Deciding Next Action...")
    messages = state["messages"]
    
    # Initialize the Anthropic Chat Model
    model = ChatAnthropic(
        model=os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6"),
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY"),
        temperature=0.1
    )
    
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
        "You are an Emergency Dispatch Officer. Your goal is to coordinate a response to the emergency incident.\n"
        "Follow this procedure:\n"
        "1. Check the availability of necessary responders (Fire, Medical, Police).\n"
        "2. Check for nearby hazards or traffic delays that might impact response times.\n"
        "3. Select and query the status of the closest hospital if injuries are reported.\n"
        "4. Dispatch the appropriate units (vehicle types and counts) based on resources and hazards.\n"
        "5. Conclude with a final, structured summary detailing which resources were dispatched to where, "
        "and any instructions for the field units.\n\n"
        "Do not stop until all necessary resource dispatching and coordination has been executed."
    )
    
    initial_state = {
        "incident": incident,
        "messages": [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Incident Details:\n{incident}")
        ]
    }
    
    result = app.invoke(initial_state)
    
    # Extract final response from the agent
    final_message = result["messages"][-1].content
    
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

