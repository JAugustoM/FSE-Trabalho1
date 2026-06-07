import asyncio

from .hardware import HardwareController
from .modos import Modo


class SemaforoCruzamento:
    def __init__(self, loop, hw: HardwareController, id: int):
        self.pedido_ped_prin = False
        self.pedido_ped_cruz = False
        self._modo = None
        self._current_task = None
        self.id = id
        self.codigo_manual = None

        self.loop = loop or asyncio.get_event_loop()

        self.hw = hw

        self.hw.registrar_callbacks_botoes(
            callback_p=self._processar_btn_principal,
            callback_c=self._processar_btn_cruzamento,
        )

        self.modo = Modo.NORMAL

    @property
    def modo(self):
        return self._modo

    @modo.setter
    def modo(self, new_modo):
        if self._modo != new_modo:
            self._modo = new_modo
            self.on_modo_change(new_modo)

    def set_codigo_manual(self, codigo: int):
        self.codigo_manual = codigo
        self.modo = Modo.MANUAL

    def on_modo_change(self, new_modo):
        if self._current_task and not self._current_task.done():
            self._current_task.cancel()

        coro = None
        match new_modo:
            case Modo.NORMAL:
                coro = self.executar_ciclo_normal()
            case Modo.NOITE:
                coro = self.executar_ciclo_noite()
            case Modo.EMERGENCIA_PRINCIPAL:
                coro = self.executar_ciclo_emerg_principal()
            case Modo.EMERGENCIA_CRUZAMENTO:
                coro = self.executar_ciclo_emerg_cruzamento()
            case Modo.MANUAL:
                coro = self.executar_modo_manual()

        if coro:
            self._current_task = self.loop.create_task(coro)

    def _processar_btn_principal(self):
        print(f"\n[C{self.id}] Botão Pedestre Principal pressionado!")
        if self.hw.estado_atual == 1:
            self.pedido_ped_prin = True

    def _processar_btn_cruzamento(self):
        print(f"\n[C{self.id}] Botão Pedestre Cruzamento pressionado!")
        if self.hw.estado_atual == 5:
            self.pedido_ped_cruz = True

    async def esperar_tempo_variavel(self, tempo_maximo, checar_pedido):
        passos = int(tempo_maximo / 0.1)
        for _ in range(passos):
            if checar_pedido():
                print(f"[C{self.id}] Sinal verde interrompido pelo pedestre!")
                break
            await asyncio.sleep(0.1)

    async def executar_modo_manual(self):
        try:
            while True:
                if self.codigo_manual is not None:
                    self.hw.enviar_codigo_3bits(self.codigo_manual)
                await asyncio.sleep(0.5)
        except asyncio.CancelledError:
            raise

    async def executar_ciclo_normal(self):
        try:
            while True:
                self.pedido_ped_prin = False
                self.hw.enviar_codigo_3bits(1)
                print(f"\n[C{self.id}] Via Principal: VERDE | Via Cruzamento: VERMELHO")
                await asyncio.sleep(15)
                await self.esperar_tempo_variavel(15, lambda: self.pedido_ped_prin)

                self.hw.enviar_codigo_3bits(2)
                print(
                    f"\n[C{self.id}] Via Principal: AMARELO | Via Cruzamento: VERMELHO"
                )
                await asyncio.sleep(3)

                self.hw.enviar_codigo_3bits(4)
                print(
                    f"\n[C{self.id}] Via Principal: VERMELHO | Via Cruzamento: VERMELHO"
                )
                await asyncio.sleep(2)

                self.pedido_ped_cruz = False
                self.hw.enviar_codigo_3bits(5)
                print(f"\n[C{self.id}] Via Principal: VERMELHO | Via Cruzamento: VERDE")
                await asyncio.sleep(5)
                await self.esperar_tempo_variavel(5, lambda: self.pedido_ped_cruz)

                self.hw.enviar_codigo_3bits(6)
                print(
                    f"\n[C{self.id}] Via Principal: VERMELHO | Via Cruzamento: AMARELO"
                )
                await asyncio.sleep(3)

                self.hw.enviar_codigo_3bits(4)
                print(
                    f"\n[C{self.id}] Via Principal: VERMELHO | Via Cruzamento: VERMELHO"
                )
                await asyncio.sleep(2)

        except asyncio.CancelledError:
            print(f"\n[C{self.id}] Ciclo Normal encerrado (Mudança de Modo).")
            raise

    async def executar_ciclo_noite(self):
        try:
            while True:
                self.hw.enviar_codigo_3bits(0)
                await asyncio.sleep(1)
                self.hw.enviar_codigo_3bits(4)
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            raise

    async def executar_ciclo_emerg_principal(self):
        try:
            while True:
                self.hw.enviar_codigo_3bits(1)
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            raise

    async def executar_ciclo_emerg_cruzamento(self):
        try:
            while True:
                self.hw.enviar_codigo_3bits(5)
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            raise
