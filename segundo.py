import socket
import argparse
import time
import os


class FileTransferSocket:
    def __init__(self, ip, port, is_udp=False, confirm_delivery=False):
        self.ip = ip
        self.port = port
        self.is_udp = is_udp
        self.confirm_delivery = confirm_delivery
        self.socket = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM if is_udp else socket.SOCK_STREAM
        )
        self.retransmission_timeout = 0
        self.block_size_count = 0
        self.time = 0

    def connect(self):
        self.socket.connect((self.ip, self.port))

    def send_file(self, file_name, block_size):
        time_start = time.time()

        if self.is_udp and self.confirm_delivery:
            self._send_file_udp_with_confirmation(file_name, block_size)
        elif self.is_udp:
            self._send_file_udp(file_name, block_size)
        else:
            self._send_file_tcp(file_name, block_size)

        time_end = time.time()
        self.time = time_end - time_start

        type_socket = "udp_conf_" if self.is_udp and self.confirm_delivery else "udp_" if self.is_udp else "tcp_"
        exists = os.path.exists(f"benchmark_{type_socket}_{block_size}.csv")

        with open(f"benchmark_{type_socket}_{block_size}.csv", "a") as file:
            if not exists:
                file.write("Tempo; Número de blocos enviados; Número de retransmissões\n")

            file.write(f"{self.time}; {self.block_size_count}; {self.retransmission_timeout}\n")

        print(f"Arquivo enviado com sucesso em {self.time} segundos.")
        if self.retransmission_timeout > 0:
            print("Número de retransmissões:", self.retransmission_timeout)
        print("Número de blocos enviados:", self.block_size_count)

    def _send_file_tcp(self, file_name, block_size):
        with open(file_name, "rb") as file:
            while True:
                data = file.read(block_size)
                if not data:
                    break
                self.block_size_count += 1
                self.socket.sendall(data)

    def _send_file_udp(self, file_name, block_size):
        with open(file_name, "rb") as file:
            while True:
                data = file.read(block_size)
                if not data:
                    self.socket.sendto(b"", (self.ip, self.port))
                    break
                self.block_size_count += 1
                self.socket.sendto(data, (self.ip, self.port))

    def _send_file_udp_with_confirmation(self, file_name, block_size):
        with open(file_name, "rb") as file:
            sequence_number = 0
            while True:
                message = str(sequence_number).zfill(10).encode()
                data = file.read(block_size - len(message))
                if not data:
                    self.socket.sendto(b"", (self.ip, self.port))
                    break
                self.block_size_count += 1

                self._send_with_confirmation(data, message, sequence_number, block_size)
                sequence_number += 1

    def _send_with_confirmation(self, data, message, sequence_number, block_size):
        while True:
            packet = message + data
            self.socket.sendto(packet, (self.ip, self.port))
            try:
                self.socket.settimeout(2)
                ack, _ = self.socket.recvfrom(block_size)
                if int(ack.decode()) == sequence_number:
                    break
                else:
                    print(
                        f"ACK inválido. Reenviando pacote... Enviado:{sequence_number} Recebido:{int(ack.decode())}"
                    )
                    self.retransmission_timeout += 1
            except socket.timeout:
                print("Timeout. Reenviando pacote...")
                self.retransmission_timeout += 1

    def close(self):
        self.socket.close()


def main():
    parser = argparse.ArgumentParser(description="Envio de arquivo via socket.")
    parser.add_argument("ip", type=str, help="Endereço IP do destino")
    parser.add_argument("port", type=int, help="Porta do destino")
    parser.add_argument("--udp", action="store_true", help="Utilizar o protocolo UDP")
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Utilizar confirmação de entrega (apenas para UDP)",
    )
    parser.add_argument("file", type=str, help="Nome do arquivo a ser enviado")
    parser.add_argument(
        "block_size",
        type=int,
        default=1024,
        help="Tamanho do bloco em bytes (padrão: 1024)",
    )
    args = parser.parse_args()

    ip = args.ip
    port = args.port
    is_udp = args.udp
    confirm_delivery = args.confirm
    file_name = args.file
    block_size = args.block_size

    file_socket = FileTransferSocket(ip, port, is_udp, confirm_delivery)
    file_socket.connect()
    file_socket.send_file(file_name, block_size)
    file_socket.close()


if __name__ == "__main__":
    main()
