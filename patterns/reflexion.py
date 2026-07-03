# patterns/reflexion.py
from typing import TypedDict, List
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END
from shared.llm import get_llm

from shared.tools import (
    check_responder_availability,
    query_hospital_status,
    check_weather_and_traffic_hazards,
    check_opel_level,
    assess_news2_score,
    dispatch_resource,
    request_human_approval
)

# Define State Schema
class ReflexionState(TypedDict):
    incident: str
    draft: str
    critique: str
    loop_count: int
    approval_status: str
    draft_history: List[str]
    final_report: str




# 1. Generator Node: Generates or refines the dispatch draft
def generator_node(state: ReflexionState):
    loop_count = state.get("loop_count", 0)
    print(f"\n[Reflexion] ✍️ Generator Phase: Creating/Refining draft (Iteration {loop_count + 1})...")
    model = get_llm(temperature=0.2)

    tools = [
        check_responder_availability,
        query_hospital_status,
        check_weather_and_traffic_hazards,
        check_opel_level,
        assess_news2_score,
        dispatch_resource
    ]
    model_with_tools = model.bind_tools(tools)

    if loop_count == 0:
        prompt = (
            f"Incident: {state['incident']}\n\n"
            "Create a 999 emergency response deployment draft for London. "
            "Use check_responder_availability, check_weather_and_traffic_hazards, assess_news2_score, "
            "check_opel_level, and query_hospital_status to research the current state, then dispatch resources as needed.\n\n"
            "UK protocol guidance:\n"
            "- Burns casualties must go to Northgate University Hospital NHS Foundation Trust (only Burns Unit).\n"
            "- Severe trauma: Northgate (MTC) or St. Aldric's (Trauma Unit) depending on OPEL level.\n"
            "- Minor injuries: Holborn Community Health Centre.\n"
            "- Use exact UK vehicle type names when dispatching "
            "('Pumping Appliance', 'Double-Crewed Ambulance', 'Response Car', etc.).\n\n"
            "Once done, write a detailed deployment draft listing dispatched vehicles, hospital routing, and hazard alerts."
        )
    else:
        prompt = (
            f"Incident: {state['incident']}\n\n"
            f"Previous Draft:\n{state['draft']}\n\n"
            f"Safety Critique:\n{state['critique']}\n\n"
            "Revise and improve the deployment draft to address every point in the critique. "
            "Use tools to dispatch additional resources or verify hospital capacity as needed. "
            "Write the complete, corrected draft."
        )

    messages = [
        SystemMessage(content="You are a 999 Emergency Dispatch Officer. Build and refine deployment drafts using NHS-standard tools."),
        HumanMessage(content=prompt)
    ]

    response = model_with_tools.invoke(messages)

    # One-turn tool execution within the node
    if response.tool_calls:
        outcomes = []
        tool_map = {
            "check_responder_availability": check_responder_availability,
            "query_hospital_status": query_hospital_status,
            "check_weather_and_traffic_hazards": check_weather_and_traffic_hazards,
            "check_opel_level": check_opel_level,
            "assess_news2_score": assess_news2_score,
            "dispatch_resource": dispatch_resource
        }
        for tool_call in response.tool_calls:
            tool_name = tool_call["name"]
            tool_args = tool_call["args"]
            print(f"[Reflexion Generator] Calling tool '{tool_name}' with args: {tool_args}")
            if tool_name in tool_map:
                try:
                    res = tool_map[tool_name].invoke(tool_args)
                    outcomes.append(f"Tool {tool_name} outcome: {res}")
                except Exception as e:
                    outcomes.append(f"Tool {tool_name} failed: {e}")

        refined_prompt = (
            f"{prompt}\n\n"
            f"Tool Outcomes:\n" + "\n".join(outcomes) + "\n\n"
            "Compile the complete deployment draft now."
        )
        final_resp = model.invoke([
            SystemMessage(content="You are a 999 Emergency Dispatch Officer compiling the final deployment draft."),
            HumanMessage(content=refined_prompt)
        ])
        draft = final_resp.content
    else:
        draft = response.content

    print(f"[Reflexion Generator] Draft generated (iteration {loop_count + 1}):\n---\n{draft[:300]}...\n---")

    draft_history = state.get("draft_history", [])
    draft_history = draft_history + [f"=== Iteration {loop_count + 1} Draft ===\n{draft}"]

    return {"draft": draft, "loop_count": loop_count + 1, "draft_history": draft_history}


