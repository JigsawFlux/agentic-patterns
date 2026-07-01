# patterns/consensus.py
import os
import json
import re
from typing import TypedDict, List, Dict
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
class ConsensusState(TypedDict):
    incident: str
    expert_reviews: Dict[str, Dict]  # expert name -> {score: int, rationale: str}
    debate_history: List[str]
    round: int
    final_report: str

def get_model(temperature=0.4):
    return ChatAnthropic(
        model=os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-6"),
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY"),
        temperature=temperature
    )

def parse_score_and_rationale(text: str) -> dict:
    # Heuristic parsing to find score: [1-5]
    match = re.search(r"score:\s*([1-5])", text, re.IGNORECASE)
    score = int(match.group(1)) if match else 3  # default to 3 if parsing fails
    return {"score": score, "rationale": text}

# 1. Expert Node: Threat Analyst
def threat_analyst_node(state: ConsensusState):
    print("\n[Consensus Agent] 📊 Threat Analyst: Assessing hazard and risk levels...")
    model = get_model()
    
    debate_str = "\n\n".join(state.get("debate_history", []))
    
    prompt = (
        f"Incident: {state['incident']}\n\n"
        f"Prior Debate Rounds:\n{debate_str if debate_str else 'None'}\n\n"
        "You are the Risk & Threat Analyst. Evaluate the hazard levels, public danger, and compound risks (weather, toxic materials). "
        "Recommend a Threat Severity Score from 1 (Minor) to 5 (Catastrophic).\n"
        "Format your answer EXACTLY as:\n"
        "SCORE: [1-5]\n"
        "RATIONALE: [your assessment]"
    )
    
    response = model.invoke([
        SystemMessage(content="You are the expert Risk & Threat Analyst."),
        HumanMessage(content=prompt)
    ])
    
    parsed = parse_score_and_rationale(response.content.strip())
    reviews = state.get("expert_reviews", {})
    reviews["ThreatAnalyst"] = parsed
    
    statement = f"Threat Analyst voted SCORE: {parsed['score']}. Rationale: {parsed['rationale'][:150]}..."
    
    return {
        "expert_reviews": reviews,
        "debate_history": state.get("debate_history", []) + [statement]
    }

# 2. Expert Node: Resource Chief
def resource_chief_node(state: ConsensusState):
    print("\n[Consensus Agent] 🚜 Resource Chief: Assessing responder availability and logisitics...")
    model = get_model()
    
    debate_str = "\n\n".join(state.get("debate_history", []))
    
    prompt = (
        f"Incident: {state['incident']}\n\n"
        f"Prior Debate Rounds:\n{debate_str if debate_str else 'None'}\n\n"
        "You are the Emergency Resource Chief. Evaluate the availability and logistics load. "
        "Is there a resource drain that could compromise other parts of the city? "
        "Recommend a Threat Severity Score from 1 (Minor) to 5 (Catastrophic).\n"
        "Format your answer EXACTLY as:\n"
        "SCORE: [1-5]\n"
        "RATIONALE: [your assessment]"
    )
    
    response = model.invoke([
        SystemMessage(content="You are the expert Emergency Resource Chief."),
        HumanMessage(content=prompt)
    ])
    
    parsed = parse_score_and_rationale(response.content.strip())
    reviews = state.get("expert_reviews", {})
    reviews["ResourceChief"] = parsed
    
    statement = f"Resource Chief voted SCORE: {parsed['score']}. Rationale: {parsed['rationale'][:150]}..."
    
    return {
        "expert_reviews": reviews,
        "debate_history": state.get("debate_history", []) + [statement]
    }

