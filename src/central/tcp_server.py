import json
import socket
import threading
from typing import Callable

PORTA_PADRAO = 5000
BUFFER = 4096


class TCPServer:
    def __init__(self, porta: int = PORTA_PADRAO):
        self.porta = porta
        self.clientes: dict[int, socket.socket] = {}
        self._lock = threading.Lock()
        self._handlers: dict[str, Callable] = {}
        self._servidor: socket.socket | None = None
        self._rodando = False

    def on(self, tipo: str, handler: Callable):
        self._handlers[tipo] = handler

    def enviar(self, cruzamento_id: int, mensagem: dict) -> bool:
        with self._lock:
            conn = self.clientes.get(cruzamento_id)
        if conn is None:
            return False
        try:
            conn.sendall((json.dumps(mensagem) + "\n").encode())
            return True
        except Exception:
            return False

    def broadcast(self, mensagem: dict):
        with self._lock:
            ids = list(self.clientes.keys())
        for cid in ids:
            self.enviar(cid, mensagem)

    def _handle_cliente(self, conn: socket.socket, addr):
        cruzamento_id = None
        buffer = ""
        print(f"[TCP] Nova conexão: {addr}")
        try:
            while self._rodando:
                data = conn.recv(BUFFER)
                if not data:
                    break
                buffer += data.decode(errors="ignore")
                while "\n" in buffer:
                    linha, buffer = buffer.split("\n", 1)
                    linha = linha.strip()
                    if not linha:
                        continue
                    try:
                        msg = json.loads(linha)
                        if cruzamento_id is None and "cruzamento" in msg:
                            cruzamento_id = msg["cruzamento"]
                            with self._lock:
                                self.clientes[cruzamento_id] = conn
                            print(f"[TCP] Cruzamento {cruzamento_id} registrado")
                        handler = self._handlers.get(msg.get("tipo"))
                        if handler:
                            handler(msg)
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            print(f"[TCP] Erro com {addr}: {e}")
        finally:
            if cruzamento_id is not None:
                with self._lock:
                    self.clientes.pop(cruzamento_id, None)
                print(f"[TCP] Cruzamento {cruzamento_id} desconectado")
            conn.close()

    def _aceitar(self):
        while self._rodando:
            try:
                conn, addr = self._servidor.accept()
                threading.Thread(
                    target=self._handle_cliente,
                    args=(conn, addr),
                    daemon=True,
                ).start()
            except Exception:
                break

    def iniciar(self):
        self._rodando = True
        self._servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._servidor.bind(("0.0.0.0", self.porta))
        self._servidor.listen(2)
        print(f"[TCP] Servidor escutando na porta {self.porta}")
        threading.Thread(target=self._aceitar, daemon=True).start()

    def parar(self):
        self._rodando = False
        if self._servidor:
            self._servidor.close()