# 2. Critic Node: Evaluates the draft against NHS safety and operational standards
def critic_node(state: ReflexionState):
    print("\n[Reflexion] 🔍 Critic Phase: Evaluating draft against NHS dispatch protocols...")
    model = get_llm(temperature=0.2)

    prompt = (
        f"Incident Description:\n{state['incident']}\n\n"
        f"Proposed Deployment Draft:\n{state['draft']}\n\n"
        "Evaluate the draft against these NHS/UK dispatch safety protocols:\n"
        "1. FIRE PROTOCOL: For a structural building fire, a minimum of 4 Pumping Appliances must be dispatched "
        "(per NFCC guidance for multi-story structures). An Aerial Ladder Platform is required for structures of 3 or more storeys.\n"
        "2. MEDICAL ROUTING PROTOCOL: Burns casualties must be routed to Northgate University Hospital NHS Foundation Trust "
        "(the only Burns Unit in the network). Severe trauma victims must go to Northgate (Major Trauma Centre) "
        "or St. Aldric's General Hospital (Trauma Unit). Holborn Community Health Centre handles minor injuries only.\n"
        "3. HAZARD PROTOCOL: The draft must explicitly reference a check of road hazards and recommend "
        "a diversion route for emergency vehicles given known congestion.\n"
        "4. OPEL PROTOCOL: The draft must reference the OPEL level of the receiving hospital before committing "
        "to a routing decision.\n\n"
        "If the draft satisfies ALL protocols perfectly, reply with the word 'PASS' and nothing else.\n"
        "If any protocol is violated, output a detailed, bulleted critique so the generator can correct it. "
        "Do NOT output 'PASS' if any protocol is unmet."
    )

    response = model.invoke([
        SystemMessage(content="You are an NHS Emergency Service Safety Inspector enforcing strict dispatch protocols."),
        HumanMessage(content=prompt)
    ])

    critique = response.content.strip()
    print(f"[Reflexion Critic] Result:\n---\n{critique}\n---")

    return {"critique": critique}


def should_continue(state: ReflexionState):
    is_passed = state["critique"].strip().upper() == "PASS"
    if is_passed:
        print("[Reflexion] 🔀 Decision: Draft approved by Critic. Requesting Silver Commander authorisation.")
        return "human_approval"
    elif state["loop_count"] >= 3:
        print("[Reflexion] 🔀 Decision: Maximum iterations (3) reached. Proceeding to synthesizer.")
        return "synthesize"
    print("[Reflexion] 🔀 Decision: Draft failed safety check. Routing back to Generator.")
    return "generator"


# 3. Human Approval Node: Silver Commander sign-off after critic PASS
def human_approval_node(state: ReflexionState):
    print("\n[Reflexion] 🔐 Human Approval Phase: Requesting Silver Commander authorisation...")
    result = request_human_approval.invoke({
        "action": (
            f"Finalise and deploy emergency response plan for: {state['incident'][:120]}"
        ),
        "reasoning": (
            f"Draft has passed all {state['loop_count']} iteration(s) of NHS protocol review "
            f"(Critic returned PASS). Requesting Silver Commander sign-off before issuing the operational order."
        )
    })
    print(f"[Reflexion Human Approval] Result: {result}")
    return {"approval_status": result}


# 4. Synthesizer Node: Produces the final polished report
def synthesizer_node(state: ReflexionState):
    print("\n[Reflexion] ✍️ Synthesizer Phase: Compiling final verified report...")
    model = get_llm(temperature=0.2)

    approval_note = state.get("approval_status", "")
    approval_section = (
        f"\n\nAuthorisation Status: {approval_note}" if approval_note else ""
    )

    prompt = (
        f"Incident: {state['incident']}\n\n"
        f"Verified Draft (passed NHS protocol review):\n{state['draft']}"
        f"{approval_section}\n\n"
        "Reformat this as a clean, professional Emergency Deployment Summary in Markdown. "
        "Include all dispatched resources, hospital routing, diversion routes, hazard alerts, and field instructions. "
        "If an authorisation status is provided, include it prominently in the report header."
    )

    response = model.invoke([
        SystemMessage(content="You are a Chief of Emergency Services. Present the final polished deployment order."),
        HumanMessage(content=prompt)
    ])

    return {"final_report": response.content}


# Compile Graph
def build_reflexion_graph():
    workflow = StateGraph(ReflexionState)

    workflow.add_node("generator", generator_node)
    workflow.add_node("critic", critic_node)
    workflow.add_node("human_approval", human_approval_node)
    workflow.add_node("synthesizer", synthesizer_node)

    workflow.add_edge(START, "generator")
    workflow.add_edge("generator", "critic")
    workflow.add_conditional_edges(
        "critic",
        should_continue,
        {
            "generator": "generator",
            "human_approval": "human_approval",
            "synthesize": "synthesizer"
        }
    )
    workflow.add_edge("human_approval", "synthesizer")
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
        "approval_status": "",
        "draft_history": [],
        "final_report": ""
    })

    history = result.get("draft_history", [])
    history.append(f"=== Final Critique ===\n{result['critique']}")
    history.append(f"=== Authorisation ===\n{result.get('approval_status', 'N/A')}")

    return {
        "pattern": "Reflexion",
        "final_report": result["final_report"],
        "history": history
    }
