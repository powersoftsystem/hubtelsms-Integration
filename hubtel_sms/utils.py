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
        # Map method names to our event options
        method_event_map = {
            "before_save": "Before Save",
            "after_insert": "After Insert", 
            "before_submit": "Before Submit",
            "on_submit": "On Submit",
            "before_cancel": "Before Cancel", 
            "on_cancel": "On Cancel",
            "on_update_after_submit": "On Update After Submit",
            "before_delete": "Before Delete",
            "after_delete": "After Delete",
            "on_change": "On Change"
        }
        
        event_name = method_event_map.get(method)
        if not event_name:
            return  # Unknown event, skip
        
        # Get all enabled notifications for this document type and event
        filters = {
            "document_type": doc.doctype,
            "event": event_name,
            "enabled": 1
        }
        
        notifications = frappe.get_all("Hubtel SMS Notification", filters=filters)
        
        for notification in notifications:
            try:
                notification_doc = frappe.get_doc("Hubtel SMS Notification", notification.name)
                process_notification(notification_doc, doc)
                
            except Exception as e:
                frappe.log_error(
                    f"Error processing SMS notification {notification.name}: {str(e)}", 
                    "SMS Notification Error"
                )
                
    except Exception as e:
        frappe.log_error(f"Error in sms_notification: {str(e)}", "SMS Notification Error")


def process_notification(notification_doc, doc):
    """
    Process a single SMS notification.
    
    Args:
        notification_doc: The Hubtel SMS Notification document
        doc: The document that triggered the notification
    """
    try:
        # Check conditions if enabled
        if notification_doc.condition and not evaluate_conditions(notification_doc, doc):
            return  # Conditions not met, skip notification
        
        # Get recipient phone number
        phone_number = get_recipient_phone_number(notification_doc, doc)
        if not phone_number:
            frappe.log_error(
                f"No phone number found for notification {notification_doc.name}",
                "SMS Notification Error"
            )
            return
        
        # Process message template
        message = process_message_template(notification_doc.sms_message_template, doc)
        
        # Send SMS (immediately or with delay)
        if notification_doc.send_immediately:
            hubtel_sms = frappe.new_doc("Hubtel SMS")
            hubtel_sms.append("recipients", {
                "recipient": phone_number,
            })
            hubtel_sms.content = message
            hubtel_sms.save()
            frappe.db.commit()

        else:
            # Schedule for later (you can implement background job here)
            delay_minutes = notification_doc.delay_in_minutes or 0
            if delay_minutes > 0:
                # For now, we'll send immediately, but you can implement frappe.enqueue for delays
                frappe.log_error(
                    f"Delayed SMS scheduling not implemented yet. Sending immediately.",
                    "SMS Notification Info"
                )
            hubtel_sms = frappe.new_doc("Hubtel SMS")
            hubtel_sms.append("recipients", {
                "recipient": phone_number,
            })
            hubtel_sms.content = message
            hubtel_sms.save()
            frappe.db.commit()
            
    except Exception as e:
        frappe.log_error(
            f"Error processing notification {notification_doc.name}: {str(e)}",
            "SMS Notification Error"
        )


def evaluate_conditions(notification_doc, doc):
    """
    Evaluate notification conditions.
    
    Args:
        notification_doc: The notification document
        doc: The document being evaluated
        
    Returns:
        bool: True if conditions are met, False otherwise
    """
    try:
        if not notification_doc.condition:
            return True  # No conditions means always send
        
        # Simple condition evaluation using eval (for basic conditions)
        # In production, you might want a more secure condition parser
        condition_text = notification_doc.condition.strip()
        
        if not condition_text:
            return True
        
        # Create a safe context for evaluation
        context = {
            'doc': doc,
            'nowdate': frappe.utils.nowdate,
            'nowtime': frappe.utils.nowtime,
            'now_datetime': frappe.utils.now_datetime,
            'getdate': frappe.utils.getdate,
            'flt': frappe.utils.flt,
            'cint': frappe.utils.cint
        }
        
        # Add doc fields directly to context for easier access
        for field, value in doc.as_dict().items():
            context[field] = value
        
        # Evaluate the condition safely
        try:
            result = eval(condition_text, {"__builtins__": {}}, context)
            return bool(result)
        except Exception as e:
            frappe.log_error(
                f"Error evaluating condition '{condition_text}': {str(e)}",
                "SMS Condition Error"
            )
            return False
            
    except Exception as e:
        frappe.log_error(f"Error in evaluate_conditions: {str(e)}", "SMS Notification Error")
        return False


