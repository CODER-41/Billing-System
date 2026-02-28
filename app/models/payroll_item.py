from app.extensions import db
from datetime import datetime

class PayrollItem(db.Model):
    __tablename__ = 'payroll_items'

    id               = db.Column(db.Integer, primary_key=True)
    payroll_run_id   = db.Column(db.Integer, db.ForeignKey('payroll_runs.id'), nullable=False)
    employee_id      = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    bank_account_id  = db.Column(db.Integer, db.ForeignKey('bank_accounts.id'), nullable=False)
    gross_salary     = db.Column(db.Numeric(12, 2), nullable=False)
    total_allowances = db.Column(db.Numeric(12, 2), default=0)
    total_deductions = db.Column(db.Numeric(12, 2), default=0)
    net_salary       = db.Column(db.Numeric(12, 2), nullable=False)
    status           = db.Column(db.String(20), default='pending')
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)

    employee     = db.relationship('Employee', backref='payroll_items')
    bank_account = db.relationship('BankAccount', backref='payroll_items')
    transfers    = db.relationship('Transfer', backref='payroll_item',
                       lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id':               self.id,
            'payroll_run_id':   self.payroll_run_id,
            'employee':         self.employee.to_dict(),
            'bank_account':     self.bank_account.to_dict(),
            'gross_salary':     float(self.gross_salary),
            'total_allowances': float(self.total_allowances),
            'total_deductions': float(self.total_deductions),
            'net_salary':       float(self.net_salary),
            'status':           self.status,
            'created_at':       self.created_at.isoformat()
        }
