from mcp.server.fastmcp import FastMCP
import http.client
import json
import logging

logger = logging.getLogger(__name__)

mcp = FastMCP("zipcode")

def check_zip_code_validity(zip_code):
    try:
        conn = http.client.HTTPSConnection('gateway-dev.nextere.com')
        headers = {"accept": "application/json"}
    
        endpoint = f"/api/quotingtool-service/geography/zip-by-details?zipCode={zip_code}&year=2024"

        conn.request("GET", endpoint, headers=headers)
        res = conn.getresponse()
        data = res.read().decode("utf-8")
        logger.info(f"Zip code {zip_code} response: {data}")
        if res.status == 200:
            json_data = json.loads(data)
            if json_data[0]["name"]:
                return True
            else:
                return False
        else:
            return False
    except Exception as e:
        logger.error(f"Error validating zip code {zip_code}: {e}")
        return None
    

def fetchCountyData(zipcode):
    try:
        conn = http.client.HTTPSConnection('gateway-dev.nextere.com')
        headers = {"accept": "application/json"}
        endpoint = f"/api/quotingtool-service/geography/zip-by-details?zipCode={zipcode}&year=2024"
        conn.request("GET", endpoint, headers=headers)
        res = conn.getresponse()
        fetch_data_of_county = res.read().decode("utf-8")
        fetch_county_data = json.loads(fetch_data_of_county)
        # Check if data is a list and has at least one item
        if isinstance(fetch_county_data, list) and fetch_county_data:
            return fetch_county_data[0]
        else:
            return {"error": "Invalid or unsupported zip code. Please provide a valid zip code."}

    except Exception as e:
        logger.error(f"Error while fetching county data for zip code {zipcode}: {str(e)}")
        return {"error": "Failed to fetch county data due to a server error."}

@mcp.tool()
async def get_county_info(zipcode):
    """
    Trigger this tool whenever a zipcode is mentioned.
    
    This tool provides county information when someone:
    - Mentions any 5-digit number that could be a zipcode
    - Says "my zipcode is [number]"
    - Shares just a zipcode with no other context
    - Asks anything related to a zipcode
    
    Args:
        zipcode: 5 digit numbers (e.g. 33601)
    """
    print("Zipcode Tool called")
    validate_zip = check_zip_code_validity(zipcode)
    
    if validate_zip == None:
        return {"alert_status": "Invalid zipcode", "county_data": None}
    elif validate_zip:
        zip_data = fetchCountyData(zipcode)
        return {
            "alert_status": "County information found",
            "county_data": zip_data
        }
    else:
        return {"alert_status": "Invalid zipcode", "county_data": None}
        