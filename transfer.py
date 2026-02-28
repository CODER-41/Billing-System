from app.extensions import db
from datetime import datetime

class Transfer(db.Model):
    __tablename__ = 'transfers'

    id                      = db.Column(db.Integer, primary_key=True)
    payroll_item_id         = db.Column(db.Integer, db.ForeignKey('payroll_items.id'), nullable=False)
    paystack_transfer_code  = db.Column(db.String(100))
    paystack_reference      = db.Column(db.String(255), unique=True, nullable=False)
    amount                  = db.Column(db.Numeric(12, 2), nullable=False)
    status                  = db.Column(db.String(20), default='pending')
    failure_reason          = db.Column(db.Text, nullable=True)
    initiated_at            = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at            = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            'id':                     self.id,
            'payroll_item_id':        self.payroll_item_id,
            'paystack_transfer_code': self.paystack_transfer_code,
            'paystack_reference':     self.paystack_reference,
            'amount':                 float(self.amount),
            'status':                 self.status,
            'failure_reason':         self.failure_reason,
            'initiated_at':           self.initiated_at.isoformat(),
            'completed_at':           self.completed_at.isoformat() if self.completed_at else None
        }
