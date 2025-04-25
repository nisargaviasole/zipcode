from mcp.server.fastmcp import FastMCP
import http.client
import json
from urllib.parse import quote
import logging

logger = logging.getLogger(__name__)
mcp = FastMCP("doctor_list")

# Import check_zip_code_validity safely
try:
    from zipcode import check_zip_code_validity
except ImportError as e:
    logger.error(f"Failed to import check_zip_code_validity: {e}")
    def check_zip_code_validity(zip_code):
        logger.warning("check_zip_code_validity not available; returning False")
        return False

def fetch_doctor(query, zipcode):
    conn = None
    try:
        conn = http.client.HTTPSConnection('gateway-dev.nextere.com')
        headers = {"accept": "application/json"}
        encoded_query = quote(query)
        endpoint = f"/api/quotingtool-service/provider-and-drug-coverage/search-providers-all?zipcode={zipcode}&query={encoded_query}&year=2024&providerType=Individual"
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
        logger.error(f"Error fetching doctor list: {e}")
        return None
    finally:
        if conn:
            conn.close()

@mcp.tool()
async def get_doctor_list_by_zipcode(doctor_name: str, zipcode: str) -> dict:
    """Get doctor list for a validated zipcode.

    Args:
        doctor_name: Name of the doctor
        zipcode: 5 digit number (e.g., 33601)
    """
    if not check_zip_code_validity(zipcode):
        return {
            "needs_input": "zipcode",
            "message": "Please provide a valid 5-digit zip code to continue the hospital search."
        }
    
    doctor_list = fetch_doctor(doctor_name, zipcode)
    if not doctor_list:
        return {"error": "No doctors found or error fetching data."}
    
    formatted_doctors = []
    for doc in doctor_list:
        provider = doc.get("provider", {})
        address = doc.get("address", {})
        name = provider.get("name", "N/A")
        phone = address.get("phone", "N/A")
        specialties = ", ".join(provider.get("specialties", [])) or "N/A"
        street1 = address.get("street1", "")
        street2 = address.get("street2", "")
        city = address.get("city", "")
        state = address.get("state", "")
        zipcode = address.get("zipcode", "")
        full_address = f"{street1} {street2}, {city}, {state} {zipcode}".strip().replace(" ,", ",")
        formatted_doctors.append({
            "name": name,
            "phone": phone,
            "specialties": specialties,
            "address": full_address
        })
    
    return {"doctors": formatted_doctors}