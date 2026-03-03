from flask import Blueprint, request, jsonify, current_app
from app.services.paystack_service import PaystackService

bp = Blueprint("webhooks", __name__)

@bp.route("/paystack", methods=["POST"])
def paystack_webhook():
    signature = request.headers.get("X-Paystack-Signature", "")
    payload   = request.get_data()
    secret    = current_app.config["PAYSTACK_SECRET_KEY"]

    if not PaystackService.verify_webhook_signature(payload, signature, secret):
        return jsonify({"message": "Invalid signature"}), 401

    event = request.get_json()
    from app.tasks.payroll_tasks import process_webhook_task
    process_webhook_task.delay(event)
    return jsonify({"status": "ok"}), 200
