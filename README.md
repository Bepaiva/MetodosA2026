# Simulador de Filas em Tandem

Disciplina: **Simulação e Métodos Analíticos** — PUCRS
Módulo 6 | Desenvolvimento de Simulador para Filas em Tandem

Grupo T1 - 690 - 43: Eduardo Ferreira Alves, Bernardo Hoff Paiva dos Santos, Matheus Stumff Mota

## O que este simulador faz

Simula uma rede de duas filas em tandem (Fila 1 → Fila 2), usando simulação orientada a eventos discretos:

- **Fila 1**: G/G/2/3 — 2 servidores, capacidade total do sistema = 3, chegadas externas.
- **Fila 2**: G/G/1/5 — 1 servidor, capacidade total do sistema = 5. Não recebe chegadas externas: 100% dos clientes que saem da Fila 1 entram na Fila 2.
- Cliente perdido (bloqueado) quando chega numa fila que já está na capacidade máxima.
- Gerador de números pseudoaleatórios próprio, pelo Método Congruente Linear (LCG), sem depender de bibliotecas prontas de aleatoriedade.
- A simulação encerra assim que o 100.000º número pseudoaleatório é consumido.

Ao final, o programa imprime, para cada fila: o tempo acumulado e a probabilidade de cada estado (0 até a capacidade máxima), o número de clientes perdidos e o tempo global de simulação.

## Requisitos

- Python 3.8 ou superior (não usa nenhuma biblioteca externa, só `heapq` da biblioteca padrão).

## Como executar

```bash
python3 tandem_sim.py
```

Isso roda a simulação com os parâmetros do trabalho (Fila 1: chegadas 1..5, atendimento 4..5; Fila 2: atendimento 1..3; primeiro cliente em t=2,5) e imprime o relatório no terminal.

## Como mudar os parâmetros

Todos os parâmetros ficam explícitos dentro da função `simula()`, no arquivo `tandem_sim.py`:

```python
def simula(seed, max_randoms=100_000, primeira_chegada_tempo=2.5):
    fila2 = Fila("Fila 2", servidores=1, capacidade=5,
                 service_range=(1, 3), arrival_range=None, downstream=None)
    fila1 = Fila("Fila 1", servidores=2, capacidade=3,
                 service_range=(4, 5), arrival_range=(1, 5), downstream=fila2)
```

- `servidores`: número de servidores da fila.
- `capacidade`: capacidade total do sistema (fila + em atendimento).
- `service_range` / `arrival_range`: intervalo (mín, máx) para tempo de atendimento / entre chegadas, sorteado uniformemente.
- `downstream`: para onde o cliente vai ao sair da fila (outra `Fila`, ou `None` se sai do sistema).
- `seed`, `max_randoms`, `primeira_chegada_tempo`: passados na chamada de `simula(...)` no final do arquivo.

Para simular uma fila única (sem rede), basta criar uma `Fila` com `downstream=None` e chamar o loop principal só com ela — veja `validate_m4_referencia_professor.py` como exemplo, que reaproveita as mesmas classes (`LCG`, `Fila`, `Escalonador`) para simular G/G/1/5 e G/G/2/5 isoladas.

## Gerador de números pseudoaleatórios

Implementado do zero na classe `LCG` (Método Congruente Linear):

```
X(n+1) = (a * X(n) + c) mod M
```

Parâmetros usados nesta entrega: `a = 1103515245`, `c = 12345`, `M = 2^31`, semente (`X0`) = `123456789`. O período de M ≈ 2,1 bilhões garante que a sequência não repete dentro dos 100.000 números usados na simulação.

## Estrutura do código

- `LCG`: gerador de números pseudoaleatórios.
- `Fila`: entidade fila (servidores, capacidade, estado atual, tempos acumulados, perdas).
- `Escalonador`: fila de prioridade por tempo (min-heap) para os eventos.
- `processa_chegada` / `processa_saida`: procedimentos que tratam os eventos de CHEGADA e SAÍDA/PASSAGEM.
- `simula`: monta a rede de filas e roda o laço principal da simulação.
- `imprime_resultados`: formata e imprime o relatório final.

## Validação

Os resultados foram conferidos rodando o mesmo motor de simulação com os parâmetros de referência divulgados pelo professor no Mural de Avisos (feedback do M4, fila única G/G/1/5 e G/G/2/5), com resultados muito próximos aos publicados — ver `validate_m4_referencia_professor.py`.

---

# Simulador de Rede de Filas com Topologia Genérica (Módulo 8 / T1)