# 3. Expert Node: Public Safety Liaison
def public_safety_liaison_node(state: ConsensusState):
    print("\n[Consensus Agent] 📢 Public Safety Liaison: Assessing public panic & evacuations...")
    model = get_model()
    
    debate_str = "\n\n".join(state.get("debate_history", []))
    
    prompt = (
        f"Incident: {state['incident']}\n\n"
        f"Prior Debate Rounds:\n{debate_str if debate_str else 'None'}\n\n"
        "You are the Public Safety Liaison. Evaluate public safety, panic, evacuation difficulty, and hospital capacity. "
        "Recommend a Threat Severity Score from 1 (Minor) to 5 (Catastrophic).\n"
        "Format your answer EXACTLY as:\n"
        "SCORE: [1-5]\n"
        "RATIONALE: [your assessment]"
    )
    
    response = model.invoke([
        SystemMessage(content="You are the expert Public Safety Liaison."),
        HumanMessage(content=prompt)
    ])
    
    parsed = parse_score_and_rationale(response.content.strip())
    reviews = state.get("expert_reviews", {})
    reviews["PublicSafetyLiaison"] = parsed
    
    statement = f"Public Safety Liaison voted SCORE: {parsed['score']}. Rationale: {parsed['rationale'][:150]}..."
    
    return {
        "expert_reviews": reviews,
        "debate_history": state.get("debate_history", []) + [statement]
    }

# Router: Checks if vote scores match or round limit is reached
def route_consensus(state: ConsensusState):
    reviews = state.get("expert_reviews", {})
    scores = [reviews[exp]["score"] for exp in reviews]
    
    # Check if consensus (all scores identical) is reached
    all_equal = len(set(scores)) == 1
    round_count = state.get("round", 0)
    
    if all_equal:
        print(f"[Consensus Agent] 🔀 Decision: Consensus reached on Threat Level {scores[0]}!")
        return "compiler"
    elif round_count >= 2:
        print(f"[Consensus Agent] 🔀 Decision: Max rounds reached (2). Compiling final vote split.")
        return "compiler"
    else:
        print(f"[Consensus Agent] 🔀 Decision: Dissension detected {scores}. Loop back for debate round {round_count + 1}.")
        # Increment round counter state
        state["round"] = round_count + 1
        return "threat_analyst"

# 4. Compiler Node: Drafts final consensus report
def compiler_node(state: ConsensusState):
    print("\n[Consensus Agent] ✍️ Compiler Node: Writing final consensus summary...")
    model = get_model(temperature=0.2)
    
    debate_str = "\n\n".join(state["debate_history"])
    reviews = state["expert_reviews"]
    scores = [reviews[exp]["score"] for exp in reviews]
    consensus_score = scores[0] if len(set(scores)) == 1 else round(sum(scores)/len(scores))
    
    prompt = (
        f"Incident: {state['incident']}\n\n"
        f"Consensus Debate Log:\n{debate_str}\n\n"
        f"Consensus/Average Threat Score: {consensus_score} out of 5\n\n"
        "You are the Coordinator. Draft a consensus evaluation report in Markdown. "
        "Present the final agreed Threat Score (or average if dissension remained), "
        "a summary of the different expert viewpoints (Threat, Resource, Public Safety), "
        "and a unified tactical response deployment strategy based on the agreed threat level."
    )
    
    response = model.invoke([
        SystemMessage(content="You are the Emergency Consensus Liaison compiling the final evaluation report."),
        HumanMessage(content=prompt)
    ])
    
    return {"final_report": response.content}

# Compile Graph
def build_consensus_graph():
    workflow = StateGraph(ConsensusState)
    
    workflow.add_node("threat_analyst", threat_analyst_node)
    workflow.add_node("resource_chief", resource_chief_node)
    workflow.add_node("public_safety", public_safety_liaison_node)
    workflow.add_node("compiler", compiler_node)
    
    workflow.add_edge(START, "threat_analyst")
    workflow.add_edge("threat_analyst", "resource_chief")
    workflow.add_edge("resource_chief", "public_safety")
    
    workflow.add_conditional_edges(
        "public_safety",
        route_consensus,
        {
            "threat_analyst": "threat_analyst",
            "compiler": "compiler"
        }
    )
    workflow.add_edge("compiler", END)
    
    return workflow.compile()

def run_pattern(incident: str) -> dict:
    print(f"\n{'='*20} RUNNING MULTI-AGENT: CONSENSUS / JOINT {'='*20}")
    
    app = build_consensus_graph()
    
    result = app.invoke({
        "incident": incident,
        "expert_reviews": {},
        "debate_history": [],
        "round": 0,
        "final_report": ""
    })
    
    return {
        "pattern": "Consensus",
        "final_report": result["final_report"],
        "history": result["debate_history"]
    }
