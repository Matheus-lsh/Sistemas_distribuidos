import socket
from pathlib import Path
import os

NOME_PASTA = "compartilhada"

# Garante que a pasta existe
Path(NOME_PASTA).mkdir(exist_ok=True)

def envia_arq(socket,caminho_arq):
    arq = open(caminho_arq,"rb")
    while True:
        conteudo = arq.read(1024)
        if conteudo:
            socket.sendall(conteudo)
        else:
            break
    arq.close()

def ler_nome(sock):
    nome = bytearray()
    while True:
        conteudo = sock.recv(1)
        if not conteudo or conteudo == b"\n":
            break
        nome.extend(conteudo)
    return nome.decode()

def remover_arq(nome_arq):
    caminho = Path(NOME_PASTA + "/" + nome_arq)
    if caminho.exists():
        caminho.unlink()
        print(f"Arquivo removido: {nome_arq}")

def ler_arq(sock, nome_arq, tamanho):
    recebido = 0
    with open(NOME_PASTA + "/" + nome_arq, "wb") as arq:
        while recebido < tamanho:
            dados = sock.recv(min(1024, tamanho - recebido))
            if not dados:
                raise ConnectionError("Conexão encerrada antes do fim do arquivo")
            arq.write(dados)
            recebido += len(dados)
    print(f"Arquivo {nome_arq} recebido com sucesso.")

# Configuração do socket do servidor (fora do loop para escutar continuamente)
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as servidor:
    servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servidor.bind(("0.0.0.0", 8080))
    servidor.listen()
    print("Servidor rodando na porta 8080...")

    while True:
        cliente, endereco = servidor.accept()
        print(f"\nConexão de {endereco}")
        
        with cliente:
            try:
                # O cliente envia algo como: "0|nome_do_arq.txt|1024"
                mensagem = ler_nome(cliente)
                
                if mensagem:
                    partes = mensagem.split("|")
                    acao = partes[0]  # "0" ou "1"
                    
                    if acao == "0" and len(partes) == 3:
                        _, nome_arq, tamanho = partes
                        tamanho = int(tamanho)
                        print(f"Recebendo: {nome_arq} ({tamanho} bytes)")
                        ler_arq(cliente, nome_arq, tamanho)
                        
                    elif acao == "1" and len(partes) == 2:
                        _, nome_arq = partes
                        print(f"Removendo: {nome_arq}")
                        remover_arq(nome_arq)
                        
            except Exception as e:
                print(f"Erro ao processar cliente: {e}")