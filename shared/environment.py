# shared/environment.py
import json


class EmergencyEnvironment:
    def __init__(self):
        # Fictional UK/NHS emergency response mock database.
        # All organisation names, addresses, and personnel are invented.
        # No connection to any real NHS trust, operational data, or real incident.

        self.responders = {
            "Fire": {
                "Pumping Appliance": {"available": 3, "total": 5, "status": "Ready"},
                "Aerial Ladder Platform": {"available": 1, "total": 2, "status": "Ready"},
                "Incident Response Unit": {"available": 1, "total": 2, "status": "Ready"}
            },
            "Medical": {
                "Double-Crewed Ambulance": {"available": 6, "total": 12, "status": "Ready"},
                "Rapid Response Vehicle": {"available": 4, "total": 5, "status": "Ready"},
                "HART Team": {"available": 1, "total": 1, "status": "Ready"}
            },
            "Police": {
                "Response Car": {"available": 8, "total": 12, "status": "Ready"},
                "Roads Policing Unit": {"available": 3, "total": 4, "status": "Ready"},
                "Armed Response Vehicle": {"available": 2, "total": 3, "status": "Ready"},
                "Police Support Unit Van": {"available": 2, "total": 3, "status": "Ready"}
            }
        }

        self.hospitals = {
            "Northgate University Hospital NHS Foundation Trust": {
                "opel_level": 2,
                "available_beds": 8,
                "major_trauma_centre": True,
                "burns_unit": True,
                "burns_beds": 4,
                "helicopter_pad": True,
                "eta_mins": 12,
                "specialties": ["Major Trauma", "Burns", "Neurosurgery", "Cardiothoracic"]
            },
            "St. Aldric's General Hospital NHS Foundation Trust": {
                "opel_level": 1,
                "available_beds": 18,
                "major_trauma_centre": False,
                "trauma_unit": True,
                "burns_unit": False,
                "helicopter_pad": False,
                "eta_mins": 8,
                "specialties": ["A&E", "Trauma", "Orthopaedics", "General Surgery"]
            },
            "Holborn Community Health Centre": {
                "opel_level": 1,
                "available_beds": 15,
                "major_trauma_centre": False,
                "minor_injuries_unit": True,
                "burns_unit": False,
                "helicopter_pad": False,
                "eta_mins": 5,
                "specialties": ["Minor Injuries", "Walk-in"]
            }
        }

        self.hazards = {
            "High Holborn": "Severe congestion following road works near Holborn Circus. Expect 15+ min delay on standard approach.",
            "Kingsway / Southampton Row junction": "Temporary traffic signals causing southbound queuing. Divert via Theobalds Road.",
            "Gray's Inn Road": "Clear. Recommended Category 1 diversion route northbound from WC1B."
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
            valid = ", ".join(self.hospitals.keys())
            return f"Hospital '{hospital_name}' not found. Available: {valid}."
        return json.dumps(self.hospitals[hospital_name], indent=2)

    def get_opel_interpretation(self, opel_level: int) -> str:
        interpretations = {
            1: "OPEL 1 — Normal operations. No escalation required.",
            2: "OPEL 2 — Pressurised but operational. Monitor capacity closely.",
            3: "OPEL 3 — Operating under sustained pressure. Divert non-critical patients where possible.",
            4: "OPEL 4 — Extreme pressure. Declare internal major incident. Divert all non-critical patients immediately."
        }
        return interpretations.get(opel_level, "Unknown OPEL level.")

    def check_hazards(self, location: str) -> str:
        matched = []
        for loc, desc in self.hazards.items():
            if loc.lower() in location.lower() or location.lower() in loc.lower():
                matched.append(f"{loc}: {desc}")
        if not matched:
            return "No active road hazards or weather warnings reported for this location."
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


# Global singleton — imported by all patterns; reset via env.__init__() between runs
env = EmergencyEnvironment()
