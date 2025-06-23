import requests
import frappe

HUBTEL_SMS_URL = "https://sms.hubtel.com/v1/messages/send"
CLIENT_ID = "qyqerqtz"
CLIENT_SECRET = "howmtaqy"
SENDER_ID = "StillEVen"

@frappe.whitelist(allow_guest=True)
def send_sms(to, content):
    """
    Send an SMS using Hubtel SMS Gateway.

    Args:
        to (str): Recipient phone number (international format, e.g. 233XXXXXXXXX)
        content (str): Message content

    Returns:
        dict: Response from Hubtel API
    """
    settings = frappe.get_doc("Hubtel SMS Settings")
    params = {
        "clientid": settings.client_id,
        "clientsecret": settings.client_secret,
        "from": settings.sender_id,
        "to": to,
        "content": content
    }
    response = requests.get(HUBTEL_SMS_URL, params=params)
    try:
        return response.json()
    except Exception:
        return {"status_code": response.status_code, "text": response.text}
