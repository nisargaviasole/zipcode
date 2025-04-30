from mcp.server.fastmcp import FastMCP
import http.client
import json
from urllib.parse import quote
import logging

logger = logging.getLogger(__name__)
mcp = FastMCP("hospital_list")

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
async def get_hospitals_by_zipcode(hospital_name: str, zipcode: str, page: int = 1, items_per_page: int = 5) -> dict:
    """Find hospitals in your area by name and location with pagination.
    
    Args:
        hospital_name: Name of hospital or facility (e.g., "Memorial", "General Hospital")
        zipcode: 5 digit number (e.g., 33601) for location search
        page: Page number (starting from 1, default: 1)
        items_per_page: Number of hospitals per page (default: 5)
    
    Returns:
        Dictionary with hospitals and pagination metadata
    """
    print(
        f"Tool get_hospitals_by_zipcode called with hospital_name: {hospital_name}, zipcode: {zipcode}, page: {page}, items_per_page: {items_per_page}"
    )
    
    # Update global context
    global_context["current_hospital_name"] = hospital_name
    global_context["current_hospital_zip"] = zipcode
    global_context["current_hospital_page"] = page
    global_context["hospital_items_per_page"] = items_per_page
    
    if not check_zip_code_validity(zipcode):
        return {
            "needs_input": "zipcode",
            "message": "Please provide a valid 5-digit zip code to continue the hospital search."
        }
    
    # Get all hospitals matching the search
    all_hospitals = fetch_hospital(zipcode, hospital_name)
    
    if not all_hospitals:
        return {"error": "No hospitals found matching your criteria."}
    
    # Calculate pagination details
    total_items = len(all_hospitals)
    total_pages = (total_items + items_per_page - 1) // items_per_page
    
    # Adjust page number if out of bounds
    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages
    
    # Calculate slice indices
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)
    
    # Get hospitals for current page
    current_page_hospitals = all_hospitals[start_idx:end_idx]
    
    # Format the hospital data
    formatted_hospitals = []
    for doc in current_page_hospitals:
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
        "hospitals": formatted_hospitals,
        "pagination": pagination
    }

@mcp.tool()
async def next_hospital_page(items_per_page: int = None) -> dict:
    """Get the next page of hospital results.
    
    Args:
        items_per_page: Optional - Number of hospitals per page
        
    Returns:
        Dictionary with hospitals and pagination metadata
    """
    current_hospital_name = global_context.get("current_hospital_name")
    current_zip = global_context.get("current_hospital_zip")
    current_page = global_context.get("current_hospital_page", 1)
    
    if not current_hospital_name or not current_zip:
        return {"error": "No previous hospital search found. Please search for hospitals first."}
    
    # Use current items_per_page if not specified
    if items_per_page is None:
        items_per_page = global_context.get("hospital_items_per_page", 5)
    
    return await get_hospitals_by_zipcode(current_hospital_name, current_zip, current_page + 1, items_per_page)

@mcp.tool()
async def previous_hospital_page(items_per_page: int = None) -> dict:
    """Get the previous page of hospital results.
    
    Args:
        items_per_page: Optional - Number of hospitals per page
        
    Returns:
        Dictionary with hospitals and pagination metadata
    """
    current_hospital_name = global_context.get("current_hospital_name")
    current_zip = global_context.get("current_hospital_zip")
    current_page = global_context.get("current_hospital_page", 1)
    
    if not current_hospital_name or not current_zip:
        return {"error": "No previous hospital search found. Please search for hospitals first."}
    
    # Use current items_per_page if not specified
    if items_per_page is None:
        items_per_page = global_context.get("hospital_items_per_page", 5)
    
    return await get_hospitals_by_zipcode(current_hospital_name, current_zip, current_page - 1, items_per_page)

@mcp.tool()
async def go_to_hospital_page(page_num: int, items_per_page: int = None) -> dict:
    """Go to a specific page of hospital results.
    
    Args:
        page_num: Page number to navigate to
        items_per_page: Optional - Number of hospitals per page
        
    Returns:
        Dictionary with hospitals and pagination metadata
    """
    current_hospital_name = global_context.get("current_hospital_name")
    current_zip = global_context.get("current_hospital_zip")
    
    if not current_hospital_name or not current_zip:
        return {"error": "No previous hospital search found. Please search for hospitals first."}
    
    # Use current items_per_page if not specified
    if items_per_page is None:
        items_per_page = global_context.get("hospital_items_per_page", 5)
    
    return await get_hospitals_by_zipcode(current_hospital_name, current_zip, page_num, items_per_page)
