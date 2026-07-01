# shared/tools.py
import os
from langchain_core.tools import tool
from shared.environment import env

@tool
def check_responder_availability(service: str) -> str:
    """
    Check the status and availability of emergency vehicles for a service.
    
    Args:
        service (str): The emergency service ('Fire', 'Medical', or 'Police').
        
    Returns:
        str: JSON-formatted string of available vehicle counts and status.
    """
    return env.get_responder_status(service)

@tool
def query_hospital_status(hospital: str) -> str:
    """
    Query hospital capabilities, distance, bed availability, and specialties.
    
    Args:
        hospital (str): The hospital name (e.g., 'Mercy General', 'St. Jude Medical', 
                        'County Community', or 'all' to check all hospitals).
                        
    Returns:
        str: JSON-formatted string containing hospital status.
    """
    return env.get_hospital_status(hospital)

@tool
def check_weather_and_traffic_hazards(location: str) -> str:
    """
    Check if there are any active road hazards, traffic delays, or severe weather conditions at a location.
    
    Args:
        location (str): The target location or area name.
        
    Returns:
        str: Descriptions of matching hazards or confirmations of clear conditions.
    """
    return env.check_hazards(location)

@tool
def dispatch_resource(service: str, vehicle_type: str, units: int, location: str) -> str:
    """
    Dispatch emergency vehicles from a service to a specific location.
    This operation mutates the database by decrementing the available vehicle counts.
    
    Args:
        service (str): The emergency service ('Fire', 'Medical', or 'Police').
        vehicle_type (str): The type of vehicle (e.g., 'Fire Engine', 'Ambulance', 'Cruiser').
        units (int): The number of vehicles to dispatch.
        location (str): The incident location.
        
    Returns:
        str: Success or failure message of the dispatch action.
    """
    return env.dispatch(service, vehicle_type, units, location)

@tool
def request_human_approval(action: str, reasoning: str) -> str:
    """
    Request final human authorization for dispatching high-impact resources 
    or when encountering ambiguous/complex triage scenarios.
    
    Args:
        action (str): The specific dispatch or triage action requiring approval.
        reasoning (str): The clinical or operational reasoning behind this action.
        
    Returns:
        str: 'Approved' or 'Denied' with feedback/comments.
    """
    print(f"\n⚠️  [HUMAN APPROVAL REQUIRED] ⚠️")
    print(f"Proposed Action: {action}")
    print(f"Reasoning: {reasoning}")
    
    # Check if we should auto-approve (for automated non-interactive runs)
    if os.environ.get("AUTO_APPROVE") == "true":
        print("🤖 [Auto-Approve Mode] Action automatically approved.")
        return "Approved (Auto-Approved by System Mode)"
    
    try:
        user_input = input("Authorize this action? (yes/no/feedback): ").strip().lower()
        if user_input in ["yes", "y", "approve"]:
            return "Approved"
        elif user_input in ["no", "n", "deny"]:
            return "Denied: User rejected the action."
        else:
            return f"Denied with feedback: {user_input}"
    except (IOError, EOFError):
        # Fallback if stdin is not interactive
        print("🤖 [Non-Interactive Fallback] Action automatically approved.")
        return "Approved (Non-interactive fallback)"
