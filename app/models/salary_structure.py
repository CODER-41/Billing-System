from app.extensions import db
from datetime import datetime

class SalaryStructure(db.Model):
    __tablename__ = 'salary_structures'

    id               = db.Column(db.Integer, primary_key=True)
    employee_id      = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
    basic_salary     = db.Column(db.Numeric(12, 2), nullable=False)
    allowances       = db.Column(db.JSON, default=dict)
    deductions       = db.Column(db.JSON, default=dict)
    net_salary       = db.Column(db.Numeric(12, 2), nullable=False)
    effective_date   = db.Column(db.Date, nullable=False)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id':             self.id,
            'employee_id':    self.employee_id,
            'basic_salary':   float(self.basic_salary),
            'allowances':     self.allowances,
            'deductions':     self.deductions,
            'net_salary':     float(self.net_salary),
            'effective_date': self.effective_date.isoformat(),
            'created_at':     self.created_at.isoformat()
        }
