"""Encrypt the page data so only someone with the site password can read it.

AES-256-GCM with a key derived by PBKDF2-SHA256. The browser does the same derivation with WebCrypto
(see template.html), so the password never leaves the device and the repo holds no secret.
"""
import base64, json, os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

# A fixed, site-specific salt lets the browser cache the derived key between refreshes.
# It doesn't need to be secret; the password does.
SALT = b"my-market-radar/v1/2026-10-25"
ITERATIONS = 310_000

def derive_key(password: str) -> bytes:
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=SALT, iterations=ITERATIONS)
    return kdf.derive(password.encode())

def encrypt(obj, password: str) -> dict:
    iv = os.urandom(12)
    ct = AESGCM(derive_key(password)).encrypt(iv, json.dumps(obj, separators=(",", ":")).encode(), None)
    b64 = lambda b: base64.b64encode(b).decode()
    return {"v": 1, "kdf": "PBKDF2-SHA256", "iter": ITERATIONS, "salt": b64(SALT), "iv": b64(iv), "ct": b64(ct)}

def decrypt(payload: dict, password: str):
    d = lambda s: base64.b64decode(s)
    return json.loads(AESGCM(derive_key(password)).decrypt(d(payload["iv"]), d(payload["ct"]), None))
