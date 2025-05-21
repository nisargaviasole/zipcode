from mcp.server.fastmcp import FastMCP
import requests
import logging
import json
import http.client
from urllib.parse import quote

gateway_nextere_url = "gateway-dev.nextere.com"
tennatid = "f91e8e24-b430-eeb6-e67e-3a1287e79d01"

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
        
book=book_appointment("2025-05-22T14:30:00")
print(book)