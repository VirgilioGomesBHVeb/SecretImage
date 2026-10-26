import base64
import os

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ITERATIONS = 600_000
SALT_LENGTH = 16
MAGIC = b"SI2"
VERSION = b"\x01"


def derive_key(password: str, salt: bytes) -> bytes:
    if not password:
        raise ValueError("A chave não pode estar vazia.")

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=ITERATIONS,
    )
    raw_key = kdf.derive(password.encode("utf-8"))
    return base64.urlsafe_b64encode(raw_key)


def encrypt_message(message: str, password: str) -> bytes:
    if not message:
        raise ValueError("A mensagem não pode estar vazia.")

    salt = os.urandom(SALT_LENGTH)
    key = derive_key(password, salt)
    token = Fernet(key).encrypt(message.encode("utf-8"))

    return MAGIC + VERSION + salt + token


def decrypt_message(payload: bytes, password: str) -> str:
    header_len = len(MAGIC) + len(VERSION)

    if len(payload) <= header_len + SALT_LENGTH:
        raise ValueError("Dados SecretImage inválidos.")

    if not payload.startswith(MAGIC + VERSION):
        raise ValueError("Esta imagem não contém uma mensagem SecretImage 2.0 válida.")

    salt_start = header_len
    salt_end = salt_start + SALT_LENGTH
    salt = payload[salt_start:salt_end]
    token = payload[salt_end:]

    key = derive_key(password, salt)

    try:
        plaintext = Fernet(key).decrypt(token)
    except InvalidToken as exc:
        raise ValueError("Chave incorrecta ou imagem alterada.") from exc

    try:
        return plaintext.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("A mensagem recuperada é inválida.") from exc
