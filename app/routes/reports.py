from flask import Blueprint, request
from app.models.payroll_run import PayrollRun
from app.models.payroll_item import PayrollItem
from app.models.employee import Employee
from app.models.audit_log import AuditLog
from app.utils.decorators import require_role
from app.utils.responses import success_response, error_response, paginated_response

bp = Blueprint("reports", __name__)

@bp.route("/payroll-summary/<int:run_id>", methods=["GET"])
@require_role("super_admin", "hr_admin", "finance_admin")
def payroll_summary(run_id):
    run   = PayrollRun.query.get_or_404(run_id)
    items = PayrollItem.query.filter_by(payroll_run_id=run_id).all()
    summary = {
        "payroll_run":       run.to_dict(),
        "total_employees":   len(items),
        "total_gross":       sum(float(i.gross_salary) for i in items),
        "total_allowances":  sum(float(i.total_allowances) for i in items),
        "total_deductions":  sum(float(i.total_deductions) for i in items),
        "total_net":         sum(float(i.net_salary) for i in items),
        "paid_count":        sum(1 for i in items if i.status == "paid"),
        "failed_count":      sum(1 for i in items if i.status == "failed"),
        "pending_count":     sum(1 for i in items if i.status == "pending"),
    }
    return success_response(summary)

@bp.route("/employee-payslip", methods=["GET"])
@require_role("super_admin", "hr_admin", "finance_admin")
def employee_payslip():
    employee_id = request.args.get("employee_id", type=int)
    run_id      = request.args.get("payroll_run_id", type=int)
    if not employee_id or not run_id:
        return error_response("employee_id and payroll_run_id are required", 400)
    employee = Employee.query.get_or_404(employee_id)
    run      = PayrollRun.query.get_or_404(run_id)
    item     = PayrollItem.query.filter_by(
        payroll_run_id=run_id, employee_id=employee_id
    ).first()
    if not item:
        return error_response("No payroll item found for this employee in this run", 404)
    payslip = {
        "employee":        employee.to_dict(),
        "payroll_run":     run.to_dict(),
        "payroll_item":    item.to_dict(),
        "period":          f"{run.pay_period_start} to {run.pay_period_end}",
        "payment_date":    run.payment_date.isoformat(),
    }
    return success_response(payslip)

@bp.route("/audit-logs", methods=["GET"])
@require_role("super_admin")
def audit_logs():
    page     = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    paginated = AuditLog.query.order_by(AuditLog.created_at.desc())        .paginate(page=page, per_page=per_page, error_out=False)
    return paginated_response(
        [l.to_dict() for l in paginated.items],
        paginated.total, page, per_page
    )
