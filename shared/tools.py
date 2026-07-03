# shared/tools.py
import os
from langchain_core.tools import tool
from shared.environment import env


@tool
def check_responder_availability(service: str) -> str:
    """
    Check the status and availability of emergency vehicles for a service.

    Args:
        service (str): The emergency service. Must be one of: 'Fire', 'Medical', or 'Police'.

    Returns:
        str: JSON-formatted string of available vehicle counts and status.
             Fire vehicles: 'Pumping Appliance', 'Aerial Ladder Platform', 'Incident Response Unit'
             Medical vehicles: 'Double-Crewed Ambulance', 'Rapid Response Vehicle', 'HART Team'
             Police vehicles: 'Response Car', 'Roads Policing Unit', 'Armed Response Vehicle', 'Police Support Unit Van'
    """
    return env.get_responder_status(service)


@tool
def query_hospital_status(hospital: str) -> str:
    """
    Query hospital capabilities, ETA, bed availability, and specialties.

    Args:
        hospital (str): The hospital name. Valid values:
            - 'Northgate University Hospital NHS Foundation Trust' (Major Trauma Centre, Burns Unit, OPEL 2)
            - "St. Aldric's General Hospital NHS Foundation Trust" (Trauma Unit, A&E, no Burns Unit)
            - 'Holborn Community Health Centre' (Minor Injuries Unit only)
            - 'all' to query all hospitals at once

    Returns:
        str: JSON-formatted string containing hospital status including opel_level, available_beds,
             major_trauma_centre, burns_unit, eta_mins, and specialties.
    """
    return env.get_hospital_status(hospital)


@tool
def check_opel_level(hospital_name: str) -> str:
    """
    Check the NHS Operational Pressures Escalation Level (OPEL) for a hospital and get
    a clinical interpretation of what that level means for routing decisions.

    OPEL levels: 1=Normal, 2=Pressurised, 3=Sustained Pressure (divert non-critical), 4=Extreme (declare major incident).

    Args:
        hospital_name (str): The hospital name. Valid values:
            - 'Northgate University Hospital NHS Foundation Trust'
            - "St. Aldric's General Hospital NHS Foundation Trust"
            - 'Holborn Community Health Centre'

    Returns:
        str: OPEL level number and clinical interpretation for dispatch routing decisions.
    """
    hospital_data = env.hospitals.get(hospital_name)
    if not hospital_data:
        valid = ", ".join(env.hospitals.keys())
        return f"Hospital '{hospital_name}' not found. Available: {valid}."
    opel = hospital_data.get("opel_level", 1)
    interpretation = env.get_opel_interpretation(opel)
    return f"{hospital_name}: {interpretation}"


@tool
def assess_news2_score(patient_description: str) -> str:
    """
    Assess a patient's NEWS2 (National Early Warning Score 2) risk band based on a
    clinical description of their presenting symptoms and observations.

    NEWS2 is the NHS standard for detecting patient deterioration. It guides clinical
    urgency and appropriate receiving hospital selection.

    Risk bands:
    - Low (0-4): Routine monitoring. Transport to nearest A&E.
    - Medium (5-6): Urgent clinical review required. Pre-alert receiving hospital.
    - High (7+): Emergency response. Pre-alert Major Trauma Centre immediately.
    - Critical: Immediate life-threatening presentation. Consider HEMS and MTC pre-alert.

    Args:
        patient_description (str): A description of the patient's condition and observations
                                   (e.g., 'smoke inhalation, conscious, SpO2 91%, RR 24').

    Returns:
        str: Assessed NEWS2 risk band, recommended action, and hospital routing guidance.
    """
    description_lower = patient_description.lower()

    # Heuristic scoring based on keywords — in a real system this would use clinical values
    critical_keywords = ["cardiac arrest", "unconscious", "not breathing", "full thickness burn", "airway compromise"]
    high_keywords = ["burns", "severe smoke inhalation", "spo2 below 90", "respiratory distress", "altered consciousness"]
    medium_keywords = ["smoke inhalation", "spo2 91", "spo2 92", "tachycardia", "shortness of breath", "minor burn"]

    if any(kw in description_lower for kw in critical_keywords):
        return (
            "NEWS2 Assessment: CRITICAL\n"
            "Immediate life-threatening presentation. Activate HEMS if available. "
            "Pre-alert Northgate University Hospital NHS Foundation Trust (Major Trauma Centre / Burns Unit) immediately. "
            "Do not divert to secondary facilities."
        )
    elif any(kw in description_lower for kw in high_keywords):
        return (
            "NEWS2 Assessment: HIGH (Score 7+)\n"
            "Emergency response required. Pre-alert Northgate University Hospital NHS Foundation Trust (MTC). "
            "Burns casualties: route to Burns Unit. Severe inhalation: route to Major Trauma. "
            "Continuous monitoring en route."
        )
    elif any(kw in description_lower for kw in medium_keywords):
        return (
            "NEWS2 Assessment: MEDIUM (Score 5-6)\n"
            "Urgent clinical review required. Pre-alert St. Aldric's General Hospital NHS Foundation Trust (A&E/Trauma Unit). "
            "If burns are present, reroute to Northgate (Burns Unit). Monitor for deterioration."
        )
    else:
        return (
            "NEWS2 Assessment: LOW (Score 0-4)\n"
            "Routine monitoring. Transport to nearest A&E. "
            "St. Aldric's General Hospital (8 min ETA) or Holborn Community Health Centre (5 min ETA, minor injuries only). "
            "Reassess if condition changes."
        )


