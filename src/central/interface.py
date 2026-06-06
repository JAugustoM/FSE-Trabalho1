import os


class Interface:
    def __init__(self, servidor):
        self.servidor = servidor

    def _exibir(self):
        os.system("clear")
        estado = self.servidor.estado
        multas = self.servidor.log_multas.multas
        clientes = list(self.servidor.tcp.clientes.keys())

        print("=" * 54)
        print("   SERVIDOR CENTRAL - CONTROLE DE CRUZAMENTOS")
        print("=" * 54)
        print(f"  Modo noturno : {'ATIVO' if estado.dados['modo_noturno'] else 'inativo'}")
        print(f"  Emergência   : {'ATIVA' if estado.dados['emergencia_ativa'] else 'inativa'}")
        print(f"  Cruzamentos  : {clientes if clientes else 'nenhum conectado'}")
        print()

        print("  TRÁFEGO POR SENSOR")
        print("-" * 54)
        contagens = estado.dados.get("contagens", {})
        if contagens:
            for sid in sorted(contagens.keys(), key=int):
                print(f"  Sensor {sid}: {contagens[sid]:>4} veículos")
        else:
            print("  Sem dados ainda.")
        print()

        print(f"  MULTAS: {len(multas)}")
        print("-" * 54)
        for m in multas[-5:]:
            print(f"  {m.timestamp[11:19]} C{m.cruzamento} S{m.sensor_id} | {m.velocidade_kmh:.0f} km/h | {m.placa} | R$ {m.valor:.2f}")
        if not multas:
            print("  Nenhuma multa registrada.")

    def _menu(self) -> str:
        print()
        print("-" * 54)
        print("  1 - Alternar modo noturno")
        print("  2 - Controle manual de semáforo")
        print("  3 - Atualizar tela")
        print("  0 - Sair")
        print("-" * 54)
        return input("> ").strip()

    def _controlar_semaforo(self):
        print("Cruzamento (1 ou 2):")
        try:
            cruzamento = int(input("> "))
        except ValueError:
            print("[ERRO] Inválido")
            return
        print("Código do semáforo (0-7):")
        try:
            codigo = int(input("> "))
        except ValueError:
            print("[ERRO] Inválido")
            return
        if self.servidor.tcp.enviar(cruzamento, {"tipo": "semaforo_manual", "codigo": codigo}):
            print(f"[OK] Código {codigo} enviado para cruzamento {cruzamento}")
        else:
            print(f"[ERRO] Cruzamento {cruzamento} não conectado")
        input("Enter para continuar...")

    def executar(self):
        while True:
            self._exibir()
            escolha = self._menu()

            if escolha == "0":
                break
            elif escolha == "1":
                noturno = not self.servidor.estado.dados["modo_noturno"]
                self.servidor.estado.dados["modo_noturno"] = noturno
                self.servidor.estado.salvar()
                self.servidor.tcp.broadcast({"tipo": "modo_noturno", "ativo": noturno})
                print(f"[OK] Modo noturno {'ativado' if noturno else 'desativado'}")
                input("Enter para continuar...")
            elif escolha == "2":
                self._controlar_semaforo()
