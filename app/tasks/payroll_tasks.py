from app.extensions import db
from app.models.payroll_run import PayrollRun
from app.models.payroll_item import PayrollItem
from app.models.transfer import Transfer
from app.utils.currency import to_paystack_amount
from app.services.paystack_service import PaystackService
import uuid
import os
from datetime import datetime

paystack = PaystackService()

def process_payroll_task_fn(payroll_run_id):
    run = PayrollRun.query.get(payroll_run_id)
    if not run:
        return

    items = PayrollItem.query.filter_by(
        payroll_run_id=payroll_run_id, status="pending"
    ).all()

    is_test = os.getenv("FLASK_ENV") == "development"

    for item in items:
        try:
            if not item.bank_account.paystack_recipient_code:
                item.status = "failed"
                db.session.commit()
                continue

            reference = f"payroll_{run.id}_item_{item.id}_{uuid.uuid4().hex[:8]}"

            if is_test:
                transfer = Transfer(
                    payroll_item_id=item.id,
                    paystack_transfer_code=f"TRF_test_{uuid.uuid4().hex[:12]}",
                    paystack_reference=reference,
                    amount=item.net_salary,
                    status="success",
                    completed_at=datetime.utcnow()
                )
                db.session.add(transfer)
                item.status = "paid"
                db.session.commit()
            else:
                response = paystack.initiate_transfer(
                    amount=to_paystack_amount(float(item.net_salary)),
                    recipient_code=item.bank_account.paystack_recipient_code,
                    reference=reference,
                    reason=f"{run.title} - {item.employee.full_name}"
                )
                transfer = Transfer(
                    payroll_item_id=item.id,
                    paystack_transfer_code=response.get("transfer_code"),
                    paystack_reference=reference,
                    amount=item.net_salary,
                    status="pending"
                )
                db.session.add(transfer)
                item.status = "processing"
                db.session.commit()

        except Exception as e:
            item.status = "failed"
            db.session.commit()

    _check_and_finalize_run(run)

def process_webhook_task_fn(event):
    event_type = event.get("event")
    data       = event.get("data", {})
    reference  = data.get("reference")

    if not reference:
        return

    transfer = Transfer.query.filter_by(paystack_reference=reference).first()
    if not transfer:
        return

    if event_type == "transfer.success":
        transfer.status = "success"
        transfer.payroll_item.status = "paid"
        transfer.completed_at = datetime.utcnow()

    elif event_type in ["transfer.failed", "transfer.reversed"]:
        transfer.status = "failed"
        transfer.payroll_item.status = "failed"
        transfer.failure_reason = data.get("reason", "Unknown failure")
        transfer.completed_at = datetime.utcnow()

    db.session.commit()
    _check_and_finalize_run(transfer.payroll_item.payroll_run)

def retry_transfer_task_fn(item_id):
    item = PayrollItem.query.get(item_id)
    if not item:
        return

    is_test = os.getenv("FLASK_ENV") == "development"

    try:
        reference = f"retry_{item.payroll_run_id}_item_{item.id}_{uuid.uuid4().hex[:8]}"

        if is_test:
            transfer = Transfer(
                payroll_item_id=item.id,
                paystack_transfer_code=f"TRF_test_{uuid.uuid4().hex[:12]}",
                paystack_reference=reference,
                amount=item.net_salary,
                status="success",
                completed_at=datetime.utcnow()
            )
            db.session.add(transfer)
            item.status = "paid"
            db.session.commit()
        else:
            response = paystack.initiate_transfer(
                amount=to_paystack_amount(float(item.net_salary)),
                recipient_code=item.bank_account.paystack_recipient_code,
                reference=reference,
                reason=f"Retry - {item.payroll_run.title} - {item.employee.full_name}"
            )
            transfer = Transfer(
                payroll_item_id=item.id,
                paystack_transfer_code=response.get("transfer_code"),
                paystack_reference=reference,
                amount=item.net_salary,
                status="pending"
            )
            db.session.add(transfer)
            item.status = "processing"
            db.session.commit()

    except Exception as e:
        item.status = "failed"
        db.session.commit()

def _check_and_finalize_run(run):
    items    = PayrollItem.query.filter_by(payroll_run_id=run.id).all()
    statuses = {item.status for item in items}
    if "processing" not in statuses and "pending" not in statuses:
        run.status = "completed" if "failed" not in statuses else "failed"
        db.session.commit()

try:
    from celery_worker import celery

    @celery.task(name="process_payroll_task")
    def process_payroll_task(payroll_run_id):
        process_payroll_task_fn(payroll_run_id)

    @celery.task(name="process_webhook_task")
    def process_webhook_task(event):
        process_webhook_task_fn(event)

    @celery.task(name="retry_transfer_task")
    def retry_transfer_task(item_id):
        retry_transfer_task_fn(item_id)

except Exception:
    def process_payroll_task(payroll_run_id):
        process_payroll_task_fn(payroll_run_id)

    def process_webhook_task(event):
        process_webhook_task_fn(event)

    def retry_transfer_task(item_id):
        retry_transfer_task_fn(item_id)
