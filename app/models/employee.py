from app.extensions import db
from datetime import datetime

class Employee(db.Model):
    __tablename__ = 'employees'

    id              = db.Column(db.Integer, primary_key=True)
    employee_code   = db.Column(db.String(50), unique=True, nullable=False)
    full_name       = db.Column(db.String(255), nullable=False)
    email           = db.Column(db.String(255), unique=True, nullable=False)
    phone           = db.Column(db.String(20))
    department      = db.Column(db.String(100))
    position        = db.Column(db.String(100))
    employment_type = db.Column(db.String(50), default='full-time')
    status          = db.Column(db.String(20), default='active')
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    bank_accounts     = db.relationship('BankAccount', backref='employee',
                            lazy=True, cascade='all, delete-orphan')
    salary_structures = db.relationship('SalaryStructure', backref='employee',
                            order_by='SalaryStructure.effective_date.desc()',
                            lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id':              self.id,
            'employee_code':   self.employee_code,
            'full_name':       self.full_name,
            'email':           self.email,
            'phone':           self.phone,
            'department':      self.department,
            'position':        self.position,
            'employment_type': self.employment_type,
            'status':          self.status,
            'created_at':      self.created_at.isoformat()
        }
