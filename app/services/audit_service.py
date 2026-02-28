from app.extensions import db
from app.models.audit_log import AuditLog
from flask import request

def log_action(user_id: int, action: str, entity_type: str,
               entity_id: int, metadata: dict = None):
    try:
        log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            metadata=metadata or {},
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f'Audit log error: {e}')