@tool
def check_weather_and_traffic_hazards(location: str) -> str:
    """
    Check for active road hazards, traffic delays, or conditions affecting emergency vehicle access.

    Args:
        location (str): The target location or area name (e.g., 'High Holborn', 'Kingsway', "Gray's Inn Road").

    Returns:
        str: Descriptions of matching hazards or confirmation of clear conditions.
    """
    return env.check_hazards(location)


@tool
def dispatch_resource(service: str, vehicle_type: str, units: int, location: str) -> str:
    """
    Dispatch emergency vehicles from a service to a specific location.
    This operation mutates the database by decrementing the available vehicle counts.

    Args:
        service (str): The emergency service. Must be one of: 'Fire', 'Medical', or 'Police'.
        vehicle_type (str): The type of vehicle. Must exactly match the vehicle type name:
            Fire: 'Pumping Appliance', 'Aerial Ladder Platform', 'Incident Response Unit'
            Medical: 'Double-Crewed Ambulance', 'Rapid Response Vehicle', 'HART Team'
            Police: 'Response Car', 'Roads Policing Unit', 'Armed Response Vehicle', 'Police Support Unit Van'
        units (int): The number of vehicles to dispatch.
        location (str): The incident location (e.g., '14 Kingsbourne Terrace, WC1B 9ZZ, London').

    Returns:
        str: Success or failure message of the dispatch action.
    """
    return env.dispatch(service, vehicle_type, units, location)


@tool
def request_human_approval(action: str, reasoning: str) -> str:
    """
    Request Silver Commander authorisation for a high-impact dispatch decision or
    when the situation requires human oversight before proceeding.

    Use this when:
    - Declaring or escalating to a Major Incident
    - Routing critically ill patients against standard protocol
    - Exhausting a resource type (last available unit)
    - Any action with significant operational or clinical risk

    Args:
        action (str): The specific dispatch or triage action requiring authorisation.
        reasoning (str): The operational or clinical reasoning behind this action.

    Returns:
        str: 'Approved' or 'Denied' with feedback.
    """
    print(f"\n⚠️  [SILVER COMMANDER AUTHORISATION REQUIRED] ⚠️")
    print(f"Proposed Action: {action}")
    print(f"Reasoning: {reasoning}")

    if os.environ.get("AUTO_APPROVE") == "true":
        print("🤖 [Auto-Approve Mode] Action automatically approved.")
        return "Approved (Auto-Approved by System Mode)"

    try:
        user_input = input("Authorise this action? (yes/no/feedback): ").strip().lower()
        if user_input in ["yes", "y", "approve"]:
            return "Approved"
        elif user_input in ["no", "n", "deny"]:
            return "Denied: Silver Commander rejected the action."
        else:
            return f"Denied with feedback: {user_input}"
    except (IOError, EOFError):
        print("🤖 [Non-Interactive Fallback] Action automatically approved.")
        return "Approved (Non-interactive fallback)"
