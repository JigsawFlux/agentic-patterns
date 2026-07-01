# patterns/reflexion.py
import os
from typing import TypedDict, List, Annotated
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
class ReflexionState(TypedDict):
    incident: str
    draft: str
    critique: str
    loop_count: int
    final_report: str

def get_model():
    return ChatAnthropic(
        model=os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6"),
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY"),
        temperature=0.2
    )

# 1. Generator Node: Generates or refines the dispatch draft
def generator_node(state: ReflexionState):
    loop_count = state.get("loop_count", 0)
    print(f"\n[Reflexion] ✍️ Generator Phase: Creating/Refining draft (Iteration {loop_count + 1})...")
    model = get_model()
    
    tools = [
        check_responder_availability,
        query_hospital_status,
        check_weather_and_traffic_hazards,
        dispatch_resource
    ]
    model_with_tools = model.bind_tools(tools)
    
    # We will run a simple tool execution run inside generator or direct prompt
    # First, let's query the environment to see what we have
    if loop_count == 0:
        # Initial run: ask model to inspect and write initial draft
        prompt = (
            f"Incident: {state['incident']}\n\n"
            "Please create an emergency response deployment draft. Use the check_responder_availability, check_weather_and_traffic_hazards, "
            "and query_hospital_status tools to research the current state, and then run dispatch_resource as needed. "
            "Once you have gathered the data and dispatched the resources, write a detailed deployment draft listing:\n"
            "- Dispatched vehicles and counts\n"
            "- Targeted hospital location\n"
            "- Traffic delay alerts\n"
            "Output your final draft clearly."
        )
    else:
        # Refinement run: inspect critique and update draft
        prompt = (
            f"Incident: {state['incident']}\n\n"
            f"Previous Draft:\n{state['draft']}\n\n"
            f"Critic Critique:\n{state['critique']}\n\n"
            "You MUST update and improve the deployment draft based on the critic's safety critique. "
            "Use tools (like dispatching more resources or querying hospital capacities) to correct any deficiencies. "
            "Write the complete, revised draft."
        )
        
    messages = [
        SystemMessage(content="You are an Emergency Dispatch Officer. Build and refine response drafts using tools."),
        HumanMessage(content=prompt)
    ]
    
    response = model_with_tools.invoke(messages)
    
    # Simple one-turn tool execution loop within the node for simplicity
    if response.tool_calls:
        # Execute tool calls
        outcomes = []
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            print(f"[Reflexion Generator] Calling tool '{tool_name}' with args: {tool_args}")
            
            tool_map = {
                "check_responder_availability": check_responder_availability,
                "query_hospital_status": query_hospital_status,
                "check_weather_and_traffic_hazards": check_weather_and_traffic_hazards,
                "dispatch_resource": dispatch_resource
            }
            if tool_name in tool_map:
                try:
                    res = tool_map[tool_name].invoke(tool_args)
                    outcomes.append(f"Tool {tool_name} outcome: {res}")
                except Exception as e:
                    outcomes.append(f"Tool {tool_name} failed: {e}")
                    
        # Now invoke the model again with the tool outcomes so it can generate the text draft
        refined_prompt = (
            f"{prompt}\n\n"
            f"Immediate Tool Outcomes:\n" + "\n".join(outcomes) + "\n\n"
            "Please compile the complete deployment draft now."
        )
        final_resp = model.invoke([
            SystemMessage(content="You are an Emergency Dispatch Officer compiling the final text draft."),
            HumanMessage(content=refined_prompt)
        ])
        draft = final_resp.content
    else:
        draft = response.content
        
    print(f"[Reflexion Generator] Draft generated:\n--- \n{draft[:300]}...\n---")
    return {"draft": draft, "loop_count": loop_count + 1}

