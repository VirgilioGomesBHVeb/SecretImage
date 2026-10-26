# SecretImage 2.0 - Interface final

Versão preparada para reproduzir a interface de referência: página inicial, esconder mensagem, sucesso, extrair mensagem, mensagem recuperada, erro, Sobre e Ajuda.

## Windows 10

```powershell
cd SecretImage_2.0
py -m venv .venv
.\.venv\Scripts\activate
py -m pip install -r requirements.txt
py app.py
```

Abra: `http://127.0.0.1:5000`

Para acesso pela rede Wi-Fi, descubra o IPv4 do computador com `ipconfig` e use `http://IP_DO_PC:5000` a partir do outro dispositivo, desde que a firewall permita a porta 5000.

## Fluxo

- `/` Início
- `/esconder` Esconder mensagem
- `/extrair` Extrair mensagem
- `/sobre` Sobre
- `/ajuda` Ajuda

O backend original de criptografia/esteganografia foi mantido e a camada web foi reorganizada para corresponder à referência visual.
