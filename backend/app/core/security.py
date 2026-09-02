"""Password hashing and minimal HS256 JWT implementation without external authority."""
import base64, hashlib, hmac, json, secrets, time
from .config import settings

def hash_password(password: str, salt: str | None = None) -> str:
    if len(password) < 12:
        raise ValueError("Password must contain at least 12 characters")
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 310_000).hex()
    return f"pbkdf2_sha256$310000${salt}${digest}"

def verify_password(password: str, encoded: str) -> bool:
    _, rounds, salt, stored = encoded.split("$", 3)
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), int(rounds)).hex()
    return hmac.compare_digest(candidate, stored)

def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()

def _unb64(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))

def issue_token(subject: str, role: str, expires_in: int = 3600) -> str:
    header = _b64(b'{"alg":"HS256","typ":"JWT"}')
    payload = _b64(json.dumps({"sub": subject, "role": role, "exp": int(time.time()) + expires_in}, separators=(",", ":")).encode())
    signature = _b64(hmac.new(settings.jwt_secret.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest())
    return f"{header}.{payload}.{signature}"

def decode_token(token: str) -> dict:
    header, payload, signature = token.split(".")
    expected = _b64(hmac.new(settings.jwt_secret.encode(), f"{header}.{payload}".encode(), hashlib.sha256).digest())
    if not hmac.compare_digest(signature, expected): raise ValueError("Invalid signature")
    claims = json.loads(_unb64(payload))
    if claims.get("exp", 0) < time.time(): raise ValueError("Expired token")
    return claims