def get_recipient_phone_number(notification_doc, doc):
    """
    Get the recipient phone number based on notification configuration.
    
    Args:
        notification_doc: The notification document
        doc: The document being processed
        
    Returns:
        str: Phone number or None if not found
    """
    try:
        if notification_doc.send_to_field == "Fixed Number":
            return notification_doc.fixed_number
        
        elif notification_doc.send_to_field == "Field" and notification_doc.recipient_fieldname:
            phone_number = doc.get(notification_doc.recipient_fieldname)
            return phone_number
        
        return None
        
    except Exception as e:
        frappe.log_error(f"Error getting recipient phone number: {str(e)}", "SMS Notification Error")
        return None


def process_message_template(template, doc):
    """
    Process the message template with document data.
    
    Args:
        template: The message template string
        doc: The document with data to substitute
        
    Returns:
        str: Processed message
    """
    try:
        message = template
        doc_dict = doc.as_dict()
        
        # Replace field variables {field_name}
        for field, value in doc_dict.items():
            if value is not None:
                # Handle different data types
                if isinstance(value, datetime):
                    value = value.strftime("%d/%m/%Y %H:%M")
                elif isinstance(value, (int, float)):
                    value = str(value)
                elif value is True:
                    value = "Yes"
                elif value is False:
                    value = "No"
                else:
                    value = str(value)
                
                # Replace both {field} and {doc.field} patterns
                message = message.replace(f"{{{field}}}", value)
                message = message.replace(f"{{doc.{field}}}", value)
        
        # Handle any remaining unreplaced variables
        message = re.sub(r'\{[^}]+\}', '', message)  # Remove unreplaced variables
        
        return message.strip()
        
    except Exception as e:
        frappe.log_error(f"Error processing message template: {str(e)}", "SMS Notification Error")
        return template  # Return original template if processing fails


def send_sms_with_retry(phone_number, message, notification_doc):
    """
    Send SMS with retry logic.
    
    Args:
        phone_number: Recipient phone number
        message: SMS message
        notification_doc: Notification document with retry settings
    """
    max_retries = notification_doc.retry_attempts or 3
    retry_interval = notification_doc.retry_interval or 5
    
    for attempt in range(max_retries + 1):
        try:
            # Clean phone number (remove spaces, ensure proper format)
            clean_phone = clean_phone_number(phone_number)
            if not clean_phone:
                frappe.log_error(f"Invalid phone number format: {phone_number}", "SMS Send Error")
                return
            
            # Send SMS
            response = send_sms(clean_phone, message)
            
            # Log successful send
            log_sms_send(notification_doc.name, clean_phone, message, response, attempt + 1)
            
            # Check if successful (this depends on your Hubtel API response format)
            if response and (response.get("status") == "Success" or response.get("status_code") == 200):
                return  # Success, exit retry loop
                
        except Exception as e:
            frappe.log_error(
                f"SMS send attempt {attempt + 1} failed: {str(e)}",
                "SMS Send Error"
            )
        
        # If not the last attempt, wait before retrying
        if attempt < max_retries:
            import time
            time.sleep(retry_interval * 60)  # Convert minutes to seconds
    
    # All retries failed
    frappe.log_error(
        f"Failed to send SMS after {max_retries + 1} attempts to {phone_number}",
        "SMS Send Failed"
    )


def clean_phone_number(phone_number):
    """
    Clean and format phone number for SMS sending.
    
    Args:
        phone_number: Raw phone number
        
    Returns:
        str: Cleaned phone number or None if invalid
    """
    if not phone_number:
        return None
    
    # Remove all non-digit characters except +
    cleaned = re.sub(r'[^\d+]', '', str(phone_number))
    
    # Remove leading + if present
    if cleaned.startswith('+'):
        cleaned = cleaned[1:]
    
    # Ensure it's a valid length (10-15 digits)
    if len(cleaned) < 10 or len(cleaned) > 15:
        return None
    
    return cleaned


def log_sms_send(notification_name, phone_number, message, response, attempt):
    """
    Log SMS send attempt.
    
    Args:
        notification_name: Name of the notification rule
        phone_number: Recipient phone number
        message: SMS message
        response: API response
        attempt: Attempt number
    """
    try:
        # You can create a custom DocType for SMS logs if needed
        frappe.log_error(
            f"SMS sent via notification '{notification_name}' to {phone_number}\n"
            f"Message: {message}\n"
            f"Attempt: {attempt}\n"
            f"Response: {json.dumps(response)}",
            "SMS Send Log"
        )
    except Exception as e:
        frappe.log_error(f"Error logging SMS send: {str(e)}", "SMS Log Error")
        
