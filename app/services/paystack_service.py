import requests
import hmac
import hashlib
from flask import current_app

class PaystackService:

    def _headers(self):
        return {
            "Authorization": f"Bearer {current_app.config['PAYSTACK_SECRET_KEY']}",
            "Content-Type": "application/json"
        }

    def _base(self):
        return current_app.config["PAYSTACK_BASE_URL"]

    def resolve_account(self, account_number: str, bank_code: str):
        try:
            res = requests.get(
                f"{self._base()}/bank/resolve",
                params={"account_number": account_number, "bank_code": bank_code},
                headers=self._headers(), timeout=10
            )
            if res.status_code == 200 and res.json().get("status"):
                return res.json()["data"]
            return None
        except Exception as e:
            current_app.logger.error(f"Paystack resolve error: {e}")
            return None

    def create_recipient(self, recipient_type, name, account_number, bank_code, currency="KES"):
        try:
            payload = {
                "type": "nuban" if recipient_type == "bank" else "mobile_money",
                "name": name,
                "account_number": account_number,
                "bank_code": bank_code,
                "currency": currency
            }
            res = requests.post(
                f"{self._base()}/transferrecipient",
                json=payload, headers=self._headers(), timeout=10
            )
            if res.status_code in [200, 201] and res.json().get("status"):
                return res.json()["data"]
            current_app.logger.error(f"Paystack create recipient failed: {res.text}")
            return None
        except Exception as e:
            current_app.logger.error(f"Paystack recipient error: {e}")
            return None

    def get_balance(self):
        try:
            res = requests.get(
                f"{self._base()}/balance",
                headers=self._headers(), timeout=10
            )
            if res.status_code == 200 and res.json().get("status"):
                balances = res.json()["data"]
                kes = next((b for b in balances if b["currency"] == "KES"), None)
                if kes:
                    return kes["balance"] / 100
            return None
        except Exception as e:
            current_app.logger.error(f"Paystack balance error: {e}")
            return None

    def initiate_transfer(self, amount: int, recipient_code: str,
                          reference: str, reason: str):
        payload = {
            "source":    "balance",
            "amount":    amount,
            "recipient": recipient_code,
            "reason":    reason,
            "reference": reference
        }
        res = requests.post(
            f"{self._base()}/transfer",
            json=payload, headers=self._headers(), timeout=30
        )
        if res.status_code in [200, 201]:
            return res.json()["data"]
        raise Exception(f"Paystack transfer failed: {res.text}")

    @staticmethod
    def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
        computed = hmac.new(
            secret.encode("utf-8"), payload, hashlib.sha512
        ).hexdigest()
        return hmac.compare_digest(computed, signature)
