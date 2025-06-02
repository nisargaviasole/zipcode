# from mcp.server.fastmcp import FastMCP
# import requests
# import logging
# import json
# import http.client
# import urllib.parse
# from zipcode import fetchCountyData


# def build_plan_listing_url(user_data):
#     """
#     Build the plan listing URL with user data parameters
    
#     Args:
#         user_data (dict): User's healthcare information
        
#     Returns:
#         str: Complete URL with encoded form data
#     """
#     try:
#         # Extract basic user information
#         age = user_data.get("age", 22)
#         gender = user_data.get("gender", "Male")
#         tobacco_use = str(user_data.get("tobacco_use", "")).strip().lower() == "yes"
#         pregnancy_status = user_data.get("pregnancy_status", "No") == "Yes"
#         employer_coverage = user_data.get("employer_coverage", False)
#         household_size = user_data.get("household_size", 1)
#         annual_income = user_data.get("annual_income", 0)
#         zip_code = user_data.get("zip_code", "")
        
#         # Get zip code data for pincode section
#         zip_data = fetchCountyData(zip_code) if zip_code else {}
#         county_name = zip_data.get("county", "")
#         county_fips = zip_data.get("fips", "")
#         state = zip_data.get("state", "")
#         state_name = zip_data.get("state_name", "")
        
#         # Process providers (doctors) - convert from user preferences to provider format
#         providers = []
#         preferred_doctors = user_data.get("preferred_doctors", [])
        
#         for doctor in preferred_doctors:
#             if isinstance(doctor, dict):
#                 provider_entry = {
#                     "address": {
#                         "city": doctor.get("city", "").upper(),
#                         "phone": doctor.get("phone", ""),
#                         "state": doctor.get("state", "").upper(),
#                         "street1": doctor.get("address", "").upper(),
#                         "street2": doctor.get("suite", ""),
#                         "zipcode": doctor.get("zipcode", zip_code)
#                     },
#                     "distance": doctor.get("distance", 0.0),
#                     "provider": {
#                         "accepting": doctor.get("accepting", "accepting"),
#                         "facility_Types": [],
#                         "gender": doctor.get("gender", "unknown"),
#                         "group_Id": doctor.get("group_id", ""),
#                         "languages": doctor.get("languages", ["English"]),
#                         "name": doctor.get("name", "").upper(),
#                         "npi": doctor.get("npi", ""),
#                         "provider_Type": doctor.get("provider_type", "Individual"),
#                         "specialties": doctor.get("specialties", []),
#                         "taxonomy": doctor.get("taxonomy", ""),
#                         "valid": doctor.get("valid", False)
#                     }
#                 }
#                 providers.append(provider_entry)
        
#         # Process medications/drugs
#         drugs = []
#         preferred_medications = user_data.get("preferred_medications", [])
        
#         for medication in preferred_medications:
#             if isinstance(medication, dict):
#                 drug_entry = {
#                     "full_Name": medication.get("full_name", ""),
#                     "name": medication.get("name", "").upper(),
#                     "route": medication.get("route", "Oral Pill"),
#                     "rxcui": medication.get("rxcui", ""),
#                     "rxnorm_dose_form": medication.get("dose_form", "Oral Tablet"),
#                     "rxterms_dose_form": medication.get("dose_form_short", "Tab"),
#                     "strength": medication.get("strength", "")
#                 }
#                 drugs.append(drug_entry)
        
#         # Build the form data structure
#         form_data = {
#             "selfAge": age,
#             "selfGender": gender,
#             "selfTobaccoUser": tobacco_use,
#             "selfPregnant": pregnancy_status,
#             "selfCoverage": employer_coverage,
#             "dependents": [],  # Empty for now, can be extended for family members
#             "utilizationLevel": "Low",  # Default value
#             "householdSize": household_size,
#             "income": annual_income,
#             "providers": providers,
#             "drugs": drugs,
#             "pincode": {
#                 "zipcode": zip_code,
#                 "name": county_name,
#                 "fips": county_fips,
#                 "state": state,
#                 "stateName": state_name
#             },
#             "countOfMember": household_size
#         }
        
