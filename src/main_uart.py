from uart.base import ProtocoloBase
from uart.modbus import ProtocoloMODBUS


def main():
    print("[INPUT] Escolha o protocolo:")
    print("  1 - Protocolo Simplificado")
    print("  2 - MODBUS")
    escolha = input().strip()

    if escolha == "2":
        uart = ProtocoloMODBUS()
        print("[LOG] Usando protocolo MODBUS")
    else:
        uart = ProtocoloBase()
        print("[LOG] Usando protocolo Simplificado")

    try:
        while True:
            print("[INPUT] Digite o comando:")
            comando = input().strip().upper()

            if len(comando) != 2 or comando[0] not in ["A", "B"]:
                print("[ERRO] Comando inválido!")
                continue

            tipo_comando = comando[0]

            try:
                num_comando = int(comando[1])
            except ValueError:
                print("[ERRO] O comando deve conter um número válido após a letra.")
                continue

            if num_comando not in [1, 2, 3]:
                print("[ERRO] Comando deve ser 1, 2 ou 3.")
                continue

            print("[INPUT] Digite a matrícula (6 dígitos):")
            matricula = input().strip()

            if tipo_comando == "A":
                uart.comandoLeitura(num_comando, matricula)

            elif tipo_comando == "B":
                if num_comando == 1:
                    print("[INPUT] Digite um inteiro:")
                    try:
                        dados = int(input().strip())
                    except ValueError:
                        print("[ERRO] Valor inserido não é um inteiro válido.")
                        continue
                elif num_comando == 2:
                    print("[INPUT] Digite um número real:")
                    try:
                        dados = float(input().strip())
                    except ValueError:
                        print("[ERRO] Valor inserido não é um número real válido.")
                        continue
                else:
                    print("[INPUT] Digite um texto (payload para o envio):")
                    dados = input()

                uart.comandoEnvio(num_comando, dados, matricula)

    except KeyboardInterrupt:
        print("\n[LOG] Encerrando o UART")
    finally:
        uart.finalizar()
        print("[LOG] UART encerrado com sucesso!")


if __name__ == "__main__":
    main()
