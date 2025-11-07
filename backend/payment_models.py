from flask import jsonify
from typing import Optional
from datetime import datetime

class SubscribeRequest:
    def __init__(self, user_id: str, email: str, name: str, plan_name: str, amount: int, currency: str):
        self.user_id = user_id
        self.email = email
        self.name = name
        self.plan_name = plan_name
        self.amount = amount
        self.currency = currency

class SubscribeResponse:
    def __init__(self, payment_link: str, tx_ref: str, status: str):
        self.payment_link = payment_link
        self.tx_ref = tx_ref
        self.status = status

    def to_dict(self):
        return {
            "payment_link": self.payment_link,
            "tx_ref": self.tx_ref,
            "status": self.status
        }

class WebhookResponse:
    def __init__(self, status: str):
        self.status = status

    def to_dict(self):
        return {"status": self.status}

class SubscriptionDoc:
    def __init__(self, user_id: str, email: str, plan_name: str, plan_amount: int, payment_ref: str, status: str, created_at: datetime, renewal_date: Optional[datetime] = None):
        self.user_id = user_id
        self.email = email
        self.plan_name = plan_name
        self.plan_amount = plan_amount
        self.payment_ref = payment_ref
        self.status = status
        self.created_at = created_at
        self.renewal_date = renewal_date

class UserDoc:
    def __init__(self, _id: str, subscription_status: str, plan_id: str, renewal_date: datetime):
        self._id = _id
        self.subscription_status = subscription_status
        self.plan_id = plan_id
        self.renewal_date = renewal_date
