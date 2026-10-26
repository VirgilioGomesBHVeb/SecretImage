import os
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.fernet import Fernet, InvalidToken

CHUNK_SIZE = 1024 * 1024  # 1 MB por bloco
MAGIC_FOOTER = b"SEC_PAYLOAD_V2"
# Salt fixo de derivação para payload de mídia
PAYLOAD_SALT = b"SecretImage_MediaPayload_Salt_v2"

def _derive_fernet(password: str) -> Fernet:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=PAYLOAD_SALT,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))
    return Fernet(key)

def anexar_midia(imagem_base_path, media_path, saida_path, password):
    """
    Cifra e anexa o arquivo ao final da imagem, preservando nome e extensão originais.
    """
    fernet = _derive_fernet(password)
    nome_original = os.path.basename(media_path).encode('utf-8')
    tamanho_nome = len(nome_original)

    with open(saida_path, 'wb') as f_out:
        # 1. Copia a imagem hospedeira
        with open(imagem_base_path, 'rb') as f_img:
            while chunk := f_img.read(CHUNK_SIZE):
                f_out.write(chunk)

        # 2. Cifra o conteúdo do arquivo
        with open(media_path, 'rb') as f_sec:
            dados_brutos = f_sec.read()
            dados_cifrados = fernet.encrypt(dados_brutos)
            f_out.write(dados_cifrados)

        # 3. Rodapé estruturado:
        # [Nome com extensão] + [2 bytes: tam nome] + [8 bytes: tam dados cifrados] + [Assinatura]
        tamanho_cifrado = len(dados_cifrados)
        f_out.write(nome_original)
        f_out.write(tamanho_nome.to_bytes(2, byteorder='big'))
        f_out.write(tamanho_cifrado.to_bytes(8, byteorder='big'))
        f_out.write(MAGIC_FOOTER)

def extrair_midia(imagem_estego_path, pasta_destino, password):
    """
    Verifica se a imagem possui arquivo embutido, valida a chave e extrai o arquivo original.
    Retorna o caminho do ficheiro ou None.
    """
    tam_footer = len(MAGIC_FOOTER)
    with open(imagem_estego_path, 'rb') as f:
        f.seek(0, os.SEEK_END)
        total_len = f.tell()

        if total_len < tam_footer + 10:
            return None

        # Valida a assinatura de rodapé
        f.seek(-tam_footer, os.SEEK_END)
        if f.read(tam_footer) != MAGIC_FOOTER:
            return None

        # Lê tamanhos dos metadados
        f.seek(-tam_footer - 10, os.SEEK_END)
        tam_nome = int.from_bytes(f.read(2), byteorder='big')
        tam_dados = int.from_bytes(f.read(8), byteorder='big')

        # Lê o nome original do ficheiro
        pos_nome = -tam_footer - 10 - tam_nome
        f.seek(pos_nome, os.SEEK_END)
        nome_arquivo = f.read(tam_nome).decode('utf-8', errors='ignore')

        # Lê os dados cifrados
        pos_dados = pos_nome - tam_dados
        f.seek(pos_dados, os.SEEK_END)
        dados_cifrados = f.read(tam_dados)

    # Tenta desencriptar com a senha
    fernet = _derive_fernet(password)
    try:
        dados_recuperados = fernet.decrypt(dados_cifrados)
    except InvalidToken:
        raise ValueError("Chave incorreta para o ficheiro embutido.")

    caminho_final = os.path.join(pasta_destino, nome_arquivo)
    with open(caminho_final, 'wb') as f_out:
        f_out.write(dados_recuperados)

    return caminho_final