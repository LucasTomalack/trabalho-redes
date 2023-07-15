import argparse
import socket


def start_server(ip, port, file_name, block_size, protocol, confirm_delivery):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM if protocol == "tcp" else socket.SOCK_DGRAM)
    server_socket.bind((ip, port))
    server_socket.listen(1)
    print(f"Servidor {protocol.upper()} iniciado. Aguardando conexão em {ip}:{port}...")

    with open(file_name, "wb+") as file:
        if protocol == "tcp":
            client_socket, client_address = server_socket.accept()
            print(f"Conexão TCP estabelecida com {client_address[0]}:{client_address[1]}")

            while True:
                data = client_socket.recv(block_size)
                print (data)
                if data == b"":
                    print("Pacote recebido! Fim da conexão.")
                    break
                file.write(data)
                file.flush()

            client_socket.close()
        else:  # UDP
            while True:
                data, client_address = server_socket.recvfrom(block_size)
                if data == b"":
                    break
                file.write(data)
                file.flush()

            if confirm_delivery:
                sequence_number = 0
                while True:
                    data, client_address = server_socket.recvfrom(block_size)
                    if data == b"":
                        sequence_number = 0
                        break
                    ack = int(data[:10])
                    data = data[10:]

                    if ack == sequence_number:
                        file.write(data)
                        file.flush()
                        sequence_number += 1
                    else:
                        print(f"Erro na entrega do pacote {sequence_number}. Recebido pacote {ack}.")

                    server_socket.sendto(str(ack).zfill(10).encode(), client_address)

    server_socket.close()


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Servidor de transferência de arquivo via socket TCP/UDP."
    )
    parser.add_argument("ip", type=str, help="Endereço IP do servidor")
    parser.add_argument("port", type=int, help="Porta do servidor")
    parser.add_argument("file_name", type=str, help="Nome do arquivo a ser enviado")
    parser.add_argument("block_size", type=int, help="Tamanho do bloco de dados")
    parser.add_argument("--udp", action="store_true", help="Utilizar UDP em vez de TCP")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Utilizar confirmação de entrega (apenas para UDP)",
    )

    return parser.parse_args()


def main():
    args = parse_arguments()

    ip = args.ip
    port = args.port
    file_name = args.file_name
    block_size = args.block_size
    protocol = "udp" if args.udp else "tcp"
    confirm_delivery = args.confirm

    start_server(ip, port, file_name, block_size, protocol, confirm_delivery)


if __name__ == "__main__":
    main()
