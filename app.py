import os
import secrets
import tempfile
import uuid
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template, request, send_from_directory
from werkzeug.utils import secure_filename

from crypto import decrypt_message, encrypt_message
from stego import extract_payload, hide_payload

# Configuração de diretórios compatível com Vercel (read-only) e Local
BASE_DIR = Path(__file__).resolve().parent

# Se estiver na Vercel (VERCEL=1) ou sistema somente leitura, usa /tmp
if os.environ.get("VERCEL") or not os.access(BASE_DIR, os.W_OK):
    TEMP_ROOT = Path(tempfile.gettempdir())
    UPLOAD_DIR = TEMP_ROOT / "secretimage_uploads"
    OUTPUT_DIR = TEMP_ROOT / "secretimage_outputs"
else:
    UPLOAD_DIR = BASE_DIR / "uploads"
    OUTPUT_DIR = BASE_DIR / "outputs"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
app.secret_key = os.environ.get("SECRETIMAGE_SESSION_KEY", secrets.token_hex(32))

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "bmp"}
GENERIC_EXTRACT_ERROR = "A chave fornecida não corresponde à imagem ou a imagem está corrompida."


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file_storage):
    if not file_storage or not file_storage.filename:
        raise ValueError("Seleccione uma imagem.")
    if not allowed_file(file_storage.filename):
        raise ValueError("Formato não suportado. Use PNG, JPG, JPEG ou BMP.")
    extension = file_storage.filename.rsplit(".", 1)[1].lower()
    filename = secure_filename(f"{uuid.uuid4().hex}.{extension}")
    path = UPLOAD_DIR / filename
    file_storage.save(path)
    return path


def remove_file(path):
    try:
        Path(path).unlink(missing_ok=True)
    except OSError:
        pass


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/esconder")
def hide_page():
    return render_template("hide.html")


@app.get("/extrair")
def extract_page():
    return render_template("extract.html")


@app.get("/sobre")
def about_page():
    return render_template("about.html")


@app.get("/ajuda")
def help_page():
    return render_template("help.html")


@app.post("/hide")
def hide():
    image = request.files.get("image")
    message = request.form.get("message", "").strip()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    if not image or not image.filename:
        return render_template("error.html", title="Não foi possível proteger a mensagem", message="Seleccione uma imagem para continuar.", causes=["Nenhuma imagem foi seleccionada."]), 400
    if not message:
        return render_template("error.html", title="Não foi possível proteger a mensagem", message="Escreva a mensagem que deseja proteger.", causes=["A mensagem está vazia."]), 400
    if len(message) > 200_000:
        return render_template("error.html", title="Não foi possível proteger a mensagem", message="A mensagem é demasiado grande.", causes=["O limite da mensagem é 200 000 caracteres."]), 400
    if not password:
        return render_template("error.html", title="Não foi possível proteger a mensagem", message="Digite uma chave.", causes=["A chave está vazia."]), 400
    if len(password) < 8:
        return render_template("error.html", title="Não foi possível proteger a mensagem", message="A chave é demasiado curta.", causes=["Use pelo menos 8 caracteres."]), 400
    if password != confirm_password:
        return render_template("error.html", title="Não foi possível proteger a mensagem", message="As chaves não coincidem.", causes=["A confirmação da chave é diferente da chave principal."]), 400

    input_path = None
    output_name = f"secretimage_{uuid.uuid4().hex[:8]}.png"
    output_path = OUTPUT_DIR / output_name
    original_name = secure_filename(image.filename) or "imagem"

    try:
        input_path = save_uploaded_file(image)
        payload = encrypt_message(message, password)
        hide_payload(input_path, payload, output_path)
        return render_template(
            "success_hide.html",
            filename=output_name,
            original_name=original_name,
            created_at=datetime.now().strftime("%d/%m/%Y %H:%M"),
        )
    except ValueError as exc:
        return render_template("error.html", title="Não foi possível proteger a mensagem", message=str(exc), causes=["Verifique o formato e o tamanho da imagem.", "Tente outra imagem se a capacidade for insuficiente."]), 400
    except Exception:
        return render_template("error.html", title="Não foi possível proteger a mensagem", message="Ocorreu um erro ao processar a imagem.", causes=["A imagem pode estar corrompida.", "Tente novamente com uma imagem PNG ou JPG válida."]), 500
    finally:
        if input_path:
            remove_file(input_path)


@app.post("/extract")
def extract():
    image = request.files.get("extract_image")
    password = request.form.get("password", "")
    original_name = secure_filename(image.filename) if image and image.filename else "imagem protegida"

    if not image or not image.filename or not allowed_file(image.filename) or not password:
        return render_template("error.html", title="Não foi possível recuperar a mensagem", message=GENERIC_EXTRACT_ERROR, causes=["Chave incorrecta.", "Imagem que não é do SecretImage 2.0.", "Imagem corrompida ou alterada."]), 400

    input_path = None
    try:
        input_path = save_uploaded_file(image)
        payload = extract_payload(input_path)
        message = decrypt_message(payload, password)
        return render_template(
            "success_extract.html",
            extracted_message=message,
            original_name=original_name,
            key_mask="•" * min(max(len(password), 8), 12),
            created_at=datetime.now().strftime("%d/%m/%Y %H:%M"),
        )
    except Exception:
        return render_template("error.html", title="Não foi possível recuperar a mensagem", message=GENERIC_EXTRACT_ERROR, causes=["Chave incorrecta.", "Imagem que não é do SecretImage 2.0.", "Imagem corrompida ou alterada."]), 400
    finally:
        if input_path:
            remove_file(input_path)


@app.get("/download/<filename>")
def download_file(filename):
    safe_name = secure_filename(filename)
    if safe_name != filename or not safe_name.endswith(".png"):
        return "Ficheiro inválido.", 400
    file_path = OUTPUT_DIR / safe_name
    if not file_path.is_file():
        return "Ficheiro não encontrado.", 404
    return send_from_directory(OUTPUT_DIR, safe_name, as_attachment=True, mimetype="image/png")


@app.errorhandler(413)
def too_large(_error):
    return render_template("error.html", title="Ficheiro demasiado grande", message="O ficheiro enviado ultrapassa o limite permitido.", causes=["O limite de upload é 10 MB."]), 413


if __name__ == "__main__":
    host = os.environ.get("SECRETIMAGE_HOST", "0.0.0.0")
    port = int(os.environ.get("SECRETIMAGE_PORT", "5000"))
    debug = os.environ.get("SECRETIMAGE_DEBUG", "0") == "1"
    app.run(host=host, port=port, debug=debug)