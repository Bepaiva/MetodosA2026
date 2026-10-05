"""
Simulador de rede de filas com topologia generica - Modulo 8 (T1), Simulacao e Metodos Analiticos.
Generaliza o simulador de filas em tandem (Modulo 6) para aceitar qualquer rede de filas,
descrita em um arquivo YAML no mesmo estilo do simulador de referencia do Modulo 3.
Encerra ao consumir o N-esimo numero pseudoaleatorio (default 100.000).

Uso:
    python3 network_sim.py modelo.yml [--max-randoms N]

Formato do YAML de entrada (ver model_t1.yml para um exemplo completo):
    arrivals:                  # filas com chegada externa e o instante do 1o cliente
      Q1: 2.0
    queues:
      Q1:
        servers: 1
        capacity: -1            # -1 ou omitido = capacidade ilimitada
        minArrival: 2.0
        maxArrival: 4.0
        minService: 1.0
        maxService: 2.0
    network:                    # roteamento entre filas; probabilidade restante = saida do sistema
      - source: Q1
        target: Q2
        probability: 0.2
    seed: 123456789
"""

import sys
import heapq
import yaml


class LCG:
    """X(n+1) = (a*X(n) + c) mod M. next_random() normaliza para [0,1)."""

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
    def __init__(self, nome, servidores, capacidade, service_range, arrival_range=None):
        self.nome = nome
        self.servidores = servidores
        self.capacidade = capacidade            # None = ilimitada
        self.service_range = service_range
        self.arrival_range = arrival_range      # None = sem chegada externa
        self.destinos = []                      # lista de (fila_destino_ou_None, probabilidade)

        self.n = 0
        self.perdas = 0
        self.tempo_acumulado = {}               # estado (int) -> tempo acumulado
        self.last_change_time = 0.0

    def acumula_tempo(self, tempo_atual):
        delta = tempo_atual - self.last_change_time
        if delta > 0:
            self.tempo_acumulado[self.n] = self.tempo_acumulado.get(self.n, 0.0) + delta
        self.last_change_time = tempo_atual

    def escolhe_destino(self, rng):
        """Sorteia para onde vai o cliente que acabou de ser atendido.
        Probabilidade que nao aparece na lista de destinos = sai da rede (retorna None)."""
        if not self.destinos:
            return None
        if len(self.destinos) == 1 and self.destinos[0][1] >= 1.0:
            return self.destinos[0][0]
        r = rng.next_random()
        acumulado = 0.0
        for destino, p in self.destinos:
            acumulado += p
            if r <= acumulado:
                return destino
        return None


CHEGADA = "CHEGADA"
SAIDA = "SAIDA"


class Escalonador:
    def __init__(self):
        self._heap = []
        self._seq = 0  # desempate para eventos com o mesmo tempo (ordem de chegada no escalonador)

    def agenda(self, tempo, tipo, fila, destino=None):
        self._seq += 1
        heapq.heappush(self._heap, (tempo, self._seq, tipo, fila, destino))

    def proximo(self):
        return heapq.heappop(self._heap)

    def vazio(self):
        return len(self._heap) == 0


def monta_rede(config):
    """Le o dict ja carregado do YAML e constroi as filas e a lista de chegadas iniciais."""
    filas = {}
    for nome, q in config.get("queues", {}).items():
        capacidade = q.get("capacity", -1)
        capacidade = None if capacidade is None or capacidade < 0 else capacidade

        tem_chegada = "minArrival" in q and "maxArrival" in q
        arrival_range = (q["minArrival"], q["maxArrival"]) if tem_chegada else None

        filas[nome] = Fila(
            nome=nome,
            servidores=q["servers"],
            capacidade=capacidade,
            service_range=(q["minService"], q["maxService"]),
            arrival_range=arrival_range,
        )

    for edge in config.get("network", []):
        filas[edge["source"]].destinos.append((filas[edge["target"]], edge["probability"]))

    chegadas_iniciais = [
        (filas[nome], tempo) for nome, tempo in config.get("arrivals", {}).items()
    ]

    return filas, chegadas_iniciais


