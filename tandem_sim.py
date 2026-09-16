"""
Simulador de filas em tandem (Fila 1 -> Fila 2) - Modulo 6, Simulacao e Metodos Analiticos.
Fila 1: G/G/2/3 (chegadas externas). Fila 2: G/G/1/5 (recebe 100% da saida da Fila 1).
Encerra ao consumir o 100.000o numero pseudoaleatorio.
"""

import heapq


class LCG:
    """X(n+1) = (a*X(n) + c) mod M. NextRandom() normaliza para [0,1)."""

    def __init__(self, seed, a=1103515245, c=12345, m=2 ** 31):
        self.a, self.c, self.m = a, c, m
        self.x = seed
        self.count = 0

    def next_random(self):
        self.x = (self.a * self.x + self.c) % self.m
        self.count += 1
        return self.x / self.m

    def uniform(self, low, high):
        return low + (high - low) * self.next_random()


class Fila:
    def __init__(self, nome, servidores, capacidade, service_range,
                 arrival_range=None, downstream=None):
        self.nome = nome
        self.servidores = servidores
        self.capacidade = capacidade
        self.service_range = service_range
        self.arrival_range = arrival_range      # None = sem chegada externa
        self.downstream = downstream            # proxima fila da rede, ou None

        self.n = 0
        self.perdas = 0
        self.tempo_acumulado = [0.0] * (capacidade + 1)
        self.last_change_time = 0.0

    def acumula_tempo(self, tempo_atual):
        delta = tempo_atual - self.last_change_time
        if delta > 0:
            self.tempo_acumulado[self.n] += delta
        self.last_change_time = tempo_atual


CHEGADA = "CHEGADA"
SAIDA = "SAIDA"


class Escalonador:
    def __init__(self):
        self._heap = []
        self._seq = 0  # desempate para eventos com o mesmo tempo

    def agenda(self, tempo, tipo, fila):
        self._seq += 1
        heapq.heappush(self._heap, (tempo, self._seq, tipo, fila))

    def proximo(self):
        return heapq.heappop(self._heap)

    def vazio(self):
        return len(self._heap) == 0


def processa_chegada(fila, tempo, rng, esc):
    if fila.arrival_range is not None:
        intervalo = rng.uniform(*fila.arrival_range)
        esc.agenda(tempo + intervalo, CHEGADA, fila)

    if fila.n < fila.capacidade:
        servidores_ocupados_antes = min(fila.n, fila.servidores)
        fila.n += 1
        if servidores_ocupados_antes < fila.servidores:
            atendimento = rng.uniform(*fila.service_range)
            esc.agenda(tempo + atendimento, SAIDA, fila)
        # caso contrario, cliente so espera - nada a agendar agora
    else:
        fila.perdas += 1


def processa_saida(fila, tempo, rng, esc):
    n_antes = fila.n
    fila.n -= 1

    if n_antes > fila.servidores:  # tinha gente esperando -> ocupa o servidor liberado
        atendimento = rng.uniform(*fila.service_range)
        esc.agenda(tempo + atendimento, SAIDA, fila)

    if fila.downstream is not None:
        processa_chegada(fila.downstream, tempo, rng, esc)


def simula(seed, max_randoms=100_000, primeira_chegada_tempo=2.5):
    rng = LCG(seed)
    esc = Escalonador()

    fila2 = Fila("Fila 2", servidores=1, capacidade=5,
                 service_range=(1, 3), arrival_range=None, downstream=None)
    fila1 = Fila("Fila 1", servidores=2, capacidade=3,
                 service_range=(4, 5), arrival_range=(1, 5), downstream=fila2)
    filas = [fila1, fila2]

    esc.agenda(primeira_chegada_tempo, CHEGADA, fila1)  # agendada na mao, nao gasta aleatorio
    tempo_global = 0.0

    while rng.count < max_randoms and not esc.vazio():
        if rng.count >= max_randoms:
            break
        tempo, _, tipo, fila = esc.proximo()

        for f in filas:  # tempo passa igual pras duas filas, mude o estado de quem mudar
            f.acumula_tempo(tempo)
        tempo_global = tempo

        if tipo == CHEGADA:
            processa_chegada(fila, tempo, rng, esc)
        else:
            processa_saida(fila, tempo, rng, esc)

    return filas, tempo_global, rng.count


def imprime_resultados(filas, tempo_global, total_randoms):
    print(f"Numeros pseudoaleatorios utilizados: {total_randoms}")
    print(f"Tempo global de simulacao: {tempo_global:.4f}\n")
    for f in filas:
        print(f"===== {f.nome} (servidores={f.servidores}, capacidade={f.capacidade}) =====")
        print(f"Perdas de clientes: {f.perdas}")
        print(f"{'Estado':>8} | {'Tempo acumulado':>16} | {'Probabilidade':>13}")
        soma_check = 0.0
        for estado, tempo_estado in enumerate(f.tempo_acumulado):
            prob = tempo_estado / tempo_global if tempo_global > 0 else 0.0
            soma_check += prob
            print(f"{estado:>8} | {tempo_estado:>16.4f} | {prob:>13.6f}")
        print(f"{'soma':>8} | {'':>16} | {soma_check:>13.6f}")
        print()


if __name__ == "__main__":
    filas, tempo_global, total_randoms = simula(seed=123456789)
    imprime_resultados(filas, tempo_global, total_randoms)
