# user_data: {'full_name': 'nisarg jadhav', 'age': 24, 'gender': 'male', 'zip_code': '33601', 'email': 'abc@gmail.com', 'phone_number': '7984561230', 'tobacco_use': False, 'pregnancy_status': 'Not applicable', 'employer_coverage': False, 'household_size': 4, 'annual_income': 500000, 'preferred_doctors': ['MARGARET C. TEST CRNA'], 'preferred_hospitals': [], 'preferred_medications': []}
# eligibility_payload: {'household': {'income': 500000, 'people': [{'age': 24, 'gender': 'male', 'isPregnant': False, 'usesTobacco': False, 'relationship': 'Self', 'hasMec': True}]}, 'market': 'Individual', 'place': {'countyFips': '12057', 'state': 'FL', 'zipcode': '33601'}, 'year': 2024}


from mcp.server.fastmcp import FastMCP
import json
import requests
from zipcode import fetchCountyData


def fetch_savings(user_data):
    """
    Process user data and return savings and health plan information.

    Args:
        user_data (dict): User's healthcare information including demographics and preferences

    Returns:
        dict: Dictionary containing savings amount, plan name, and rounded premium
    """
    try:
        url_eligibility = "https://gateway-dev.nextere.com/api/quotingtool-service/households-and-eligibility/household-eligibility-estimates"

        # Extract data from user_data dictionary
        income = user_data.get("annual_income")
        age = user_data.get("age")
        gender = user_data.get("gender")
        valueOfPrehganant = user_data.get("pregnancy_status") == "Yes"
        valueOfTobbaco = user_data.get("tobacco_use", False)
        valueOfCoverage = not user_data.get("employer_coverage", False)
        zip_code_data = user_data.get("zip_code")
        zip_data = fetchCountyData(zip_code_data)
        county_fips = zip_data["fips"]
        state = 'zip_data["state"]'

        # Build payload for eligibility estimate
        eligibility_payload = {
            "household": {
                "income": income,
                "people": [
                    {
                        "age": age,
                        "gender": gender,
                        "isPregnant": valueOfPrehganant,
                        "usesTobacco": valueOfTobbaco,
                        "relationship": "Self",
                        "hasMec": valueOfCoverage,
                    }
                ],
            },
            "market": "Individual",
            "place": {
                "countyFips": county_fips,
                "state": state,
                "zipcode": zip_code_data,
            },
            "year": 2024,
        }

        print("eligibility_payload:", eligibility_payload)

        response = requests.post(
            url=url_eligibility,
            data=json.dumps(eligibility_payload),
            headers={"Content-Type": "application/json"},
        )

        aptc = 0
        aptcEligible = False
        if response.status_code == 200:
            data = response.json()
            estimates = data.get("estimates", [])
            if estimates:
                aptc = estimates[0].get("aptc", 0)
                aptcEligible = aptc > 0

        # Now fetch lowest cost bronze plan
        url_plan = "https://gateway-dev.nextere.com/api/quotingtool-service/households-and-eligibility/lowest-cost-bronze-plan-aI"

        plan_payload = {
            "household": {
                "income": income,
                "people": [
                    {
                        "aptcEligible": aptcEligible,
                        "age": age,
                        "hasMec": valueOfCoverage,
                        "isPregnant": valueOfPrehganant,
                        "usesTobacco": valueOfTobbaco,
                        "gender": gender,
                        "relationship": "Self",
                        "utilizationLevel": "Low",
                    }
                ],
                "hasMarriedCouple": False,
            },
            "place": {
                "countyFips": county_fips,
                "state": state,
                "zipcode": zip_code_data,
            },
        }

        print("plan",plan_payload)
        plan_response = requests.post(
            url=url_plan,
            data=json.dumps(plan_payload),
            headers={"Content-Type": "application/json"},
        )
        print("stats",plan_response.status_code)
        if plan_response.status_code == 200:
            plan_data = plan_response.json()
            plans = plan_data.get("plans", [])
            if plans:
                plan_name = plans[0].get("name", "")
                plan_with_discount = plans[0].get("premium_W_Credit", 0)
                rounded_plan = round(plan_with_discount)

                return {
                    "savings": aptc,
                    "plan_name": plan_name,
                    "rounded_plan": rounded_plan,
                }

    except Exception as e:
        print(f"Error calculating savings: {e}")

    return {"savings": 0, "plan_name": "", "rounded_plan": 0}


sample_user_data = {
    "full_name": "nisarg jadhav",
    "age": 24,
    "gender": "male",
    "zip_code": "33601",
    "email": "abc@gmail.com",
    "phone_number": "7984561230",
    "tobacco_use": False,
    "pregnancy_status": "Not applicable",
    "employer_coverage": False,
    "household_size": 4,
    "annual_income": 500000,
    "preferred_doctors": ["MARGARET C. TEST CRNA"],
    "preferred_hospitals": [],
    "preferred_medications": [],
}

print(fetch_savings(sample_user_data))
