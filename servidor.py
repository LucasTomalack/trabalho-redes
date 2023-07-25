import argparse
import socket


def iniciar_servidor(ip, porta, nome_arquivo, tamanho_bloco, protocolo, confirmar_entrega):
    socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM if protocolo == "tcp" else socket.SOCK_DGRAM)
    socket_servidor.bind((ip, porta))
    socket_servidor.listen(1)
    print(f"Aguardando envio de dados do cliente.")

    with open(nome_arquivo, "wb+") as arquivo:
        if protocolo == "tcp":
            socket_cliente, endereco_cliente = socket_servidor.accept()
            print(f"Conexão OK")

            while True:
                dados = socket_cliente.recv(tamanho_bloco)
                print(dados)
                if dados == b"":
                    print("Pacote entregue.")
                    break
                arquivo.write(dados)
                arquivo.flush()

            socket_cliente.close()
        else:  # UDP
            while True:
                dados, endereco_cliente = socket_servidor.recvfrom(tamanho_bloco)
                if dados == b"":
                    break
                arquivo.write(dados)
                arquivo.flush()

            if confirmar_entrega:
                numero_sequencia = 0
                while True:
                    dados, endereco_cliente = socket_servidor.recvfrom(tamanho_bloco)
                    if dados == b"":
                        numero_sequencia = 0
                        break
                    ack = int(dados[:10])
                    dados = dados[10:]

                    if ack == numero_sequencia:
                        arquivo.write(dados)
                        arquivo.flush()
                        numero_sequencia += 1
                    else:
                        print(f"Erro na entrega do pacote {numero_sequencia}. Recebido pacote {ack}.")

                    socket_servidor.sendto(str(ack).zfill(10).encode(), endereco_cliente)

    socket_servidor.close()


def analisar_argumentos():
    parser = argparse.ArgumentParser(
        description="Servidor de envio TCP/UDP."
    )
    parser.add_argument("ip", type=str, help="Endereço IP servidor")
    parser.add_argument("porta", type=int, help="Porta servidor")
    parser.add_argument("nome_arquivo", type=str, help="Nome arquivo manipulado")
    parser.add_argument("tamanho_bloco", type=int, help="Tamanho bloco de dados")
    parser.add_argument("udp", action="store_true", help="Protocolo UDP")
    parser.add_argument(
        "udp_conf",
        action="store_true",
        help="Utilizar confirmação do tipo pare-e-espere",
    )

    return parser.parse_args()


def main():
    args = analisar_argumentos()

    ip = args.ip
    porta = args.porta
    nome_arquivo = args.nome_arquivo
    tamanho_bloco = args.tamanho_bloco
    protocolo = "udp" if args.udp else "tcp"
    confirmar_entrega = args.confirmar

    iniciar_servidor(ip, porta, nome_arquivo, tamanho_bloco, protocolo, confirmar_entrega)


if __name__ == "__main__":
    main()
