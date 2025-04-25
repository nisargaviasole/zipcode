from mcp.server.fastmcp import FastMCP
import http.client
import json
from urllib.parse import quote
import logging

logger = logging.getLogger(__name__)
mcp = FastMCP("medicine_list")


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
async def get_medicine_list(medicine_name: str) -> dict:
    """Get Medicine List and details.

    Args:
        medicine_name: Name of the medicine
    """
    medicine_list = fetch_medicine(medicine_name)
    if not medicine_list:
        return {"error": "No medicines found or error fetching data."}

    formatted_medicines = []
    for medicine in medicine_list:
        medicine_info = {
            "name": medicine.get("name", "N/A"),
            "strength": medicine.get("strength", "N/A"),
            "full_name": medicine.get(
                "full_Name", "N/A"
            )
        }
    formatted_medicines.append(medicine_info)

    return {"medicines": formatted_medicines}
