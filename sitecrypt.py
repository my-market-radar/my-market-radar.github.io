"""Encryption for everything the site serves or stores as data.

Format v2 (decrypted in the browser with WebCrypto, see template.html):
  master  = PBKDF2-SHA256(password, msalt, iter=310000) -> 32 bytes   (msalt is a fixed, public, site-wide salt)
  filekey = HKDF-SHA256(master, salt=random 16 bytes per write, info="mmr-file-v2") -> AES-256 key
  ct      = AES-256-GCM(filekey, iv=random 12 bytes per write, JSON) (tag appended, as WebCrypto expects)
A fixed msalt lets the browser run the slow PBKDF2 once and optionally remember the master key (never the password);
the random per-write salt + IV mean every file and every write gets a fresh key and nonce.
CLI:  SITE_PASSWORD=... python3 sitecrypt.py enc in.json out.enc.json   |   ... dec in.enc.json
"""
import base64, json, os, sys, pathlib
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

MSALT = b"my-market-radar/v1/2026-10-25"
ITERATIONS = 310_000
INFO = b"mmr-file-v2"
_cache = {}
b64e = lambda b: base64.b64encode(b).decode()
b64d = base64.b64decode

def master_key(password: str, msalt: bytes = MSALT, it: int = ITERATIONS) -> bytes:
    k = (password, msalt, it)
    if k not in _cache:
        _cache[k] = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=msalt, iterations=it).derive(password.encode())
    return _cache[k]

def _file_key(master: bytes, salt: bytes) -> bytes:
    return HKDF(algorithm=hashes.SHA256(), length=32, salt=salt, info=INFO).derive(master)

def encrypt(obj, password: str) -> dict:
    salt, iv = os.urandom(16), os.urandom(12)
    ct = AESGCM(_file_key(master_key(password), salt)).encrypt(iv, json.dumps(obj, separators=(",", ":")).encode(), None)
    return {"v": 2, "kdf": "PBKDF2-SHA256+HKDF-SHA256", "iter": ITERATIONS, "msalt": b64e(MSALT),
            "salt": b64e(salt), "iv": b64e(iv), "ct": b64e(ct)}

def decrypt(p: dict, password: str):
    m = master_key(password, b64d(p["msalt"]), p["iter"])
    return json.loads(AESGCM(_file_key(m, b64d(p["salt"]))).decrypt(b64d(p["iv"]), b64d(p["ct"]), None))

def password():
    pw = os.environ.get("SITE_PASSWORD") or os.environ.get("WATCHLIST_SITE_PASSWORD")
    if not pw: sys.exit("SITE_PASSWORD is not set; refusing to read or write site data.")
    return pw

def load(path, default=None):
    p = pathlib.Path(path)
    return decrypt(json.loads(p.read_text()), password()) if p.exists() else default

def save(path, obj):
    pathlib.Path(path).write_text(json.dumps(encrypt(obj, password())) + "\n")

if __name__ == "__main__":
    if sys.argv[1] == "enc": save(sys.argv[3], json.loads(pathlib.Path(sys.argv[2]).read_text()))
    elif sys.argv[1] == "dec": print(json.dumps(load(sys.argv[2]), indent=1))
