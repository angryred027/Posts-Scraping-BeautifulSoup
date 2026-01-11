from datetime import datetime

def log_debug(message: str):
    print(f"[{datetime.utcnow().strftime('%H:%M:%S')}] {message}")