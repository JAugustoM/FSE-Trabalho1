from central.servidor import ServidorCentral


def main():
    print("[CENTRAL] Iniciando Servidor Central...")
    servidor = ServidorCentral()
    try:
        servidor.iniciar()
    except KeyboardInterrupt:
        print("\n[CENTRAL] Encerrando...")
    finally:
        servidor.parar()
        print("[CENTRAL] Servidor encerrado.")


if __name__ == "__main__":
    main()
