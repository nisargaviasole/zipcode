from mcp.server.fastmcp import FastMCP
import logging
import json
import requests
from zipcode import fetchCountyData
import urllib.parse

logger = logging.getLogger(__name__)
mcp = FastMCP("get_url")

def build_plan_listing_url(user_data):
    """
    Build the plan listing URL with user data parameters
    
    Args:
        user_data (dict): User's healthcare information
        
    Returns:
        str: Complete URL with encoded form data
    """
    try:
        # Extract basic user information
        age = user_data.get("age", 22)
        gender = user_data.get("gender", "Male")
        tobacco_use = str(user_data.get("tobacco_use", "")).strip().lower() == "yes"
        pregnancy_status = user_data.get("pregnancy_status", "No") == "Yes"
        employer_coverage = user_data.get("employer_coverage", False)
        household_size = user_data.get("household_size", 1)
        annual_income = user_data.get("annual_income", 0)
        zip_code = user_data.get("zip_code", "")
        
        # Get zip code data for pincode section
        zip_data = fetchCountyData(zip_code) if zip_code else {}
        county_name = zip_data.get("county", "")
        county_fips = zip_data.get("fips", "")
        state = zip_data.get("state", "")
        state_name = zip_data.get("state_name", "")
        
        # Process providers (doctors) - convert from user preferences to provider format
        providers = []
        preferred_doctors = user_data.get("preferred_doctors", [])
        
        for doctor in preferred_doctors:
            if isinstance(doctor, dict):
                provider_entry = {
                    "address": {
                        "city": doctor.get("city", "").upper(),
                        "phone": doctor.get("phone", ""),
                        "state": doctor.get("state", "").upper(),
                        "street1": doctor.get("address", "").upper(),
                        "street2": doctor.get("suite", ""),
                        "zipcode": doctor.get("zipcode", zip_code)
                    },
                    "distance": doctor.get("distance", 0.0),
                    "provider": {
                        "accepting": doctor.get("accepting", "accepting"),
                        "facility_Types": [],
                        "gender": doctor.get("gender", "unknown"),
                        "group_Id": doctor.get("group_id", ""),
                        "languages": doctor.get("languages", ["English"]),
                        "name": doctor.get("name", "").upper(),
                        "npi": doctor.get("npi", ""),
                        "provider_Type": doctor.get("provider_type", "Individual"),
                        "specialties": doctor.get("specialties", []),
                        "taxonomy": doctor.get("taxonomy", ""),
                        "valid": doctor.get("valid", False)
                    }
                }
                providers.append(provider_entry)
        
        # Process medications/drugs
        drugs = []
        preferred_medications = user_data.get("preferred_medications", [])
        
        for medication in preferred_medications:
            if isinstance(medication, dict):
                drug_entry = {
                    "full_Name": medication.get("full_name", ""),
                    "name": medication.get("name", "").upper(),
                    "route": medication.get("route", "Oral Pill"),
                    "rxcui": medication.get("rxcui", ""),
                    "rxnorm_dose_form": medication.get("dose_form", "Oral Tablet"),
                    "rxterms_dose_form": medication.get("dose_form_short", "Tab"),
                    "strength": medication.get("strength", "")
                }
                drugs.append(drug_entry)
        
        # Build the form data structure
        form_data = {
            "selfAge": age,
            "selfGender": gender,
            "selfTobaccoUser": tobacco_use,
            "selfPregnant": pregnancy_status,
            "selfCoverage": employer_coverage,
            "dependents": [],  # Empty for now, can be extended for family members
            "utilizationLevel": "Low",  # Default value
            "householdSize": household_size,
            "income": annual_income,
            "providers": providers,
            "drugs": drugs,
            "pincode": {
                "zipcode": zip_code,
                "name": county_name,
                "fips": county_fips,
                "state": state,
                "stateName": state_name
            },
            "countOfMember": household_size
        }
        
        # Convert to JSON string and URL encode
        form_json = json.dumps(form_data, separators=(',', ':'))
        encoded_form = urllib.parse.quote(form_json)
        
        # Build the complete URL
        base_url = "https://nexquoting.com/nextere/plan/plan-listing"
        complete_url = f"{base_url}?form={encoded_form}"
        
        return complete_url
        
    except Exception as e:
        logger.error(f"Error building URL: {e}")
        return ""
     
@mcp.tool()
async def generate_plan_listing_url(json_data):
    """
    Generate a plan listing URL based on user's healthcare information.
    
    Args:
        json_data (dict): JSON object containing user's complete profile including:
          - Full name
          - Age
          - Gender
          - Zip code
          - Email
          - Phone number
          - Tobacco use status
          - Pregnancy status (if applicable)
          - Employer coverage status
          - Household size
          - Annual income
          - Preferred doctors (list of doctor objects with details)
          - Preferred hospitals
          - Preferred medications (list of medication objects with details)
    
    Returns:
        dict: Dictionary containing:
          - url (str): Complete URL for plan listing page
          - success (bool): Whether URL generation was successful
          - message (str): Status message
    """
    try:
        print("URL Generator Tool called with data:", json_data)
        
        # Generate the URL
        url = build_plan_listing_url(json_data)
        
        if url:
            return {
                "url": url,
                "success": True,
                "message": "URL generated successfully"
            }
        else:
            return {
                "url": "",
                "success": False,
                "message": "Failed to generate URL"
            }
            
    except Exception as e:
        logger.error(f"Error in generate_plan_listing_url: {e}")
        return {
            "url": "",
            "success": False,
            "message": f"Error generating URL: {str(e)}"
        }