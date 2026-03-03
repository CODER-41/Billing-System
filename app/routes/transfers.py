from flask import Blueprint, request
from app.models.transfer import Transfer
from app.models.payroll_item import PayrollItem
from app.utils.decorators import require_role
from app.utils.responses import success_response, paginated_response

bp = Blueprint("transfers", __name__)

@bp.route("/", methods=["GET"])
@require_role("super_admin", "finance_admin")
def list_transfers():
    page     = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    status   = request.args.get("status")
    query    = Transfer.query
    if status:
        query = query.filter_by(status=status)
    query = query.order_by(Transfer.initiated_at.desc())
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    return paginated_response(
        [t.to_dict() for t in paginated.items],
        paginated.total, page, per_page
    )

@bp.route("/<int:transfer_id>", methods=["GET"])
@require_role("super_admin", "finance_admin")
def get_transfer(transfer_id):
    transfer = Transfer.query.get_or_404(transfer_id)
    return success_response(transfer.to_dict())
