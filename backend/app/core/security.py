import base64
import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import settings


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    iterations = 210_000
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return "$".join(
        [
            "pbkdf2_sha256",
            str(iterations),
            _b64url_encode(salt),
            _b64url_encode(digest),
        ]
    )


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations_text, salt_text, digest_text = password_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False

        iterations = int(iterations_text)
        salt = _b64url_decode(salt_text)
        expected_digest = _b64url_decode(digest_text)
        actual_digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            iterations,
        )
        return hmac.compare_digest(actual_digest, expected_digest)
    except Exception:
        return False


def create_access_token(subject: str, role: str) -> str:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=settings.auth_access_token_expire_minutes)
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "sub": subject,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }

    signing_input = ".".join(
        [
            _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8")),
            _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")),
        ]
    )
    signature = hmac.new(
        settings.auth_secret_key.encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return f"{signing_input}.{_b64url_encode(signature)}"


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        header_text, payload_text, signature_text = token.split(".", 2)
    except ValueError as exc:
        raise ValueError("无效的 token 格式") from exc

    signing_input = f"{header_text}.{payload_text}"
    expected_signature = hmac.new(
        settings.auth_secret_key.encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()
    actual_signature = _b64url_decode(signature_text)
    if not hmac.compare_digest(actual_signature, expected_signature):
        raise ValueError("token 签名校验失败")

    payload = json.loads(_b64url_decode(payload_text))
    expires_at = int(payload.get("exp", 0))
    if expires_at < int(datetime.now(timezone.utc).timestamp()):
        raise ValueError("token 已过期")

    return payload
