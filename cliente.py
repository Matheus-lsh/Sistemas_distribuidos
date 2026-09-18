import socket
from pathlib import Path
import time
import hashlib

NOME_PASTA = "compartilhada"
SERVIDOR = ("10.3.1.35", 8080)

def hash_arquivo(caminho):
    sha256 = hashlib.sha256()
    with open(caminho, "rb") as arquivo:
        while bloco := arquivo.read(1024 * 1024):
            sha256.update(bloco)
    return sha256.hexdigest()

def envia_arq(sock, caminho_arq, tamanho):
    enviado = 0
    with open(caminho_arq, "rb") as arq:
        while enviado < tamanho:
            conteudo = arq.read(min(1024, tamanho - enviado))
            if not conteudo:
                break
            sock.sendall(conteudo)
            enviado += len(conteudo)

pasta = Path(NOME_PASTA)
pasta.mkdir(exist_ok=True)

print(f"Monitorando a pasta '{NOME_PASTA}'...")

estado = {}  # nome -> hash do último conteúdo enviado ao servidor
             # (vazio no início: arquivos já existentes serão enviados na 1ª volta)

while True:
    try:
        atuais = {a.name: a for a in pasta.iterdir() if a.is_file()}

        para_enviar = []
        for nome, caminho in atuais.items():
            h = hash_arquivo(caminho)
            if estado.get(nome) != h:      # novo OU alterado
                para_enviar.append((nome, caminho, h))

        removidos = [n for n in estado if n not in atuais]

        if para_enviar or removidos:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cliente:
                cliente.connect(SERVIDOR)

                for nome, caminho, h in para_enviar:
                    tamanho = caminho.stat().st_size
                    print(f"Enviando {nome} ({tamanho} bytes)")
                    cliente.sendall(f"0|{nome}|{tamanho}\n".encode())
                    envia_arq(cliente, caminho, tamanho)
                    estado[nome] = h       # só atualiza após enviar

                for nome in removidos:
                    print(f"{nome} removido")
                    cliente.sendall(f"1|{nome}\n".encode())
                    del estado[nome]

        time.sleep(2)

    except ConnectionRefusedError:
        print("Servidor offline. Tentando reconectar em 3 segundos...")
        time.sleep(3)
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
        time.sleep(2)