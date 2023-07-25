import socket
import argparse
import time
import os


class SocketTransferenciaArquivo:
    def __init__(self, ip, porta, is_udp=False, confirmar_entrega=False):
        self.ip = ip
        self.porta = porta
        self.is_udp = is_udp
        self.confirmar_entrega = confirmar_entrega
        self.socket = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM if is_udp else socket.SOCK_STREAM
        )
        self.timeout_retransmissao = 0
        self.contagem_tamanho_bloco = 0
        self.tempo = 0

    def conectar(self):
        self.socket.connect((self.ip, self.porta))

    def enviar_arquivo(self, nome_arquivo, tamanho_bloco):
        tempo_inicio = time.time()

        if self.is_udp and self.confirmar_entrega:
            self._enviar_arquivo_udp_com_confirmacao(nome_arquivo, tamanho_bloco)
        elif self.is_udp:
            self._enviar_arquivo_udp(nome_arquivo, tamanho_bloco)
        else:
            self._enviar_arquivo_tcp(nome_arquivo, tamanho_bloco)

        tempo_fim = time.time()
        self.tempo = tempo_fim - tempo_inicio

        tipo_socket = "udp_conf_" if self.is_udp and self.confirmar_entrega else "udp_" if self.is_udp else "tcp_"
        existe_arquivo = os.path.exists(f"benchmark_{tipo_socket}_{tamanho_bloco}.csv")

        with open(f"benchmark_{tipo_socket}_{tamanho_bloco}.csv", "a") as arquivo:
            if not existe_arquivo:
                arquivo.write("Tempo; Número de blocos enviados; Número de retransmissões\n")

            arquivo.write(f"{self.tempo}; {self.contagem_tamanho_bloco}; {self.timeout_retransmissao}\n")

        print(f"Arquivo enviado com sucesso em {self.tempo} segundos.")
        if self.timeout_retransmissao > 0:
            print("Número de retransmissões:", self.timeout_retransmissao)
        print("Número de blocos enviados:", self.contagem_tamanho_bloco)

    def _enviar_arquivo_tcp(self, nome_arquivo, tamanho_bloco):
        with open(nome_arquivo, "rb") as arquivo:
            while True:
                dados = arquivo.read(tamanho_bloco)
                if not dados:
                    break
                self.contagem_tamanho_bloco += 1
                self.socket.sendall(dados)

    def _enviar_arquivo_udp(self, nome_arquivo, tamanho_bloco):
        with open(nome_arquivo, "rb") as arquivo:
            while True:
                dados = arquivo.read(tamanho_bloco)
                if not dados:
                    self.socket.sendto(b"", (self.ip, self.porta))
                    break
                self.contagem_tamanho_bloco += 1
                self.socket.sendto(dados, (self.ip, self.porta))

    def _enviar_arquivo_udp_com_confirmacao(self, nome_arquivo, tamanho_bloco):
        with open(nome_arquivo, "rb") as arquivo:
            numero_sequencia = 0
            while True:
                mensagem = str(numero_sequencia).zfill(10).encode()
                dados = arquivo.read(tamanho_bloco - len(mensagem))
                if not dados:
                    self.socket.sendto(b"", (self.ip, self.porta))
                    break
                self.contagem_tamanho_bloco += 1

                self._enviar_com_confirmacao(dados, mensagem, numero_sequencia, tamanho_bloco)
                numero_sequencia += 1

    def _enviar_com_confirmacao(self, dados, mensagem, numero_sequencia, tamanho_bloco):
        while True:
            pacote = mensagem + dados
            self.socket.sendto(pacote, (self.ip, self.porta))
            try:
                self.socket.settimeout(2)
                ack, _ = self.socket.recvfrom(tamanho_bloco)
                if int(ack.decode()) == numero_sequencia:
                    break
                else:
                    print(
                        f"ACK inválido. Reenviando pacote... Enviado:{numero_sequencia} Recebido:{int(ack.decode())}"
                    )
                    self.timeout_retransmissao += 1
            except socket.timeout:
                print("Timeout. Reenviando pacote...")
                self.timeout_retransmissao += 1

    def fechar(self):
        self.socket.close()


def main():
    parser = argparse.ArgumentParser(description="Envio de arquivo via socket.")
    parser.add_argument("ip", type=str, help="Endereço IP do destino")
    parser.add_argument("porta", type=int, help="Porta do destino")
    parser.add_argument("udp", action="store_true", help="Protocolo UDP")
    parser.add_argument(
        "udp_conf",
        action="store_true",
        help="Utilizar confirmação de entrega (apenas para UDP)",
    )
    parser.add_argument("arquivo", type=str, help="Nome do arquivo manipulado")
    parser.add_argument(
        "tamanho_bloco",
        type=int,
        default=1024,
        help="Tamanho bloco em bytes",
    )
    args = parser.parse_args()

    ip = args.ip
    porta = args.porta
    is_udp = args.udp
    confirmar_entrega = args.confirmar
    nome_arquivo = args.arquivo
    tamanho_bloco
