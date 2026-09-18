import socket
from pathlib import Path
import time

NOME_PASTA = "compartilhada"

def envia_arq(socket, caminho_arq):
    with open(caminho_arq, "rb") as arq:
        while True:
            conteudo = arq.read(1024)
            if not conteudo:
                break
            socket.sendall(conteudo)

def ler_nome(socket):
    conteudo_total = b""
    while True:
        conteudo = socket.recv(1)
        if conteudo != b"\n":
            conteudo_total += conteudo
        else:
            break
    return conteudo_total

def remover_arq_local(nome_arq):
    # Função caso precise manipular algo localmente (opcional)
    pass

# Garante que a pasta existe localmente
pasta = Path(NOME_PASTA)
pasta.mkdir(exist_ok=True)

print(f"Monitorando a pasta '{NOME_PASTA}'...")

while True:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cliente:
            cliente.connect(("10.3.1.35", 8080))
            
            # Pega o estado inicial dos arquivos
            arquivos_conhecidos = set(pasta.iterdir())
            time.sleep(2)
            # Pega o estado após o intervalo
            arquivos_novos = set(pasta.iterdir())
            
            novos = arquivos_novos - arquivos_conhecidos
            removidos = arquivos_conhecidos - arquivos_novos 
            
            if novos:
                for arquivo in novos:
                    if arquivo.is_file():
                        print(f"{arquivo.name} adicionado")
                        tamanho = arquivo.stat().st_size
                        # Envia o protocolo de adição: "0|nome|tamanho"
                        cliente.sendall(f"0|{arquivo.name}|{tamanho}\n".encode())
                        envia_arq(cliente, arquivo)
                        print(f"{arquivo.name} enviado com sucesso.")
                        
            if removidos:
                for arquivo in removidos:
                    print(f"{arquivo.name} removido")
                    # Envia o protocolo de remoção: "1|nome"
                    cliente.sendall(f"1|{arquivo.name}\n".encode())
                    
    except ConnectionRefusedError:
        print("Servidor offline. Tentando reconectar em 3 segundos...")
        time.sleep(3)
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
        time.sleep(2)