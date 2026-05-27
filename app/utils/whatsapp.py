"""
WhatsApp Integration
RecruitPro CRM
"""

import re
from typing import Optional


WHATSAPP_BASE = "https://wa.me/"

# Pre-built message templates
MESSAGE_TEMPLATES = {
    "joining_reminder": (
        "📋 *Joining Reminder*\n\n"
        "Dear {name},\n\n"
        "This is a reminder that your joining date at *{company}* is scheduled for *{joining_date}*.\n\n"
        "Please ensure you carry all required documents:\n"
        "• Offer Letter\n"
        "• Aadhar Card / PAN Card\n"
        "• Educational Certificates\n"
        "• Previous Experience Letters\n\n"
        "Best regards,\nRecruitPro Team"
    ),
    "document_reminder": (
        "📄 *Document Submission Reminder*\n\n"
        "Dear {name},\n\n"
        "We noticed that some of your documents are pending submission.\n\n"
        "Kindly share the following at the earliest:\n"
        "• Updated Resume\n"
        "• Educational Certificates\n"
        "• Government ID Proof\n\n"
        "Please contact us if you need any assistance.\n\n"
        "Best regards,\nRecruitPro Team"
    ),
    "selection_congratulations": (
        "🎉 *Congratulations!*\n\n"
        "Dear {name},\n\n"
        "We are pleased to inform you that you have been *selected* for the position of "
        "*{designation}* at *{company}*.\n\n"
        "Your expected joining date is: *{joining_date}*\n\n"
        "We will be in touch with further details. Congratulations once again!\n\n"
        "Best regards,\nRecruitPro Team"
    ),
    "follow_up": (
        "👋 *Quick Follow-up*\n\n"
        "Dear {name},\n\n"
        "This is a quick follow-up regarding your placement status.\n\n"
        "Kindly get in touch with us at your earliest convenience so we can assist you better.\n\n"
        "Best regards,\nRecruitPro Team"
    ),
    "payment_confirmation": (
        "💰 *Payment Confirmation Request*\n\n"
        "Dear Team,\n\n"
        "This is to confirm that *{name}* has successfully completed *90 days* "
        "at your organization.\n\n"
        "As per our agreement, the placement fee of *₹{amount}* is now due.\n\n"
        "Kindly arrange the payment at the earliest.\n\n"
        "Thank you for your continued partnership.\n\n"
        "Best regards,\nRecruitPro Team"
    ),
}


def clean_phone(phone: str) -> str:
    """Normalize phone number for WhatsApp URL."""
    digits = re.sub(r"\D", "", str(phone))
    # Add India country code if not present
    if len(digits) == 10:
        digits = "91" + digits
    elif len(digits) == 11 and digits.startswith("0"):
        digits = "91" + digits[1:]
    return digits


def get_whatsapp_url(phone: str, message: str = "") -> str:
    """Generate WhatsApp URL for a phone number with optional pre-filled message."""
    cleaned = clean_phone(phone)
    if message:
        import urllib.parse
        encoded = urllib.parse.quote(message)
        return f"{WHATSAPP_BASE}{cleaned}?text={encoded}"
    return f"{WHATSAPP_BASE}{cleaned}"


def get_template_message(template_key: str, **kwargs) -> str:
    """Fill a message template with provided values."""
    template = MESSAGE_TEMPLATES.get(template_key, "")
    try:
        return template.format(**kwargs)
    except KeyError as e:
        return template  # Return unfilled if key missing


def get_all_templates() -> list:
    return [
        {"key": "joining_reminder", "label": "📋 Joining Reminder"},
        {"key": "document_reminder", "label": "📄 Document Reminder"},
        {"key": "selection_congratulations", "label": "🎉 Selection Congratulations"},
        {"key": "follow_up", "label": "👋 General Follow-up"},
        {"key": "payment_confirmation", "label": "💰 Payment Confirmation (Company)"},
    ]
