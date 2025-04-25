from mcp.server.fastmcp import FastMCP
import http.client
import json
from urllib.parse import quote
import logging

logger = logging.getLogger(__name__)
mcp = FastMCP("hospital_list")

# Import check_zip_code_validity safely
try:
    from zipcode import check_zip_code_validity
except ImportError as e:
    logger.error(f"Failed to import check_zip_code_validity: {e}")
    def check_zip_code_validity(zip_code):
        logger.warning("check_zip_code_validity not available; returning False")
        return False

def fetch_hospital(zipcode, query):
    try:
        conn = http.client.HTTPSConnection('gateway-dev.nextere.com')
        headers = {"accept": "application/json"}

        encoded_query = quote(query)

        endpoint = f"/api/quotingtool-service/provider-and-drug-coverage/search-providers-all?zipcode={zipcode}&query={encoded_query}&year=2024&providerType=Facility"
        conn.request("GET", endpoint, headers=headers)
        res = conn.getresponse()
        data = res.read().decode("utf-8")

        if res.status == 200:
            json_data = json.loads(data)
            return json_data
        else:
            logger.error(f"HTTP error occurred: {res.status} {res.reason}")
            return None
    except Exception as e:
        print("error", e)
        logger.error(f"error:{str(e)}")
        return None
    

@mcp.tool()
async def get_hospital_list_by_zipcode(hospital_name: str, zipcode: str) -> dict:
    """Get hospital list for a validated zipcode.

    Args:
        hospital_name: Name of the hospital
        zipcode: 5 digit number (e.g., 33601)
    """
    if not check_zip_code_validity(zipcode):
        return {
            "needs_input": "zipcode",
            "message": "Please provide a valid 5-digit zip code to continue the hospital search."
        }
    
    hospitals_lists = fetch_hospital(zipcode,hospital_name)
    if not hospitals_lists:
        return {"error": "No hospitals found or error fetching data."}
    
    formatted_hospitals = []
    for doc in hospitals_lists:
        provider = doc.get("provider", {})
        address = doc.get("address", {})
        name = provider.get("name", "N/A")
        taxonomy = provider.get("taxonomy", "N/A")
        phone = address.get("phone", "N/A")
        specialties = ", ".join(provider.get("specialties", [])) or "N/A"
        street1 = address.get("street1", "")
        street2 = address.get("street2", "")
        city = address.get("city", "")
        state = address.get("state", "")
        zipcode = address.get("zipcode", "")
        full_address = f"{street1} {street2}, {city}, {state} {zipcode}".strip().replace(" ,", ",")
        formatted_hospitals.append({
            "name": name,
            "phone": phone,
            "specialties": specialties,
            "taxonomy": taxonomy,
            "address": full_address
        })
        
    return {"hospitals": formatted_hospitals}