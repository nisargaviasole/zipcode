from mcp.server.fastmcp import FastMCP
import http.client
import json
from urllib.parse import quote
import logging

logger = logging.getLogger(__name__)
mcp = FastMCP("doctor_list")

global_context = {
    "current_zip": None,
    "current_page": 1  # Track the current page
}
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
async def get_doctors_by_zipcode(doctor_name: str, zipcode: str, page: int = 1, items_per_page: int = 5) -> dict:
    """Find doctors in your area by name and location with pagination.
    
    Args:
        doctor_name: Name of doctor or specialty (e.g., "Dr. Smith", "Cardiologist")
        zipcode: 5 digit number (e.g., 33601) for location search
        page: Page number (starting from 1, default: 1)
        items_per_page: Number of doctors per page (default: 5)
    
    Returns:
        Dictionary with doctors and pagination metadata
    """
    print(
        f"Tool get_doctors_by_zipcode called with doctor_name: {doctor_name}, zipcode: {zipcode}, page: {page}, items_per_page: {items_per_page}"
    )
    
    # Update global context
    global_context["current_doctor_name"] = doctor_name
    global_context["current_zip"] = zipcode
    global_context["current_page"] = page
    
    if not check_zip_code_validity(zipcode):
        return {
            "needs_input": "zipcode",
            "message": "Please provide a valid 5-digit zip code to continue the doctor search."
        }
    
    # Get all doctors matching the search
    all_doctors = fetch_doctor(doctor_name, zipcode)
    
    if not all_doctors:
        return {"error": "No doctors found or error fetching data."}
    
    # Calculate pagination details
    total_items = len(all_doctors)
    total_pages = (total_items + items_per_page - 1) // items_per_page
    
    # Adjust page number if out of bounds
    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages
    
    # Calculate slice indices
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)
    
    # Get doctors for current page
    current_page_doctors = all_doctors[start_idx:end_idx]
    
    # Format the doctor data
    formatted_doctors = []
    for doc in current_page_doctors:
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
    
    # Create pagination metadata
    pagination = {
        "current_page": page,
        "total_pages": total_pages,
        "total_items": total_items,
        "items_per_page": items_per_page,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }
    
    return {
        "doctors": formatted_doctors,
        "pagination": pagination
    }

@mcp.tool()
async def next_page(items_per_page: int = None) -> dict:
    """Get the next page of doctor results.
    
    Args:
        items_per_page: Optional - Number of doctors per page
        
    Returns:
        Dictionary with doctors and pagination metadata
    """
    current_doctor_name = global_context.get("current_doctor_name")
    current_zip = global_context.get("current_zip")
    current_page = global_context.get("current_page", 1)
    
    if not current_doctor_name or not current_zip:
        return {"error": "No previous doctor search found. Please search for doctors first."}
    
    # Use current items_per_page if not specified
    if items_per_page is None:
        items_per_page = global_context.get("items_per_page", 5)
    
    return await get_doctors_by_zipcode(current_doctor_name, current_zip, current_page + 1, items_per_page)

@mcp.tool()
async def previous_page(items_per_page: int = None) -> dict:
    """Get the previous page of doctor results.
    
    Args:
        items_per_page: Optional - Number of doctors per page
        
    Returns:
        Dictionary with doctors and pagination metadata
    """
    current_doctor_name = global_context.get("current_doctor_name")
    current_zip = global_context.get("current_zip")
    current_page = global_context.get("current_page", 1)
    
    if not current_doctor_name or not current_zip:
        return {"error": "No previous doctor search found. Please search for doctors first."}
    
    # Use current items_per_page if not specified
    if items_per_page is None:
        items_per_page = global_context.get("items_per_page", 5)
    
    return await get_doctors_by_zipcode(current_doctor_name, current_zip, current_page - 1, items_per_page)

@mcp.tool()
async def go_to_page(page_num: int, items_per_page: int = None) -> dict:
    """Go to a specific page of doctor results.
    
    Args:
        page_num: Page number to navigate to
        items_per_page: Optional - Number of doctors per page
        
    Returns:
        Dictionary with doctors and pagination metadata
    """
    current_doctor_name = global_context.get("current_doctor_name")
    current_zip = global_context.get("current_zip")
    
    if not current_doctor_name or not current_zip:
        return {"error": "No previous doctor search found. Please search for doctors first."}
    
    # Use current items_per_page if not specified
    if items_per_page is None:
        items_per_page = global_context.get("items_per_page", 5)
    
    return await get_doctors_by_zipcode(current_doctor_name, current_zip, page_num, items_per_page)