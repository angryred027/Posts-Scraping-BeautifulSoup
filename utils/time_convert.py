from datetime import datetime, timezone, timedelta

def format_human_time(value) -> str:
    """
    Accepts:
      - datetime
      - ISO string

    Returns:
      Today at 7:21 AM
      Yesterday at 6:56 AM
      Jan 11 at 7:21 AM
    """

    # Normalize input
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        dt = datetime.fromisoformat(value)
    else:
        return ""

    # Assume UTC if no tzinfo
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    today = now.date()
    yesterday = today - timedelta(days=1)

    time_part = dt.strftime("%I:%M %p").lstrip("0")

    if dt.date() == today:
        return f"Today at {time_part}"
    elif dt.date() == yesterday:
        return f"Yesterday at {time_part}"
    else:
        return dt.strftime("%b %d at %I:%M %p").replace(" 0", " ")
