from flask import Blueprint, request, jsonify, make_response
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
from app.extensions import db, bcrypt, limiter
from app.models.user import User
from app.utils.responses import success_response, error_response

bp = Blueprint("auth", __name__)

@bp.route("/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    data = request.get_json()
    if not data or not data.get("email") or not data.get("password"):
        return error_response("Email and password are required", 400)

    user = User.query.filter_by(email=data["email"]).first()
    if not user or not bcrypt.check_password_hash(user.password_hash, data["password"]):
        return error_response("Invalid email or password", 401)

    access_token  = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    response = make_response(success_response({
        "access_token": access_token,
        "user": user.to_dict()
    }))
    response.set_cookie(
        "refresh_token", refresh_token,
        httponly=True,
        secure=False,
        samesite="Lax",
        max_age=604800
    )
    return response

@bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    if not user:
        return error_response("User not found", 404)
    access_token = create_access_token(identity=str(user_id))
    return success_response({
        "access_token": access_token,
        "user": user.to_dict()
    })

@bp.route("/logout", methods=["POST"])
@jwt_required()
def logout():
    response = make_response(success_response({"message": "Logged out successfully"}))
    response.delete_cookie("refresh_token")
    return response

@bp.route("/change-password", methods=["POST"])
@jwt_required()
def change_password():
    user_id = get_jwt_identity()
    user = User.query.get(int(user_id))
    data = request.get_json()

    if not data.get("current_password") or not data.get("new_password"):
        return error_response("current_password and new_password are required", 400)

    if not bcrypt.check_password_hash(user.password_hash, data["current_password"]):
        return error_response("Current password is incorrect", 401)

    if len(data["new_password"]) < 8:
        return error_response("New password must be at least 8 characters", 400)

    user.password_hash = bcrypt.generate_password_hash(data["new_password"]).decode("utf-8")
    db.session.commit()
    return success_response({"message": "Password changed successfully"})
