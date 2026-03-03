from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity
from app.extensions import db
from app.models.payroll_run import PayrollRun
from app.models.payroll_item import PayrollItem
from app.models.employee import Employee
from app.models.bank_account import BankAccount
from app.models.salary_structure import SalaryStructure
from app.models.transfer import Transfer
from app.utils.decorators import require_role
from app.utils.responses import success_response, error_response, paginated_response
from app.services.audit_service import log_action
from datetime import date

bp = Blueprint("payroll", __name__)

@bp.route("/", methods=["GET"])
@require_role("super_admin", "hr_admin", "finance_admin")
def list_payroll_runs():
    page     = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    status   = request.args.get("status")
    query    = PayrollRun.query
    if status:
        query = query.filter_by(status=status)
    query = query.order_by(PayrollRun.created_at.desc())
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    return paginated_response(
        [r.to_dict() for r in paginated.items],
        paginated.total, page, per_page
    )

@bp.route("/<int:run_id>", methods=["GET"])
@require_role("super_admin", "hr_admin", "finance_admin")
def get_payroll_run(run_id):
    run = PayrollRun.query.get_or_404(run_id)
    return success_response(run.to_dict())

@bp.route("/", methods=["POST"])
@require_role("super_admin", "hr_admin")
def create_payroll_run():
    data    = request.get_json()
    user_id = int(get_jwt_identity())

    required = ["title", "pay_period_start", "pay_period_end", "payment_date"]
    for field in required:
        if not data.get(field):
            return error_response(f"{field} is required", 400)

    run = PayrollRun(
        title=data["title"],
        pay_period_start=date.fromisoformat(data["pay_period_start"]),
        pay_period_end=date.fromisoformat(data["pay_period_end"]),
        payment_date=date.fromisoformat(data["payment_date"]),
        created_by=user_id,
        status="draft"
    )
    db.session.add(run)
    db.session.flush()

    active_employees = Employee.query.filter_by(status="active").all()
    total = 0

    for emp in active_employees:
        salary = SalaryStructure.query.filter_by(employee_id=emp.id)            .order_by(SalaryStructure.effective_date.desc()).first()
        bank = BankAccount.query.filter_by(employee_id=emp.id, is_primary=True).first()

        if not salary or not bank:
            continue

        item = PayrollItem(
            payroll_run_id=run.id,
            employee_id=emp.id,
            bank_account_id=bank.id,
            gross_salary=float(salary.basic_salary) + sum(float(v) for v in salary.allowances.values()),
            total_allowances=sum(float(v) for v in salary.allowances.values()),
            total_deductions=sum(float(v) for v in salary.deductions.values()),
            net_salary=float(salary.net_salary),
            status="pending"
        )
        db.session.add(item)
        total += float(salary.net_salary)

    run.total_amount = total
    db.session.commit()
    log_action(user_id, "CREATE_PAYROLL_RUN", "payroll_run", run.id)
    return success_response(run.to_dict(), 201)

@bp.route("/<int:run_id>", methods=["PUT"])
@require_role("super_admin", "hr_admin")
def update_payroll_run(run_id):
    run = PayrollRun.query.get_or_404(run_id)
    if run.status != "draft":
        return error_response("Only draft payroll runs can be updated", 422)
    data = request.get_json()
    if "title" in data:
        run.title = data["title"]
    if "payment_date" in data:
        run.payment_date = date.fromisoformat(data["payment_date"])
    db.session.commit()
    return success_response(run.to_dict())

@bp.route("/<int:run_id>", methods=["DELETE"])
@require_role("super_admin", "hr_admin")
def delete_payroll_run(run_id):
    run = PayrollRun.query.get_or_404(run_id)
    if run.status != "draft":
        return error_response("Only draft payroll runs can be deleted", 422)
    db.session.delete(run)
    db.session.commit()
    return success_response({"message": "Payroll run deleted"})

@bp.route("/<int:run_id>/submit", methods=["POST"])
@require_role("super_admin", "hr_admin")
def submit_payroll(run_id):
    run = PayrollRun.query.get_or_404(run_id)
    if run.status != "draft":
        return error_response("Only draft payrolls can be submitted", 422)
    run.status = "pending_approval"
    db.session.commit()
    log_action(int(get_jwt_identity()), "SUBMIT_PAYROLL", "payroll_run", run.id)
    return success_response(run.to_dict())

@bp.route("/<int:run_id>/approve", methods=["POST"])
@require_role("super_admin", "finance_admin")
def approve_payroll(run_id):
    run     = PayrollRun.query.get_or_404(run_id)
    user_id = int(get_jwt_identity())

    if run.status != "pending_approval":
        return error_response("Only pending payrolls can be approved", 422)
    if run.created_by == user_id:
        return error_response("You cannot approve a payroll run you created", 403)

    run.status      = "approved"
    run.approved_by = user_id
    db.session.commit()
    log_action(user_id, "APPROVE_PAYROLL", "payroll_run", run.id)
    return success_response(run.to_dict())

@bp.route("/<int:run_id>/reject", methods=["POST"])
@require_role("super_admin", "finance_admin")
def reject_payroll(run_id):
    run     = PayrollRun.query.get_or_404(run_id)
    user_id = int(get_jwt_identity())
    if run.status != "pending_approval":
        return error_response("Only pending payrolls can be rejected", 422)
    run.status = "draft"
    db.session.commit()
    log_action(user_id, "REJECT_PAYROLL", "payroll_run", run.id)
    return success_response(run.to_dict())

@bp.route("/<int:run_id>/process", methods=["POST"])
@require_role("super_admin", "finance_admin")
def process_payroll(run_id):
    run     = PayrollRun.query.get_or_404(run_id)
    user_id = int(get_jwt_identity())
    if run.status != "approved":
        return error_response("Only approved payrolls can be processed", 422)
    run.status = "processing"
    db.session.commit()
    from app.tasks.payroll_tasks import process_payroll_task
    process_payroll_task.delay(run_id)
    log_action(user_id, "PROCESS_PAYROLL", "payroll_run", run.id)
    return success_response({"message": "Payroll processing started", "status": "processing"})

@bp.route("/<int:run_id>/items", methods=["GET"])
@require_role("super_admin", "hr_admin", "finance_admin")
def get_payroll_items(run_id):
    PayrollRun.query.get_or_404(run_id)
    items = PayrollItem.query.filter_by(payroll_run_id=run_id).all()
    return success_response([i.to_dict() for i in items])

@bp.route("/<int:run_id>/items/<int:item_id>/retry", methods=["POST"])
@require_role("super_admin", "finance_admin")
def retry_payroll_item(run_id, item_id):
    item = PayrollItem.query.get_or_404(item_id)
    if item.status != "failed":
        return error_response("Only failed items can be retried", 422)
    item.status = "processing"
    db.session.commit()
    from app.tasks.payroll_tasks import retry_transfer_task
    retry_transfer_task.delay(item_id)
    return success_response({"message": "Retry initiated"})
