import requests
import os

class WhatsAppService:
    def __init__(self):
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID', '808921198974802')
        self.token = os.getenv('WHATSAPP_TOKEN', 'EAAZAErWsgvsIBPlmpJAo1tGuVxXaLDcjyPAuNAlQfZBG1w4U337P1etgINLjLlOCLbtWqttnmsIpTXqn9vjKqAajjoUHjTFpUHZC2M1ex62ZBRPLqXuolfzFIyZClYgmurq4fG4kRYrZBrRey2h3QFJvR7ODlHaIB9QBM7t8jU0wpTi0z8QteN64nX4PPNlVf31gZDZD')
        self.base_url = f"https://graph.facebook.com/v17.0/{self.phone_number_id}/messages"
        
    def send_message(self, to_phone, message):
        """
        Send WhatsApp message to a phone number
        Phone number should be in format: 1234567890 (without country code prefix)
        """
        try:
            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }
            
            # Format phone number (add country code if needed)
            # Assuming Indian numbers - adjust as needed
            if not to_phone.startswith('91') and len(to_phone) == 10:
                to_phone = '91' + to_phone
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to_phone,
                "type": "text",
                "text": {
                    "body": message
                }
            }
            
            response = requests.post(self.base_url, json=payload, headers=headers)
            
            if response.status_code == 200:
                print(f"WhatsApp message sent to {to_phone}")
                return True
            else:
                print(f"WhatsApp API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"Error sending WhatsApp message: {str(e)}")
            return False
    
    def send_attendance_reminder(self, to_phone, name, week):
        """
        Send formatted attendance reminder via WhatsApp
        """
        message = f"""Hello {name},

📊 Attendance Reminder

This is a friendly reminder to submit your attendance for week {week}.

Please log in to the system and complete your attendance at your earliest convenience.

Thank you!"""
        
        return self.send_message(to_phone, message)

# Create global instance
whatsapp_service = WhatsAppService()