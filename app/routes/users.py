from flask import Blueprint, request
from flask_jwt_extended import get_jwt_identity
from app.extensions import db, bcrypt
from app.models.user import User
from app.utils.decorators import require_role
from app.utils.responses import success_response, error_response, paginated_response
from app.services.audit_service import log_action

bp = Blueprint("users", __name__)

@bp.route("/", methods=["GET"])
@require_role("super_admin")
def list_users():
    page     = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    paginated = User.query.paginate(page=page, per_page=per_page, error_out=False)
    return paginated_response(
        [u.to_dict() for u in paginated.items],
        paginated.total, page, per_page
    )

@bp.route("/<int:user_id>", methods=["GET"])
@require_role("super_admin")
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return success_response(user.to_dict())

@bp.route("/", methods=["POST"])
@require_role("super_admin")
def create_user():
    data = request.get_json()
    required = ["name", "email", "password", "role"]
    for field in required:
        if not data.get(field):
            return error_response(f"{field} is required", 400)

    valid_roles = ["super_admin", "hr_admin", "finance_admin"]
    if data["role"] not in valid_roles:
        return error_response(f"Role must be one of: {', '.join(valid_roles)}", 400)

    if User.query.filter_by(email=data["email"]).first():
        return error_response("A user with this email already exists", 409)

    if len(data["password"]) < 8:
        return error_response("Password must be at least 8 characters", 400)

    user = User(
        name=data["name"],
        email=data["email"],
        password_hash=bcrypt.generate_password_hash(data["password"]).decode("utf-8"),
        role=data["role"]
    )
    db.session.add(user)
    db.session.commit()
    log_action(get_jwt_identity(), "CREATE_USER", "user", user.id)
    return success_response(user.to_dict(), 201)

@bp.route("/<int:user_id>", methods=["PUT"])
@require_role("super_admin")
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()

    if "name" in data:
        user.name = data["name"]
    if "role" in data:
        valid_roles = ["super_admin", "hr_admin", "finance_admin"]
        if data["role"] not in valid_roles:
            return error_response(f"Role must be one of: {', '.join(valid_roles)}", 400)
        user.role = data["role"]
    if "email" in data:
        existing = User.query.filter_by(email=data["email"]).first()
        if existing and existing.id != user_id:
            return error_response("Email already in use", 409)
        user.email = data["email"]

    db.session.commit()
    log_action(get_jwt_identity(), "UPDATE_USER", "user", user.id)
    return success_response(user.to_dict())

@bp.route("/<int:user_id>", methods=["DELETE"])
@require_role("super_admin")
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    current_user_id = int(get_jwt_identity())
    if user.id == current_user_id:
        return error_response("You cannot delete your own account", 400)
    db.session.delete(user)
    db.session.commit()
    log_action(current_user_id, "DELETE_USER", "user", user_id)
    return success_response({"message": "User deleted successfully"})