def processa_chegada(fila, tempo, rng, esc, agenda_proxima):
    if agenda_proxima and fila.arrival_range is not None:
        intervalo = rng.uniform(*fila.arrival_range)
        esc.agenda(tempo + intervalo, CHEGADA, fila)

    bloqueado = fila.capacidade is not None and fila.n >= fila.capacidade
    if bloqueado:
        fila.perdas += 1
        return

    servidores_ocupados_antes = min(fila.n, fila.servidores)
    fila.n += 1
    if servidores_ocupados_antes < fila.servidores:
        destino = fila.escolhe_destino(rng)
        atendimento = rng.uniform(*fila.service_range)
        esc.agenda(tempo + atendimento, SAIDA, fila, destino)


def processa_saida(fila, tempo, rng, esc, destino_evento):
    n_antes = fila.n
    fila.n -= 1

    if n_antes > fila.servidores:  # tinha gente esperando -> ocupa o servidor liberado
        destino = fila.escolhe_destino(rng)
        atendimento = rng.uniform(*fila.service_range)
        esc.agenda(tempo + atendimento, SAIDA, fila, destino)

    if destino_evento is not None:
        processa_chegada(destino_evento, tempo, rng, esc, agenda_proxima=False)


def simula(config, max_randoms=100_000):
    rng = LCG(config["seed"])
    esc = Escalonador()
    filas, chegadas_iniciais = monta_rede(config)

    for fila, tempo0 in chegadas_iniciais:
        esc.agenda(tempo0, CHEGADA, fila)  # agendada na mao, nao gasta aleatorio

    tempo_global = 0.0
    while rng.count < max_randoms and not esc.vazio():
        tempo, _, tipo, fila, destino = esc.proximo()

        for f in filas.values():  # tempo passa igual pra todas, mude o estado de quem mudar
            f.acumula_tempo(tempo)
        tempo_global = tempo

        if tipo == CHEGADA:
            processa_chegada(fila, tempo, rng, esc, agenda_proxima=True)
        else:
            processa_saida(fila, tempo, rng, esc, destino)

    return filas, tempo_global, rng.count


def imprime_resultados(filas, tempo_global, total_randoms):
    print(f"Numeros pseudoaleatorios utilizados: {total_randoms}")
    print(f"Tempo global de simulacao: {tempo_global:.4f}\n")
    for nome, f in filas.items():
        cap_str = "ilimitada" if f.capacidade is None else str(f.capacidade)
        print(f"===== {nome} (servidores={f.servidores}, capacidade={cap_str}) =====")
        print(f"Perdas de clientes: {f.perdas}")
        print(f"{'Estado':>8} | {'Tempo acumulado':>16} | {'Probabilidade':>13}")
        soma_check = 0.0
        maior_estado = max(f.tempo_acumulado) if f.tempo_acumulado else 0
        for estado in range(maior_estado + 1):
            tempo_estado = f.tempo_acumulado.get(estado, 0.0)
            prob = tempo_estado / tempo_global if tempo_global > 0 else 0.0
            soma_check += prob
            print(f"{estado:>8} | {tempo_estado:>16.4f} | {prob:>13.6f}")
        print(f"{'soma':>8} | {'':>16} | {soma_check:>13.6f}")
        print()


def main():
    if len(sys.argv) < 2:
        print("uso: python3 network_sim.py modelo.yml [--max-randoms N]")
        sys.exit(1)

    max_randoms = 100_000
    if "--max-randoms" in sys.argv:
        i = sys.argv.index("--max-randoms")
        max_randoms = int(sys.argv[i + 1])

    with open(sys.argv[1]) as f:
        config = yaml.safe_load(f)

    filas, tempo_global, total_randoms = simula(config, max_randoms=max_randoms)
    imprime_resultados(filas, tempo_global, total_randoms)


if __name__ == "__main__":
    main()
