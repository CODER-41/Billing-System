from app import create_app
from app.extensions import db, bcrypt
from app.models.user import User

app = create_app("development")

with app.app_context():
    existing = User.query.filter_by(email="admin@payrollke.com").first()
    if existing:
        print("Admin already exists!")
    else:
        admin = User(
            name="Super Admin",
            email="admin@payrollke.com",
            password_hash=bcrypt.generate_password_hash("Admin@1234").decode("utf-8"),
            role="super_admin"
        )
        db.session.add(admin)
        db.session.commit()
        print(f"Super Admin created! ID: {admin.id}")
        print("Email:    admin@payrollke.com")
        print("Password: Admin@1234")
