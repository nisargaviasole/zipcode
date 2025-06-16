from mcp.server.fastmcp import FastMCP
import logging
import json
import requests
from zipcode import fetchCountyData
import urllib.parse

logger = logging.getLogger(__name__)
mcp = FastMCP("savings")
    
def fetch_savings(user_data):
    try:
        url_eligibility = "https://gateway-dev.nextere.com/api/quotingtool-service/households-and-eligibility/household-eligibility-estimates"
        income = user_data.get("annual_income")
        age = user_data.get("age")
        gender = user_data.get("gender")
        gender = gender.capitalize() if gender else None
        valueOfPrehganant = user_data.get("pregnancy_status") == "Yes"
        valueOfTobbaco = str(user_data.get("tobacco_use", "")).strip().lower() == "yes"
        valueOfCoverage = not user_data.get("employer_coverage", False)
        zip_code_data = user_data.get("zip_code")
        zip_data = fetchCountyData(zip_code_data)
        county_fips = zip_data.get("fips")
        state = zip_data.get("state")

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

        plan_response = requests.post(
            url=url_plan,
            data=json.dumps(plan_payload),
            headers={"Content-Type": "application/json"},
        )

        if plan_response.status_code == 200:
            plan_data = plan_response.json()
            plans = plan_data.get("plans", [])
            if plans:
                plan_name = plans[0].get("name", "")
                plan_with_discount = plans[0].get("premium_W_Credit", 0)
                rounded_plan = round(plan_with_discount)
                return {
                    "savings": str(aptc),  # Ensure savings is a string as per tool schema
                    "healthplan": plan_name,
                    "roundedplan": rounded_plan
                }

        return {"savings": "0", "healthplan": "", "roundedplan": 0}

    except Exception as e:
        logger.error(f"Error calculating savings: {e}")
        return {"savings": "0", "healthplan": "", "roundedplan": 0}

@mcp.tool()
async def get_saving_info(json_data):
    try:
        print("Saving Tool called with data:", json_data)
        result = fetch_savings(json_data)
        return result
    except Exception as e:
        logger.error(f"Error in get_saving_info: {e}")
        return {
            "savings": "0",
            "healthplan": "Error processing request",
            "roundedplan": "Error Processing request"
        }