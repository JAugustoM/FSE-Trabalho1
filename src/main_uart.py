from uart.base import ProtocoloBase
from uart.modbus import ProtocoloMODBUS

SEP = "\n" + "─" * 40


def escolher_protocolo() -> ProtocoloBase | None:
    while True:
        print(SEP)
        print("Escolha o protocolo:")
        print("  1 - Protocolo Simplificado")
        print("  2 - MODBUS")
        print("  0 - Sair")
        escolha = input("> ").strip()

        if escolha == "1":
            print("\n[LOG] Usando protocolo Simplificado")
            return ProtocoloBase()
        elif escolha == "2":
            print("\n[LOG] Usando protocolo MODBUS")
            return ProtocoloMODBUS()
        elif escolha == "0":
            return None
        else:
            print("\n[ERRO] Opção inválida.")


def executar_comando(uart: ProtocoloBase) -> bool:
    print("Comando (A1-A3, B1-B3) | 0 para voltar:")
    comando = input("> ").strip().upper()

    if comando == "0":
        return True

    if len(comando) != 2 or comando[0] not in ["A", "B"]:
        print("\n[ERRO] Comando inválido.")
        return False

    tipo_comando = comando[0]

    try:
        num_comando = int(comando[1])
    except ValueError:
        print("\n[ERRO] O comando deve ter um número após a letra.")
        return False

    if num_comando not in [1, 2, 3]:
        print("\n[ERRO] Número deve ser 1, 2 ou 3.")
        return False

    print("\nMatrícula (6 dígitos) | 0 para voltar:")
    matricula = input("> ").strip()
    if matricula == "0":
        return False

    print()

    if tipo_comando == "A":
        uart.comandoLeitura(num_comando, matricula)

    elif tipo_comando == "B":
        if num_comando == 1:
            print("Inteiro | 0 para voltar:")
            valor = input("> ").strip()
            if valor == "0":
                return False
            try:
                dados = int(valor)
            except ValueError:
                print("\n[ERRO] Valor não é um inteiro válido.")
                return False

        elif num_comando == 2:
            print("Número real | 0 para voltar:")
            valor = input("> ").strip()
            if valor == "0":
                return False
            try:
                dados = float(valor)
            except ValueError:
                print("\n[ERRO] Valor não é um número real válido.")
                return False

        else:
            print("Texto | 0 para voltar:")
            valor = input("> ").strip()
            if valor == "0":
                return False
            dados = valor

        print()
        uart.comandoEnvio(num_comando, dados, matricula)

    return False


def main():
    uart = None
    try:
        while True:
            uart = escolher_protocolo()
            if uart is None:
                break

            voltar = False
            while not voltar:
                voltar = executar_comando(uart)

            uart.finalizar()
            uart = None

    except KeyboardInterrupt:
        print("\n[LOG] Encerrando o UART")
    finally:
        if uart is not None:
            uart.finalizar()
        print("[LOG] UART encerrado com sucesso!")


if __name__ == "__main__":
    main()
