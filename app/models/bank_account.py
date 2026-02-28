from app.extensions import db
from datetime import datetime

class BankAccount(db.Model):
    __tablename__ = 'bank_accounts'

    id                      = db.Column(db.Integer, primary_key=True)
    employee_id             = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    bank_name               = db.Column(db.String(100), nullable=False)
    bank_code               = db.Column(db.String(20), nullable=False)
    account_number          = db.Column(db.String(50), nullable=False)
    account_name            = db.Column(db.String(255), nullable=False)
    recipient_type          = db.Column(db.String(20), default='bank')
    paystack_recipient_code = db.Column(db.String(100))
    is_primary              = db.Column(db.Boolean, default=False)
    created_at              = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':                      self.id,
            'employee_id':             self.employee_id,
            'bank_name':               self.bank_name,
            'bank_code':               self.bank_code,
            'account_number':          self.account_number,
            'account_name':            self.account_name,
            'recipient_type':          self.recipient_type,
            'paystack_recipient_code': self.paystack_recipient_code,
            'is_primary':              self.is_primary,
            'created_at':              self.created_at.isoformat()
        }