Disciplina: **Simulação e Métodos Analíticos** — PUCRS
T1 | Avaliação de Aprendizagem — generalização do simulador para qualquer topologia de rede de filas.

Grupo T1 - 690 - 43: Eduardo Ferreira Alves, Bernardo Hoff Paiva dos Santos, Matheus Stumff Mota

## O que este simulador faz

`network_sim.py` generaliza o simulador de filas em tandem (acima) para aceitar **qualquer rede de filas**, com qualquer número de filas, qualquer topologia de roteamento (incluindo ciclos e auto-loops) e qualquer combinação de capacidades/servidores. A rede inteira é descrita em um arquivo YAML, no mesmo estilo do simulador de referência disponibilizado no Módulo 3 (`simulator.jar`), para facilitar a comparação de resultados.

Mantém as mesmas regras de simulação já usadas no Módulo 6:

- Gerador de números pseudoaleatórios próprio (LCG), sem bibliotecas de aleatoriedade.
- A simulação encerra assim que o N-ésimo número pseudoaleatório é consumido (default: 100.000).
- Cliente perdido (bloqueado) quando chega numa fila que já está na capacidade máxima; filas sem `capacity` definida (ou `-1`) têm capacidade ilimitada.
- Roteamento probabilístico: ao terminar o atendimento, o cliente é direcionado para uma fila de destino sorteada entre as probabilidades declaradas em `network`; a probabilidade que "falta" para somar 1.0 significa que o cliente sai do sistema.

## Requisitos

- Python 3.8+ e a biblioteca `PyYAML` (`pip install pyyaml`).

## Como executar

```bash
python3 network_sim.py model_t1.yml
```

O argumento é o caminho do arquivo YAML com a rede a simular. Por padrão encerra aos 100.000 números pseudoaleatórios; para mudar isso:

```bash
python3 network_sim.py model_t1.yml --max-randoms 50000
```

O programa imprime, para cada fila da rede: o tempo acumulado e a probabilidade de cada estado (população), o número de clientes perdidos, além do tempo global de simulação.

## Formato do arquivo YAML de entrada

```yaml
arrivals:               # filas com chegada externa de clientes, e o instante do 1o cliente
  Q1: 2.0

queues:
  Q1:
    servers: 1
    capacity: -1          # -1 (ou omitido) = capacidade ilimitada
    minArrival: 2.0        # so' precisa existir em filas com chegada externa
    maxArrival: 4.0
    minService: 1.0
    maxService: 2.0
  Q2:
    servers: 2
    capacity: 5
    minService: 4.0
    maxService: 6.0

network:                  # roteamento entre filas; a probabilidade que falta para 1.0 = sai do sistema
  - source: Q1
    target: Q2
    probability: 0.2

seed: 123456789            # semente do gerador LCG proprio
```

Veja `model_t1.yml` neste repositório para a rede de validação completa (3 filas, com roteamento cíclico e auto-loop em Q2).

## Rede de validação (T1)

- **Q1** — G/G/1, ilimitada, chegadas externas entre 2..4 min (1º cliente em t=2,0), atendimento 1..2 min.
- **Q2** — G/G/2/5, atendimento 4..6 min. Sem chegada externa.
- **Q3** — G/G/2/10, atendimento 5..15 min. Sem chegada externa.
- Roteamento: Q1→Q2 (0,2) / Q1→Q3 (0,8); Q2→Q1 (0,3) / Q2→Q2 auto-loop (0,5) / Q2→sai (0,2); Q3→Q2 (0,7) / Q3→sai (0,3).

Resultados completos dessa rede (distribuição de estados, perdas por fila e tempo global) estão no PDF de entrega do T1.

## Validação contra o simulador de referência (Módulo 3)

O motor foi reconstruído a partir da leitura cuidadosa do bytecode de `simulator.jar` (decompilação com `javap`), garantindo que a ordem de consumo dos números aleatórios (roteamento antes da duração do atendimento, contabilização de tempo em todas as filas a cada evento, etc.) seguisse a mesma lógica da referência.

Para validar, alimentamos o `simulator.jar` com a *mesma sequência exata* de números pseudoaleatórios consumida pelo `network_sim.py` (opção `rndnumbers` do YAML da referência) e comparamos os relatórios: as probabilidades de estado de cada fila e o tempo global de simulação ficaram praticamente idênticos entre as duas implementações (diferença abaixo de 0,5 ponto percentual). Pequenas diferenças no número de perdas são esperadas — cada implementação consulta o estado da rede em pontos ligeiramente diferentes, o que se acumula ao longo de 100 mil eventos — mas o comportamento agregado (ocupação, saturação de cada fila, tempo médio) é equivalente.