# 2. Critic Node: Evaluates the draft against safety and operational standards
def critic_node(state: ReflexionState):
    print("\n[Reflexion] 🔍 Critic Phase: Evaluating draft against protocols...")
    model = get_model()
    
    # We define strict safety criteria:
    # 1. Were location hazards/routing checked?
    # 2. If there's fire/smoke, were at least 3 fire engines dispatched?
    # 3. If burn victims exist, were they routed to St. Jude Medical (the only burn unit)?
    # 4. If trauma injuries exist, were they routed to Mercy General or St. Jude (trauma centers)?
    
    prompt = (
        f"Incident Description:\n{state['incident']}\n\n"
        f"Proposed Deployment Draft:\n{state['draft']}\n\n"
        "Evaluate the draft against these safety protocols:\n"
        "1. FIRE PROTOCOL: If the incident involves a building fire, gas leak, or chemical spill, "
        "at least 3 Fire Engines or Hazmat Trucks must be dispatched.\n"
        "2. MEDICAL ROUTING PROTOCOL: Burn victims must be routed to St. Jude Medical (has Burn Unit). "
        "Severe trauma victims must be routed to Mercy General or St. Jude (Trauma Centers). "
        "Community clinics should only take minor cases.\n"
        "3. HAZARD PROTOCOL: The report must explicitly mention checking weather or road traffic hazards.\n\n"
        "If the draft satisfies ALL protocols perfectly, reply with the word 'PASS' and nothing else.\n"
        "If any protocol is violated, output a detailed, bulleted critique explaining what is missing or wrong "
        "so the generator can correct it. Do NOT output 'PASS' if there are warnings."
    )
    
    response = model.invoke([
        SystemMessage(content="You are an Emergency Service Safety Inspector. You enforce strict dispatch protocols."),
        HumanMessage(content=prompt)
    ])
    
    critique = response.content.strip()
    print(f"[Reflexion Critic] Result:\n--- \n{critique}\n---")
    
    return {"critique": critique}

def should_continue(state: ReflexionState):
    is_passed = state["critique"].strip().upper() == "PASS"
    if is_passed or state["loop_count"] >= 3:
        if is_passed:
            print("[Reflexion] 🔀 Decision: Draft approved by Critic. Ending loop.")
        else:
            print("[Reflexion] 🔀 Decision: Maximum loop count reached (3). Ending loop.")
        return "synthesize"
    
    print("[Reflexion] 🔀 Decision: Draft failed check. Routing back to Generator for refinement.")
    return "generator"


# Synthesizer Node
def synthesizer_node(state: ReflexionState):
    print("\n[Reflexion] ✍️ Synthesizer Phase: Compiling final verified report...")
    model = get_model()
    
    prompt = (
        f"Incident: {state['incident']}\n\n"
        f"Verified Draft:\n{state['draft']}\n\n"
        "Reformat and output this verified draft as a clean, highly professional Emergency Deployment Summary in Markdown. "
        "Ensure all final assets, locations, traffic alerts, and instructions are clearly presented."
    )
    
    response = model.invoke([
        SystemMessage(content="You are a Chief of Emergency Services. Present the final polished deployment plan."),
        HumanMessage(content=prompt)
    ])
    
    return {"final_report": response.content}

# Compile Graph
def build_reflexion_graph():
    workflow = StateGraph(ReflexionState)
    
    workflow.add_node("generator", generator_node)
    workflow.add_node("critic", critic_node)
    workflow.add_node("synthesizer", synthesizer_node)
    
    workflow.add_edge(START, "generator")
    workflow.add_edge("generator", "critic")
    workflow.add_conditional_edges(
        "critic",
        should_continue,
        {
            "generator": "generator",
            "synthesize": "synthesizer"
        }
    )
    workflow.add_edge("synthesizer", END)
    
    return workflow.compile()

def run_pattern(incident: str) -> dict:
    print(f"\n{'='*20} RUNNING SINGLE-AGENT: REFLEXION {'='*20}")
    
    app = build_reflexion_graph()
    
    result = app.invoke({
        "incident": incident,
        "draft": "",
        "critique": "",
        "loop_count": 0,
        "final_report": ""
    })
    
    return {
        "pattern": "Reflexion",
        "final_report": result["final_report"],
        "history": [f"Iteration {result['loop_count']}\nCritique: {result['critique']}"]
    }
