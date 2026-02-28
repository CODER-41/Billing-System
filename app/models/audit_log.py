from app.extensions import db
from datetime import datetime

class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action      = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(50))
    entity_id   = db.Column(db.Integer)
    extra_data  = db.Column(db.JSON, default=dict)
    ip_address  = db.Column(db.String(45))
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id":          self.id,
            "user_id":     self.user_id,
            "action":      self.action,
            "entity_type": self.entity_type,
            "entity_id":   self.entity_id,
            "extra_data":  self.extra_data,
            "ip_address":  self.ip_address,
            "created_at":  self.created_at.isoformat()
        }
