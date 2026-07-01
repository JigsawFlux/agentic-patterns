# shared/environment.py
import json

class EmergencyEnvironment:
    def __init__(self):
        # In-memory mock databases representing emergency resources
        self.responders = {
            "Fire": {
                "Fire Engine": {"available": 5, "total": 8, "status": "Ready"},
                "Hazmat Truck": {"available": 2, "total": 3, "status": "Ready"},
                "Rescue Squad": {"available": 3, "total": 4, "status": "Ready"}
            },
            "Medical": {
                "Ambulance": {"available": 6, "total": 12, "status": "Ready"},
                "Paramedic Fly-Car": {"available": 4, "total": 5, "status": "Ready"}
            },
            "Police": {
                "Cruiser": {"available": 10, "total": 15, "status": "Ready"},
                "Traffic Unit": {"available": 5, "total": 6, "status": "Ready"},
                "Tactical Van": {"available": 2, "total": 3, "status": "Ready"}
            }
        }
        
        self.hospitals = {
            "Mercy General": {
                "available_beds": 12,
                "trauma_center": True,
                "burn_unit": False,
                "distance_miles": 3.5,
                "specialties": ["Trauma", "Cardiology"]
            },
            "St. Jude Medical": {
                "available_beds": 4,
                "trauma_center": True,
                "burn_unit": True,
                "distance_miles": 7.2,
                "specialties": ["Trauma", "Burn Unit", "Pediatrics"]
            },
            "County Community": {
                "available_beds": 25,
                "trauma_center": False,
                "burn_unit": False,
                "distance_miles": 5.0,
                "specialties": ["General Medicine"]
            }
        }
        
        self.hazards = {
            "Mercy Hospital area": "Road construction on main approach, expect 10 min delay.",
            "Downtown": "High traffic density around Main St.",
            "North Highway": "Heavy rain causing slippery surface."
        }

        self.dispatched_log = []

    def get_responder_status(self, service: str) -> str:
        if service not in self.responders:
            return f"Unknown service: {service}. Available: Fire, Medical, Police."
        return json.dumps(self.responders[service], indent=2)

    def get_hospital_status(self, hospital_name: str) -> str:
        if hospital_name == "all":
            return json.dumps(self.hospitals, indent=2)
        if hospital_name not in self.hospitals:
            return f"Hospital '{hospital_name}' not found. Available: Mercy General, St. Jude Medical, County Community."
        return json.dumps(self.hospitals[hospital_name], indent=2)

    def check_hazards(self, location: str) -> str:
        matched = []
        for loc, desc in self.hazards.items():
            if loc.lower() in location.lower() or location.lower() in loc.lower():
                matched.append(f"{loc}: {desc}")
        if not matched:
            return "No active road hazards or weather warnings for this location."
        return "\n".join(matched)

    def dispatch(self, service: str, vehicle_type: str, units: int, location: str) -> str:
        if service not in self.responders:
            return f"Dispatch failed: Service '{service}' does not exist."
        
        vehicles = self.responders[service]
        if vehicle_type not in vehicles:
            valid_types = ", ".join(vehicles.keys())
            return f"Dispatch failed: Vehicle type '{vehicle_type}' not found for {service}. Valid types: {valid_types}."
        
        available = vehicles[vehicle_type]["available"]
        if available < units:
            # Dispatch as many as available
            dispatched = available
            vehicles[vehicle_type]["available"] = 0
            vehicles[vehicle_type]["status"] = "No Units Available"
        else:
            dispatched = units
            vehicles[vehicle_type]["available"] -= units
            if vehicles[vehicle_type]["available"] == 0:
                vehicles[vehicle_type]["status"] = "No Units Available"

        if dispatched == 0:
            return f"Dispatch failed: 0 '{vehicle_type}' units available in {service}."

        log_entry = {
            "service": service,
            "vehicle_type": vehicle_type,
            "requested": units,
            "dispatched": dispatched,
            "location": location
        }
        self.dispatched_log.append(log_entry)
        
        return (
            f"Dispatch Successful: Dispatched {dispatched} {vehicle_type}(s) from {service} "
            f"to '{location}'. (Requested: {units}, Remaining available: {vehicles[vehicle_type]['available']})"
        )

# Global instance of environment to be imported and used by patterns
env = EmergencyEnvironment()
