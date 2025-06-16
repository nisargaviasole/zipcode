from mcp.server.fastmcp import FastMCP
import requests
import logging
import json
import http.client
import urllib.parse
from zipcode import fetchCountyData


def build_plan_listing_url(user_data):
    """
    Build the plan listing URL with user data parameters, using defaults for missing values.

    Args:
        user_data (dict): User's healthcare information

    Returns:
        str: Complete URL with encoded form data
    """
    try:
        # Define default parameters
        default_params = {
            "selfAge": 23,
            "selfGender": "Male",
            "selfTobaccoUser": False,
            "selfPregnant": False,
            "selfCoverage": False,
            "dependents": [],
            "utilizationLevel": "Low",
            "householdSize": 1,
            "income": 40000,
            "providers": [],
            "drugs": [],
            "pincode": {
                "zipcode": "33601",
                "name": "Hillsborough County",
                "fips": "12057",
                "state": "FL",
                "stateName": "Florida",
            },
            "countOfMember": 1,
        }

        # Initialize updated parameters with defaults
        updated_params = default_params.copy()

        # Update parameters with user data if provided
        updated_params["selfAge"] = user_data.get("age", updated_params["selfAge"])
        updated_params["selfGender"] = user_data.get(
            "gender", updated_params["selfGender"]
        ).capitalize()
        updated_params["selfTobaccoUser"] = user_data.get(
            "tobacco", updated_params["selfTobaccoUser"]
        )
        updated_params["selfPregnant"] = user_data.get(
            "pregnant", updated_params["selfPregnant"]
        )
        updated_params["selfCoverage"] = user_data.get(
            "coverage", updated_params["selfCoverage"]
        )
        updated_params["householdSize"] = user_data.get(
            "household", updated_params["householdSize"]
        )
        updated_params["countOfMember"] = user_data.get(
            "household", updated_params["countOfMember"]
        )
        updated_params["income"] = user_data.get("income", updated_params["income"])

        # Handle APTC if provided (not in default_params, so only add if present)
        if "aptc" in user_data:
            updated_params["aptc"] = user_data["aptc"]

        # Update pincode information
        updated_params["pincode"] = {
            "zipcode": user_data.get("zipcode", updated_params["pincode"]["zipcode"]),
            "name": user_data.get("county", updated_params["pincode"]["name"]),
            "fips": user_data.get("county_fips", updated_params["pincode"]["fips"]),
            "state": user_data.get("state", updated_params["pincode"]["state"]),
            "stateName": user_data.get(
                "full_state", updated_params["pincode"]["stateName"]
            ),
        }

        # Handle drugs
        updated_params["drugs"] = user_data.get("drugs", updated_params["drugs"]) or []

        # Handle providers (doctors and hospitals)
        doctors = user_data.get("doctor_provider", []) or []
        hospitals = user_data.get("hospital_facility", []) or []
        updated_params["providers"] = doctors + hospitals

        # Convert to JSON string and URL encode
        form_json = json.dumps(updated_params, separators=(",", ":"))
        encoded_form = urllib.parse.quote(form_json)

        # Build the complete URL
        base_url = "https://nexquoting.com/nextere/plan/plan-listing"
        complete_url = f"{base_url}?form={encoded_form}"

        return complete_url

    except Exception as e:
        logger.error(f"Error building URL: {e}")
        return ""


user_data = {
    "name": "Nisarg",
    "age": 24,
    "email": "abc@gmail.com",
    "phone_number": "7894561230",
    "gender": "male",
    "zip_code": "33601",
    "tobacco_use": "No",
    "employer_coverage": "No",
    "pregnancy_status": "No",
    "household_size": 3,
    "annual_income": 50000,
    "preferred_doctors": "DR. JEFFREY SCOTT CALDER MD",
    "preferred_hospitals": "DIAGNOSTIC CENTER OF TAMPA",
    "preferred_medications": "VIVARIN",
}

print(build_plan_listing_url(user_data))
