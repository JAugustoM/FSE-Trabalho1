# Trabalho 1 - Fundamentos de Sistemas Embarcados 2026/1

Este repositório contém o codigo referente ao trabalho 1 da disciplina Fundamentos de Sistemas Embarcados, ministrada em 2026/1.

## Requisitos

Antes de rodar o projeto instale as bibliotecas usadas no projeto com o comando abaixo.

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Execução

### Semáforos (Entrega 1)

```sh
python src/main.py
```

Roda os dois modelos de semáforo simultaneamente (Modelo 1 — 3 LEDs e Modelo 2 — cruzamento completo).

### UART (Entrega 2)

```sh
python src/main_uart.py
```

Ao iniciar, escolha o protocolo:
- `1` — Protocolo Simplificado
- `2` — MODBUS

Em seguida, digite o comando no formato `A1`, `A2`, `A3`, `B1`, `B2` ou `B3`, a matrícula (6 dígitos) e o dado a enviar quando solicitado.

### Sistema Distribuído (Entrega Final)

O sistema é composto por três processos independentes que devem ser iniciados em terminais separados, nesta ordem:

**Terminal 1 — Servidor Central:**
```sh
cd src
python main_central.py
```

**Terminal 2 — Servidor Distribuído (Cruzamento 1):**
```sh
cd src
python main_distibuido.py 1
```

**Terminal 3 — Servidor Distribuído (Cruzamento 2):**
```sh
cd src
python main_distibuido.py 2
```

O Servidor Central deve ser iniciado primeiro. Os servidores distribuídos reconectam automaticamente caso a conexão caia.

