import requests
import frappe
from frappe import _
import json
from datetime import datetime
import re

HUBTEL_SMS_URL = "https://sms.hubtel.com/v1/messages/send"
CLIENT_ID = "qyqerqtz"
CLIENT_SECRET = "howmtaqy"
SENDER_ID = "StillEVen"

def replace_template_fields(message_template, doc):
    """
    Replace curly brackets in message template with actual field values from document.
    
    Args:
        message_template (str): The message template with curly brackets
        doc: The document object
        
    Returns:
        str: Message with replaced field values
    """
    if not message_template or not doc:
        return message_template
    
    # Find all field names in curly brackets
    field_pattern = r'\{([^}]+)\}'
    matches = re.findall(field_pattern, message_template)
    
    # Replace each field with its value
    for field_name in matches:
        field_value = ""
        
        # Handle nested fields (e.g., customer_name)
        if hasattr(doc, field_name):
            field_value = getattr(doc, field_name)
        elif hasattr(doc, 'as_dict'):
            # Try to get from document dictionary
            doc_dict = doc.as_dict()
            field_value = doc_dict.get(field_name, "")
        
        # Convert to string and handle None values
        if field_value is None:
            field_value = ""
        else:
            field_value = str(field_value)
        
        # Replace the curly bracket placeholder
        message_template = message_template.replace(f'{{{field_name}}}', field_value)
    
    return message_template

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
        "clientsecret": settings.get_password("client_secret"),
        "from": settings.sender_id,
        "to": to,
        "content": content
    }
    response = requests.get(HUBTEL_SMS_URL, params=params)
    try:
        return response.json()
    except Exception:
        return {"status_code": response.status_code, "text": response.text}


@frappe.whitelist()
def sms_notification(doc, method=None):
    """
    Process SMS notifications for document events.
    
    Args:
        doc: The document that triggered the event
        method: The event method (before_save, after_insert, etc.)
    """
    try:
        # Skip processing for Error Log documents to prevent recursion
        if doc.doctype == "Error Log":
            return
            
        # Map method names to our event options
        method_event_map = {
            "after_insert": "after_insert", 
            "on_submit": "on_submit",
            # Add other methods as needed
            "on_update": "on_update",
            "on_cancel": "on_cancel"
        }
        
        # Check if method is supported
        if method not in method_event_map:
            return
        
        # Use the mapped event name
        event_name = method_event_map[method]
        
        filters = {
            "document_type": doc.doctype,
            "event": event_name,  # Use mapped event name
            "enabled": 1
        }
        
        # Check if any notifications exist
        if not frappe.db.exists("Hubtel SMS Notification", filters):
            return
            
        notifications = frappe.get_all("Hubtel SMS Notification", filters=filters)
        
        for notification in notifications:
            try:
                notification_doc = frappe.get_doc("Hubtel SMS Notification", notification.name)
                
                # Create SMS document with proper error handling
                sms = frappe.new_doc("Hubtel SMS")
                
                # Handle recipient logic
                if notification_doc.send_to_field == "Fixed Number":
                    if not notification_doc.fixed_number:
                        continue
                        
                    sms.append("recipients", {
                        "recipient": frappe.db.get_value(doc.doctype, doc.name, notification_doc.recipient_fieldname),
                    })
                else:
                    sms.append("recipients", {
                        "recipient": frappe.db.get_value(doc.doctype, doc.name, notification_doc.recipient_fieldname),
                    })
                
                # Replace template fields with actual values
                processed_message = replace_template_fields(notification_doc.sms_message_template, doc)
                sms.message = processed_message
               
                # Save SMS with flags to prevent recursion
                sms.flags.ignore_permissions = True
                sms.flags.ignore_mandatory = True
                sms.insert()
                
                # Submit the SMS to trigger sending
                sms.submit()
                
                # Don't commit here - let the main transaction handle it
                print(f"SMS created and submitted successfully for notification {notification.name}")
                
            except Exception as e:
                # Use a simple print statement instead of log_error to avoid recursion
                print(f"Error processing SMS notification {notification.name}: {str(e)}")
                # Continue with other notifications
                continue
                
    except Exception as e:
        # Use a simple print statement instead of log_error to avoid recursion
        print(f"Error in sms_notification: {str(e)}")
        # Don't re-raise the exception to prevent breaking the main document save


