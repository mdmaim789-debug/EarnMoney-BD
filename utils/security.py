import hmac
import hashlib
from urllib.parse import parse_qs
from config.settings import settings

def verify_telegram_webapp_data(init_data: str) -> dict:
    """
    Verify Telegram Web App initData
    Returns parsed data if valid, raises ValueError if invalid
    """
    try:
        # Parse the init_data
        parsed = parse_qs(init_data)
        
        # Extract hash
        received_hash = parsed.get('hash', [None])[0]
        if not received_hash:
            raise ValueError("No hash provided")
        
        # Remove hash from data
        data_check_string_parts = []
        for key in sorted(parsed.keys()):
            if key != 'hash':
                value = parsed[key][0]
                data_check_string_parts.append(f"{key}={value}")
        
        data_check_string = '\n'.join(data_check_string_parts)
        
        # Create secret key
        secret_key = hmac.new(
            b"WebAppData",
            settings.BOT_TOKEN.encode(),
            hashlib.sha256
        ).digest()
        
        # Calculate hash
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Verify hash
        if not hmac.compare_digest(calculated_hash, received_hash):
            raise ValueError("Invalid hash")
        
        # Parse user data
        import json
        user_data = json.loads(parsed.get('user', ['{}'])[0])
        
        return {
            'user': user_data,
            'auth_date': parsed.get('auth_date', [None])[0],
            'hash': received_hash
        }
        
    except Exception as e:
        raise ValueError(f"Telegram data verification failed: {str(e)}")

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in settings.ADMIN_IDS
