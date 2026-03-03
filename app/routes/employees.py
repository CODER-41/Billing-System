from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity
from app.extensions import db
from app.models.employee import Employee
from app.models.bank_account import BankAccount
from app.models.salary_structure import SalaryStructure
from app.utils.decorators import require_role
from app.utils.responses import success_response, error_response, paginated_response
from app.services.audit_service import log_action
from datetime import date

bp = Blueprint("employees", __name__)

@bp.route("/", methods=["GET"])
@require_role("super_admin", "hr_admin", "finance_admin")
def list_employees():
    page       = request.args.get("page", 1, type=int)
    per_page   = request.args.get("per_page", 20, type=int)
    department = request.args.get("department")
    status     = request.args.get("status", "active")
    search     = request.args.get("search")
    query = Employee.query
    if department:
        query = query.filter_by(department=department)
    if status:
        query = query.filter_by(status=status)
    if search:
        query = query.filter(Employee.full_name.ilike(f"%{search}%"))
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    return paginated_response(
        [e.to_dict() for e in paginated.items],
        paginated.total, page, per_page
    )

@bp.route("/<int:emp_id>", methods=["GET"])
@require_role("super_admin", "hr_admin", "finance_admin")
def get_employee(emp_id):
    employee = Employee.query.get_or_404(emp_id)
    return success_response(employee.to_dict())

@bp.route("/", methods=["POST"])
@require_role("super_admin", "hr_admin")
def create_employee():
    data = request.get_json()
    required = ["full_name", "email", "department", "position"]
    for field in required:
        if not data.get(field):
            return error_response(f"{field} is required", 400)
    if Employee.query.filter_by(email=data["email"]).first():
        return error_response("An employee with this email already exists", 409)
    count    = Employee.query.count()
    emp_code = f"EMP{str(count + 1).zfill(4)}"
    employee = Employee(
        employee_code=emp_code,
        full_name=data["full_name"],
        email=data["email"],
        phone=data.get("phone"),
        department=data["department"],
        position=data["position"],
        employment_type=data.get("employment_type", "full-time"),
        status="active"
    )
    db.session.add(employee)
    db.session.commit()
    log_action(get_jwt_identity(), "CREATE_EMPLOYEE", "employee", employee.id)
    return success_response(employee.to_dict(), 201)

@bp.route("/<int:emp_id>", methods=["PUT"])
@require_role("super_admin", "hr_admin")
def update_employee(emp_id):
    employee = Employee.query.get_or_404(emp_id)
    data     = request.get_json()
    fields = ["full_name", "email", "phone", "department", "position", "employment_type"]
    for field in fields:
        if field in data:
            setattr(employee, field, data[field])
    db.session.commit()
    log_action(get_jwt_identity(), "UPDATE_EMPLOYEE", "employee", employee.id)
    return success_response(employee.to_dict())

@bp.route("/<int:emp_id>", methods=["DELETE"])
@require_role("super_admin", "hr_admin")
def deactivate_employee(emp_id):
    employee = Employee.query.get_or_404(emp_id)
    employee.status = "inactive"
    db.session.commit()
    log_action(get_jwt_identity(), "DEACTIVATE_EMPLOYEE", "employee", employee.id)
    return success_response({"message": f"{employee.full_name} has been deactivated"})

@bp.route("/<int:emp_id>/bank-accounts", methods=["GET"])
@require_role("super_admin", "hr_admin", "finance_admin")
def list_bank_accounts(emp_id):
    Employee.query.get_or_404(emp_id)
    accounts = BankAccount.query.filter_by(employee_id=emp_id).all()
    return success_response([a.to_dict() for a in accounts])

@bp.route("/<int:emp_id>/bank-accounts", methods=["POST"])
@require_role("super_admin", "hr_admin")
def add_bank_account(emp_id):
    employee = Employee.query.get_or_404(emp_id)
    data     = request.get_json()
    required = ["bank_name", "bank_code", "account_number", "account_name"]
    for field in required:
        if not data.get(field):
            return error_response(f"{field} is required", 400)
    existing_count = BankAccount.query.filter_by(employee_id=emp_id).count()
    is_primary     = existing_count == 0
    account = BankAccount(
        employee_id=emp_id,
        bank_name=data["bank_name"],
        bank_code=data["bank_code"],
        account_number=data["account_number"],
        account_name=data["account_name"],
        recipient_type=data.get("recipient_type", "bank"),
        paystack_recipient_code=data.get("paystack_recipient_code"),
        is_primary=is_primary
    )
    db.session.add(account)
    db.session.commit()
    log_action(get_jwt_identity(), "ADD_BANK_ACCOUNT", "bank_account", account.id)
    return success_response(account.to_dict(), 201)

@bp.route("/<int:emp_id>/bank-accounts/<int:account_id>/set-primary", methods=["PUT"])
@require_role("super_admin", "hr_admin")
def set_primary_account(emp_id, account_id):
    Employee.query.get_or_404(emp_id)
    BankAccount.query.filter_by(employee_id=emp_id).update({"is_primary": False})
    account = BankAccount.query.get_or_404(account_id)
    account.is_primary = True
    db.session.commit()
    return success_response({"message": "Primary account updated"})

@bp.route("/<int:emp_id>/salary", methods=["GET"])
@require_role("super_admin", "hr_admin", "finance_admin")
def get_salary(emp_id):
    Employee.query.get_or_404(emp_id)
    salary = SalaryStructure.query.filter_by(employee_id=emp_id)        .order_by(SalaryStructure.effective_date.desc()).first()
    if not salary:
        return error_response("No salary structure found for this employee", 404)
    return success_response(salary.to_dict())

@bp.route("/<int:emp_id>/salary/history", methods=["GET"])
@require_role("super_admin", "hr_admin", "finance_admin")
def get_salary_history(emp_id):
    Employee.query.get_or_404(emp_id)
    history = SalaryStructure.query.filter_by(employee_id=emp_id)        .order_by(SalaryStructure.effective_date.desc()).all()
    return success_response([s.to_dict() for s in history])

@bp.route("/<int:emp_id>/salary", methods=["POST"])
@require_role("super_admin", "hr_admin")
def create_salary(emp_id):
    Employee.query.get_or_404(emp_id)
    data = request.get_json()
    if not data.get("basic_salary"):
        return error_response("basic_salary is required", 400)
    if not data.get("effective_date"):
        return error_response("effective_date is required", 400)
    basic            = float(data["basic_salary"])
    allowances       = data.get("allowances", {})
    deductions       = data.get("deductions", {})
    total_allowances = sum(float(v) for v in allowances.values())
    total_deductions = sum(float(v) for v in deductions.values())
    gross            = basic + total_allowances
    net              = gross - total_deductions
    if net < 0:
        return error_response("Net salary cannot be negative. Check your deductions.", 400)
    salary = SalaryStructure(
        employee_id=emp_id,
        basic_salary=basic,
        allowances=allowances,
        deductions=deductions,
        net_salary=net,
        effective_date=date.fromisoformat(data["effective_date"])
    )
    db.session.add(salary)
    db.session.commit()
    log_action(get_jwt_identity(), "CREATE_SALARY", "salary_structure", salary.id)
    return success_response(salary.to_dict(), 201)
