from uart.base import ProtocoloBase


def main():
    uart = ProtocoloBase()

    try:
        while True:
            print("[INPUT] Digite o comando que quer executar:")
            comando = input()

            match comando[0]:
                case "A":
                    print("[INPUT] Digite a matrícula:")
                    matricula = int(input())
                    uart.comandoLeitura(int(comando[1]), matricula)

                case _:
                    print("[ERRO] Comando Inválido!")
    except KeyboardInterrupt:
        print("\n[LOG] Encerrando o UART")
    finally:
        uart.finalizar()
        print("[LOG] UART encerrado com sucesso!")


if __name__ == "__main__":
    main()
