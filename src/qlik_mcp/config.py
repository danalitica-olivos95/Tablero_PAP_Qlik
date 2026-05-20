import os
import ssl
from pathlib import Path
from dotenv import load_dotenv

# Raíz del proyecto: 3 niveles arriba de src/qlik_mcp/config.py
_ROOT = Path(__file__).resolve().parent.parent.parent

load_dotenv(dotenv_path=_ROOT / ".env")

QLIK_HOST = os.getenv("QLIK_HOST", "bi.coopserfun.com.co")
QRS_PORT = int(os.getenv("QLIK_QRS_PORT", "4242"))
ENGINE_PORT = int(os.getenv("QLIK_ENGINE_PORT", "4747"))
CERT_DIR = Path(os.getenv("QLIK_CERT_DIR", str(_ROOT / "certs")))
USER_DIR = os.getenv("QLIK_USER_DIR", "INTERNAL")
USER_ID = os.getenv("QLIK_USER_ID", "sa_engine")

XRFKEY = "abcdefghijklmnop"


def build_ssl_context() -> ssl.SSLContext:
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.load_verify_locations(cafile=str(CERT_DIR / "root.pem"))
    ctx.load_cert_chain(
        certfile=str(CERT_DIR / "client.pem"),
        keyfile=str(CERT_DIR / "client_key.pem"),
    )
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_REQUIRED
    return ctx


def qlik_user_header() -> str:
    return f"UserDirectory={USER_DIR};UserId={USER_ID}"