#         # Convert to JSON string and URL encode
#         form_json = json.dumps(form_data, separators=(',', ':'))
#         encoded_form = urllib.parse.quote(form_json)
        
#         # Build the complete URL
#         base_url = "https://nexquoting.com/nextere/plan/plan-listing"
#         complete_url = f"{base_url}?form={encoded_form}"
        
#         return complete_url
        
#     except Exception as e:
#         print(f"Error building URL: {e}")
#         return ""
    
# user_data = {
#   "full_name": "John Michael Smith",
#   "age": 28,
#   "gender": "Male",
#   "zip_code": "33601",
#   "email": "john.smith@example.com",
#   "phone_number": "+1-813-555-0123",
#   "tobacco_use": "No",
#   "pregnancy_status": "No",
#   "employer_coverage": False,
#   "household_size": 3,
#   "annual_income": 55000,
#   "preferred_doctors": [
#     {
#       "name": "Dr. Sarah Johnson MD",
#       "city": "Tampa",
#       "state": "FL",
#       "address": "1234 Health Blvd Suite 200",
#       "suite": "Suite 200",
#       "phone": "8135551234",
#       "zipcode": "33601",
#       "specialties": ["Family Medicine", "Internal Medicine"],
#       "npi": "1234567890",
#       "provider_type": "Individual",
#       "gender": "Female",
#       "accepting": "accepting",
#       "languages": ["English", "Spanish"],
#       "taxonomy": "Family Medicine",
#       "group_id": "abc123-def456-ghi789",
#       "distance": 1.2,
#       "valid": True
#     },
#     {
#       "name": "Dr. Michael Chen DMD",
#       "city": "Tampa",
#       "state": "FL",
#       "address": "5678 Dental Ave",
#       "suite": "",
#       "phone": "8135559876",
#       "zipcode": "33602",
#       "specialties": ["General Dentistry", "Oral Surgery"],
#       "npi": "0987654321",
#       "provider_type": "Individual",
#       "gender": "Male",
#       "accepting": "accepting",
#       "languages": ["English"],
#       "taxonomy": "Dentist · General Practice",
#       "group_id": "xyz789-abc123-def456",
#       "distance": 2.5,
#       "valid": True
#     }
#   ],
#   "preferred_hospitals": [
#     {
#       "name": "Tampa General Hospital",
#       "address": "1 Tampa General Cir, Tampa, FL 33606",
#       "phone": "8138443000",
#       "type": "General Hospital"
#     },
#     {
#       "name": "St. Joseph's Hospital",
#       "address": "3001 W Martin Luther King Jr Blvd, Tampa, FL 33607",
#       "phone": "8138704000",
#       "type": "General Hospital"
#     }
#   ],
#   "preferred_medications": [
#     {
#       "name": "LISINOPRIL",
#       "full_name": "lisinopril 10 MG Oral Tablet",
#       "strength": "10 mg",
#       "route": "Oral Pill",
#       "dose_form": "Oral Tablet",
#       "dose_form_short": "Tab",
#       "rxcui": "314077"
#     },
#     {
#       "name": "METFORMIN",
#       "full_name": "metformin hydrochloride 500 MG Oral Tablet",
#       "strength": "500 mg",
#       "route": "Oral Pill",
#       "dose_form": "Oral Tablet",
#       "dose_form_short": "Tab",
#       "rxcui": "860975"
#     },
#     {
#       "name": "ATORVASTATIN",
#       "full_name": "atorvastatin calcium 20 MG Oral Tablet [Lipitor]",
#       "strength": "20 mg",
#       "route": "Oral Pill",
#       "dose_form": "Oral Tablet",
#       "dose_form_short": "Tab",
#       "rxcui": "617312"
#     }
#   ]
# }

# print(build_plan_listing_url(user_data))