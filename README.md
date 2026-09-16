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
