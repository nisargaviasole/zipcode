from mcp.server.fastmcp import FastMCP
import http.client
import json
from urllib.parse import quote
import logging

logger = logging.getLogger(__name__)
mcp = FastMCP("medicine_list")

global_context = {
    "current_zip": None,
    "current_page": 1  # Track the current page
}


def fetch_medicine(query):
    try:
        conn = http.client.HTTPSConnection("gateway-dev.nextere.com")
        headers = {"accept": "application/json"}

        encoded_query = quote(query)

        endpoint = f"/api/quotingtool-service/provider-and-drug-coverage/drugs-by-name-autocomplete?name={encoded_query}&year=2024"
        conn.request("GET", endpoint, headers=headers)
        res = conn.getresponse()
        data = res.read().decode("utf-8")

        if res.status == 200:
            json_data = json.loads(data)
            conn.close()
            return json_data
        else:
            print(f"HTTP error occurred: {res.status} {res.reason}")
            return None
    except Exception as e:
        logger.error(f"error:{str(e)}")
        return None

@mcp.tool()
async def get_medicine_list(medicine_name: str, page: int = 1, items_per_page: int = 5) -> dict:
    """Find detailed information about medications and drugs with pagination.
    
    Args:
        medicine_name: Name of medicine or drug (e.g., "Lipitor", "Amoxicillin")
        page: Page number (starting from 1, default: 1)
        items_per_page: Number of medications per page (default: 5)
        
    Returns:
        Dictionary with medicines and pagination metadata
    """
    print(
        f"Tool get_medicine_list called with medicine_name: {medicine_name}, page: {page}, items_per_page: {items_per_page}"
    )
    
    # Update global context
    global_context["current_medicine_name"] = medicine_name
    global_context["current_medicine_page"] = page
    global_context["medicine_items_per_page"] = items_per_page
    
    # Get all medicines matching the search
    all_medicines = fetch_medicine(medicine_name)
    
    if not all_medicines:
        return {"error": "No medicines found matching your criteria."}
    
    # Calculate pagination details
    total_items = len(all_medicines)
    total_pages = (total_items + items_per_page - 1) // items_per_page
    
    # Adjust page number if out of bounds
    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages
    
    # Calculate slice indices
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, total_items)
    
    # Get medicines for current page
    current_page_medicines = all_medicines[start_idx:end_idx]
    
    # Format the medicine data
    formatted_medicines = []
    for medicine in current_page_medicines:
        medicine_info = {
            "name": medicine.get("name", "N/A"),
            "strength": medicine.get("strength", "N/A"),
            "full_name": medicine.get("full_Name", "N/A")
        }
        formatted_medicines.append(medicine_info)
    
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
        "medicines": formatted_medicines,
        "pagination": pagination
    }

@mcp.tool()
async def next_medicine_page(items_per_page: int = None) -> dict:
    """Get the next page of medicine results.
    
    Args:
        items_per_page: Optional - Number of medicines per page
        
    Returns:
        Dictionary with medicines and pagination metadata
    """
    current_medicine_name = global_context.get("current_medicine_name")
    current_page = global_context.get("current_medicine_page", 1)
    
    if not current_medicine_name:
        return {"error": "No previous medicine search found. Please search for medicines first."}
    
    # Use current items_per_page if not specified
    if items_per_page is None:
        items_per_page = global_context.get("medicine_items_per_page", 5)
    
    return await get_medicine_list(current_medicine_name, current_page + 1, items_per_page)

@mcp.tool()
async def previous_medicine_page(items_per_page: int = None) -> dict:
    """Get the previous page of medicine results.
    
    Args:
        items_per_page: Optional - Number of medicines per page
        
    Returns:
        Dictionary with medicines and pagination metadata
    """
    current_medicine_name = global_context.get("current_medicine_name")
    current_page = global_context.get("current_medicine_page", 1)
    
    if not current_medicine_name:
        return {"error": "No previous medicine search found. Please search for medicines first."}
    
    # Use current items_per_page if not specified
    if items_per_page is None:
        items_per_page = global_context.get("medicine_items_per_page", 5)
    
    return await get_medicine_list(current_medicine_name, current_page - 1, items_per_page)

@mcp.tool()
async def go_to_medicine_page(page_num: int, items_per_page: int = None) -> dict:
    """Go to a specific page of medicine results.
    
    Args:
        page_num: Page number to navigate to
        items_per_page: Optional - Number of medicines per page
        
    Returns:
        Dictionary with medicines and pagination metadata
    """
    current_medicine_name = global_context.get("current_medicine_name")
    
    if not current_medicine_name:
        return {"error": "No previous medicine search found. Please search for medicines first."}
    
    # Use current items_per_page if not specified
    if items_per_page is None:
        items_per_page = global_context.get("medicine_items_per_page", 5)
    
    return await get_medicine_list(current_medicine_name, page_num, items_per_page)