def to_paystack_amount(amount_in_kes: float) -> int:
    """Convert KES to Paystack cents. KES 85,000 -> 8,500,000"""
    return int(round(float(amount_in_kes) * 100))

def from_paystack_amount(cents: int) -> float:
    """Convert Paystack cents to KES. 8,500,000 -> 85,000.0"""
    return cents / 100
