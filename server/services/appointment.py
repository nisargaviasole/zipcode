from mcp.server.fastmcp import FastMCP
import logging
import json
import http.client
from urllib.parse import quote

logger = logging.getLogger(__name__)
# You can keep using the same MCP instance or create a new one
mcp = FastMCP("appointment")  # Uncomment if you want a separate MCP instance

# Define the gateway URL
gateway_nextere_url = "gateway-dev.nextere.com"
tennatid = "f91e8e24-b430-eeb6-e67e-3a1287e79d01"

def check_appointment_in_data(appointment_datetime, agent_username="yash12", tenant_id="f91e8e24-b430-eeb6-e67e-3a1287e79d01"):
    """
    Check if an appointment is available at the specified date and time.
    
    Args:
        appointment_datetime (str): Date and time for the appointment in ISO format
        agent_username (str): Username of the agent (default: "yash12")
        tenant_id (str): Tenant ID for the request
        
    Returns:
        dict: JSON response containing availability information
    """
    try:
        conn = http.client.HTTPSConnection(gateway_nextere_url)
        headers = {"accept": "application/json"}

        # URL encode the parameters
        encoded_agent_id = quote(agent_username)
        encoded_datetime = quote(appointment_datetime)

        # Construct the endpoint with encoded values
        endpoint = f"/api/quotingtool-service/agent-agency-detail/agent-available-date?dateTime={encoded_datetime}&agentUserName={encoded_agent_id}&tenantid={tenant_id}"

        print(f"Checking appointment availability at endpoint: {endpoint}")
        
        conn.request("GET", endpoint, headers=headers)
        res = conn.getresponse()
        data = res.read().decode("utf-8")
        print("res.status",res.status)
        if res.status == 200:
            json_data = json.loads(data)
            print("jsondata",json_data)
            return json_data
        else:
            logger.error(f"Error checking appointment: Status {res.status}, Response: {data}")
            return {"available": False, "error": f"Status code: {res.status}"}
    
    except Exception as e:
        logger.error(f"Exception checking appointment: {e}")
        return {"available": False, "error": str(e)}

def book_appointment(appointment_datetime):
    """
    Book an appointment for the user with the specified agent.
    
    Args:
        user_data (dict): Dictionary containing user information
        appointment_datetime (str): Date and time for the appointment
        
    Returns:
        dict: Booking confirmation or error information
    """
    try:
        payload = {
            "start": appointment_datetime,
            "agentId": "1218378",
            "title": f"Appointment book",
            "description": f"Scheduled appointment on {appointment_datetime}",
        }
        conn = http.client.HTTPSConnection(gateway_nextere_url)

        # Define the headers
        headers = {"accept": "application/json", "Content-Type": "application/json"}

        # Convert the payload to JSON string
        json_payload = json.dumps(payload)

        # Send the request
        endpoint = f"/api/quotingtool-service/agent-agency-detail/appointment?tenantid={tennatid}"
        conn.request("POST", endpoint, body=json_payload, headers=headers)
        res = conn.getresponse()
        data = res.read().decode("utf-8")
        
        if res.status == 200 or res.status == 201:
            json_data = json.loads(data)
            return {
                "appointment_confirmed": True,
                "appointment_start_time": json_data['start'],
                "appointment_end_time": json_data['end'],
                "message": json_data['description']
            }
        else:
            logger.error(f"Error booking appointment: Status {res.status}, Response: {data}")
            return {
                "appointment_confirmed": False,
                "message": f"Failed to book appointment. Status code: {res.status}"
            }
    
    except Exception as e:
        logger.error(f"Exception booking appointment: {e}")
        return {
            "appointment_confirmed": False,
            "message": f"Error: {str(e)}"
        }


@mcp.tool()
async def check_appointment_availability(appointment_datetime):
    """
    Check if an appointment slot is available at the specified date and time.
    
    Args:
        appointment_datetime (str): Date and time for the appointment in ISO format
                                   (e.g., "2024-05-20T14:30:00")
    
    Returns:
        dict: Dictionary containing:
          - available (bool): Whether the appointment slot is available
          - next_available (str, optional): Next available slot if current one is not available
          - message (str): Informational message about availability
    """
    try:
        print(f"Checking appointment availability for: {appointment_datetime}")
        result = check_appointment_in_data(appointment_datetime)
        print("result", result)
        # Use isAvailable instead of is_available to match API response
        if result and result.get("isAvailable", False):
            return {
                "available": True,
                "message": f"The requested appointment slot on {appointment_datetime} is available."
            }
        else:
            # If the API provides next available slot, include it
            next_available = result.get("availableDate", "")
            return {
                "available": False,
                "next_available": next_available,
                "message": f"The requested appointment slot is not available. Next available slot: {next_available}" if next_available else "The requested appointment slot is not available."
            }
    except Exception as e:
        logger.error(f"Error in check_appointment_availability: {e}")
        return {
            "available": False,
            "message": f"Error checking appointment availability: {str(e)}"
        }

@mcp.tool()
async def schedule_appointment(json_data, appointment_datetime):
    """
    Schedule an appointment with an agent at the specified date and time.
    
    Args:
        json_data (dict): JSON object containing user's profile including:
          - full_name: User's full name
          - email: User's email address
          - phone: User's phone number
          - zip_code: User's zip code
        appointment_datetime (str): Date and time for the appointment in ISO format
                                   (e.g., "2024-05-20T14:30:00")
    
    Returns:
        dict: Dictionary containing:
          - appointment_confirmed (bool): Whether the appointment was successfully booked
          - appointment_id (str, optional): ID of the scheduled appointment if successful
          - appointment_time (str): The scheduled appointment time
          - message (str): Confirmation or error message
    """
    try:
        print(f"Scheduling appointment for: {json_data.get('full_name')} at {appointment_datetime}")
        
        # First check if the appointment slot is available
        availability = check_appointment_in_data(appointment_datetime)
        print(f"Availability check result: {availability}")
        
        # The API is returning 'isAvailable', not 'is_available'
        if not availability or not availability.get("isAvailable", False):
            next_available = availability.get("availableDate", "")
            return {
                "appointment_confirmed": False,
                "message": f"The requested appointment slot is not available. Next available slot: {next_available}" if next_available else "The requested appointment slot is not available."
            }
        
        # If available, book the appointment
        result = book_appointment(appointment_datetime)
        return result
    except Exception as e:
        logger.error(f"Error in schedule_appointment: {e}")
        return {
            "appointment_confirmed": False,
            "message": f"Error scheduling appointment: {str(e)}"
        }