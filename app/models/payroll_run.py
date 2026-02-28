from app.extensions import db
from datetime import datetime

class PayrollRun(db.Model):
    __tablename__ = 'payroll_runs'

    id               = db.Column(db.Integer, primary_key=True)
    title            = db.Column(db.String(255), nullable=False)
    pay_period_start = db.Column(db.Date, nullable=False)
    pay_period_end   = db.Column(db.Date, nullable=False)
    payment_date     = db.Column(db.Date, nullable=False)
    status           = db.Column(db.String(50), default='draft')
    total_amount     = db.Column(db.Numeric(14, 2), default=0)
    created_by       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    approved_by      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)

    items           = db.relationship('PayrollItem', backref='payroll_run',
                          lazy=True, cascade='all, delete-orphan')
    creator         = db.relationship('User', foreign_keys=[created_by])
    approver        = db.relationship('User', foreign_keys=[approved_by])

    def to_dict(self):
        return {
            'id':               self.id,
            'title':            self.title,
            'pay_period_start': self.pay_period_start.isoformat(),
            'pay_period_end':   self.pay_period_end.isoformat(),
            'payment_date':     self.payment_date.isoformat(),
            'status':           self.status,
            'total_amount':     float(self.total_amount),
            'created_by':       self.created_by,
            'approved_by':      self.approved_by,
            'created_at':       self.created_at.isoformat()
        }
