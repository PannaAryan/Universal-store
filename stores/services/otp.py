"""One-time passwords for checkout. Plug an SMS gateway into send_sms()."""

import logging
import secrets
import time

logger = logging.getLogger(__name__)
OTP_TTL = 300
MAX_ATTEMPTS = 5


def send_sms(phone, text):
    logger.info("SMS to %s: %s", phone, text)


def issue(session, phone, store_name):
    code = f"{secrets.randbelow(900000) + 100000}"
    session["checkout_otp"] = {"phone": phone, "code": code, "at": time.time(), "tries": 0}
    send_sms(phone, f"{code} is your {store_name} order code. Valid for 5 minutes.")
    return code


def verify(session, phone, code):
    data = session.get("checkout_otp")
    if not data or data["phone"] != phone:
        return False, "Please request a code first."
    if time.time() - data["at"] > OTP_TTL:
        return False, "This code has expired. Request a new one."
    if data["tries"] >= MAX_ATTEMPTS:
        return False, "Too many attempts. Request a new code."
    data["tries"] += 1
    session["checkout_otp"] = data
    if not secrets.compare_digest(data["code"], (code or "").strip()):
        return False, "That code doesn't match. Try again."
    session.pop("checkout_otp", None)
    return True, ""
