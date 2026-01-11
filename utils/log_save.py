from typing import Optional
from datetime import datetime
from app.models.event_log import EVENT_STATUS, EVENT_TYPE
from sqlalchemy import text
import json

async def log_save(
    db,
    uuid: str,
    event_status: EVENT_STATUS,
    event_type: EVENT_TYPE,
    reason: Optional[str] = None,
    metadata: Optional[dict] = None,
    created_by: Optional[str] = "system",
):
    metadata_json = json.dumps(metadata) if metadata else None

    sql = text("""
    WITH updated AS (
        UPDATE bol_logs
        SET attempt_count = attempt_count + 1,
            event_status = :event_status,
            reason = :reason,
            metadata = :metadata,
            created_by = :created_by,
            created_at = :created_at
        WHERE uuid = :uuid AND event_type = :event_type
        RETURNING *
    )
    INSERT INTO bol_logs (uuid, event_status, event_type, attempt_count, reason, metadata, created_by, created_at)
    SELECT :uuid, :event_status, :event_type, 1, :reason, :metadata, :created_by, :created_at
    WHERE NOT EXISTS (SELECT 1 FROM updated)
    RETURNING *;
    """)

    params = {
        "uuid": uuid,
        "event_status": event_status.value,
        "event_type": event_type.value,
        "reason": reason,
        "metadata": metadata_json,
        "created_by": created_by,
        "created_at": datetime.utcnow(),
    }

    result = await db.execute(sql, params)
    await db.commit()
    row = result.first()  
    return dict(row._mapping) if row else None
