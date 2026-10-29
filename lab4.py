# ============================================================
# Laboratório Avaliado 4 — Projeto e Análise de Algoritmos I
# UFRGS — Instituto de Informática
# ============================================================
# Nome: ______________________________________________________
# Cartão: ____________________________________________________
# ============================================================
#
# Instruções:
#   - Complete as funções indicadas com "# TODO".
#   - A estrutura Union-Find (classe UnionFind), a função de leitura dos
#     casos (carregar_casos) e a função de integração (analise_casos)
#     já são fornecidas prontas.
#   - Após cada função a ser implementada, indique a complexidade
#     no comentário marcado com "# Complexidade: O( )".
#     Use n para |V| (número de vértices), m para |E| (número de arestas)
#     e α(n) para o custo amortizado de find e union da UnionFind
#     (inversa da função de Ackermann).
#   - Execute com: python3 lab4.py
#   - Ao implementar as funções, o script executará os testes e
#     avaliará o desempenho nos casos de dengue de Porto Alegre
#     (~7.000 casos), gerando o arquivo "resultado_lab4.html" para
#     inspeção visual.
#
# Regras:
#   - Não altere as assinaturas das funções nem as funções fornecidas.
#   - Utilize apenas a biblioteca padrão do Python.
#     Não utilize bibliotecas externas como networkx ou numpy.
# ============================================================

import time
import os

# Módulo visualizador auxiliar fornecido
try:
    from visualizador import gerar_visualizacao_html
except ImportError:
    gerar_visualizacao_html = None


# ============================================================
# Grafos didáticos usados nos exemplos e testes iniciais
# ============================================================
#
#  Os grafos são não dirigidos e com pesos, dados por uma lista de vértices
#  e uma lista de arestas (u, v, peso).
#
#  G_AULA — grafo do notebook da Aula 20 (sem o vértice isolado F):
#
#            A ----5---- D
#          1/  \4      4/  \2
#          S     \    /     E
#          3\     \  /     /6
#            B ----1---- C
#
#  G_FOCOS — casos de dengue; o peso é a distância entre os casos:
#
#        A ---1--- B -----11----- D ---2--- E
#          \       |              |       /
#           4      3              6      5
#             \    |              |    /
#               \  |              |  /
#                  C ------9----- F -------14------- G
#                   \                               /
#                    `--------------16-------------'
#
# ============================================================

VERTICES_AULA = ['S', 'A', 'B', 'C', 'D', 'E']
ARESTAS_AULA = [
    ('S', 'A', 1), ('S', 'B', 3), ('A', 'D', 5), ('A', 'C', 4),
    ('B', 'D', 4), ('B', 'C', 1), ('C', 'E', 6), ('D', 'E', 2),
]

VERTICES_FOCOS = ['A', 'B', 'C', 'D', 'E', 'F', 'G']
ARESTAS_FOCOS = [
    ('A', 'B', 1), ('B', 'C', 3), ('A', 'C', 4), ('D', 'E', 2),
    ('E', 'F', 5), ('D', 'F', 6), ('C', 'F', 9), ('B', 'D', 11),
    ('F', 'G', 14), ('C', 'G', 16),
]


# ============================================================
# Estrutura Union-Find (Aula 21)
# (Fornecida pronta. Não é necessário editar este bloco)
# ============================================================

class UnionFind:
    """
    Estrutura Union-Find (conjuntos disjuntos), como vista na Aula 21,
    com compressão de caminho e união por rank. Classe fornecida.

    Cada conjunto é uma árvore de ponteiros: pai[v] aponta para o próximo
    elemento no caminho até a raiz, e a raiz (pai[r] == r) é o representante
    do conjunto. rank[r] é uma estimativa da altura da árvore de raiz r.

    Operações (n = número de elementos):
        UnionFind(elementos) : O(n)
        find(v)              : O(α(n)) amortizado
        union(u, v)          : O(α(n)) amortizado
        componentes          : O(1) (atributo)

    α(n) é a inversa da função de Ackermann, que cresce tão devagar que
    α(n) <= 4 para qualquer n prático: na prática, cada operação custa O(1).
    Uma sequência de q operações custa O(q α(n)) no total (resultado de Tarjan).

    Exemplo:
        uf = UnionFind(['a', 'b', 'c', 'd'])
        uf.union('a', 'b')            -> True
        uf.union('b', 'a')            -> False  (já estão no mesmo conjunto)
        uf.find('a') == uf.find('b')  -> True
        uf.find('a') == uf.find('c')  -> False
        uf.componentes                -> 3      ({a, b}, {c}, {d})
    """

    def __init__(self, elementos):
        """
        Cria um conjunto unitário para cada elemento: pai[v] = v, rank[v] = 0.

        Complexidade: O(n)
        """
        self.pai = {v: v for v in elementos}
        self.rank = {v: 0 for v in elementos}
        self.componentes = len(self.pai)

    def find(self, v):
        """
        Retorna a raiz (representante) do conjunto que contém v.

        Compressão de caminho: todos os elementos do caminho de v até a raiz
        passam a apontar diretamente para a raiz, encurtando as próximas buscas.

        Complexidade: O(α(n)) amortizado. Uma única chamada custa, no pior
        caso, O(log n), pois a união por rank limita a altura das árvores.
        """
        if self.pai[v] != v:
            self.pai[v] = self.find(self.pai[v])
        return self.pai[v]

    def union(self, u, v) -> bool:
        """
        Une os conjuntos que contêm u e v. União por rank: a raiz de menor rank
        passa a apontar para a raiz de maior rank (o rank só aumenta quando os
        dois ranks são iguais).

        Retorna True se u e v estavam em conjuntos diferentes (e foram unidos)
        e False se já estavam no mesmo conjunto.

        Complexidade: O(α(n)) amortizado (duas chamadas a find, mais O(1)).
        """
        r, s = self.find(u), self.find(v)
        if r == s:
            return False
        if self.rank[r] < self.rank[s]:
            r, s = s, r
        self.pai[s] = r
        if self.rank[r] == self.rank[s]:
            self.rank[r] += 1
        self.componentes -= 1
        return True


# ============================================================
# Parte 1 — Algoritmo de Kruskal
# ============================================================

def kruskal(vertices, arestas: list) -> tuple[float, list]:
    """
    Calcula uma árvore geradora mínima (AGM) de um grafo não dirigido com
    pesos, utilizando o algoritmo de Kruskal com a estrutura UnionFind,
    como visto na Aula 21.

    Conceito da Aula 21:
      - Percorra as arestas em ordem crescente de peso.
      - Uma aresta (u, v) entra na árvore se u e v estão em componentes
        diferentes (isto é, se ela não forma um ciclo); nesse caso, as duas
        componentes são unidas.
      - A árvore está completa quando tiver n - 1 arestas.

    Parâmetros:
        vertices : coleção de vértices do grafo
        arestas  : lista de triplas (u, v, peso)

    Retorna:
        tuple[float, list] : (custo, agm)
            - custo: soma dos pesos das arestas da AGM
            - agm  : lista de triplas (u, v, peso) da AGM, na ordem em que
                     entraram na árvore
            Se o grafo for desconexo, não existe árvore geradora: retorne
            (float('inf'), []).

    Exemplos:
        kruskal(VERTICES_AULA, ARESTAS_AULA) -> (11, [('S', 'A', 1), ('B', 'C', 1), ('D', 'E', 2),
                                                     ('S', 'B', 3), ('B', 'D', 4)])
        kruskal(['X'], []) -> (0, [])
    """
    # TODO: implemente esta função usando a classe UnionFind.

    uf = UnionFind(vertices)
    agm = []
    custo = 0

    # TODO

    return (custo, agm)

    # Complexidade: O( )


print("=" * 60)
print("  Parte 1 — Algoritmo de Kruskal")
print("=" * 60)
print()
print("kruskal(VERTICES_AULA, ARESTAS_AULA):")
print("  obtido  :", kruskal(VERTICES_AULA, ARESTAS_AULA))
print("  esperado: (11, [('S', 'A', 1), ('B', 'C', 1), ('D', 'E', 2), ('S', 'B', 3), ('B', 'D', 4)])")
print()
print("kruskal(VERTICES_FOCOS, ARESTAS_FOCOS):")
print("  obtido  :", kruskal(VERTICES_FOCOS, ARESTAS_FOCOS))
print("  esperado: (34, [('A', 'B', 1), ('D', 'E', 2), ('B', 'C', 3), ('E', 'F', 5), ('C', 'F', 9), ('F', 'G', 14)])")
print()


# ============================================================
# Parte 2 — Focos de Transmissão (Raio r)
# ============================================================

def agrupar_raio(vertices, arestas: list, r) -> list:
    """
    Agrupa os casos em focos de transmissão: dois casos a uma distância
    menor ou igual a r estão no mesmo foco, e a relação é transitiva
    (se A está perto de B e B está perto de C, então A, B e C estão no
    mesmo foco, mesmo que A e C estejam longe um do outro).

    Utilize a classe UnionFind fornecida:
      - Cada caso começa em seu próprio foco.
      - Toda aresta com distância <= r une os focos de suas extremidades.
      - Equivale a executar o algoritmo de Kruskal e interrompê-lo na primeira
        aresta com distância maior que r. Pense: a ordem em que as arestas são
        processadas muda o resultado?

    Parâmetros:
        vertices : coleção de casos (vértices)
        arestas  : lista de triplas (u, v, distancia)
        r        : distância máxima para que dois casos sejam ligados

    Retorna:
        list : lista de focos, onde cada foco é uma lista de casos.
               A ordem dos focos e dos casos dentro de cada foco não importa.

    Exemplos:
        agrupar_raio(VERTICES_FOCOS, ARESTAS_FOCOS, 3) -> [['A', 'B', 'C'], ['D', 'E'], ['F'], ['G']]
        agrupar_raio(VERTICES_FOCOS, ARESTAS_FOCOS, 5) -> [['A', 'B', 'C'], ['D', 'E', 'F'], ['G']]
    """
    # TODO: implemente esta função usando a classe UnionFind.

    uf = UnionFind(vertices)

    # TODO

    focos = {}
    for v in vertices:
        pass

    return list(focos.values())

    # Complexidade: O( )


print("=" * 60)
print("  Parte 2 — Focos de Transmissão (Raio r)")
print("=" * 60)
print()
for _r, _esp in [(3, "[['A', 'B', 'C'], ['D', 'E'], ['F'], ['G']]"),
                 (5, "[['A', 'B', 'C'], ['D', 'E', 'F'], ['G']]")]:
    print(f"agrupar_raio(VERTICES_FOCOS, ARESTAS_FOCOS, {_r}):")
    print("  obtido  :", agrupar_raio(VERTICES_FOCOS, ARESTAS_FOCOS, _r))
    print("  esperado:", _esp, "(em qualquer ordem)")
    print()


# ============================================================
# Parte 3 — Divisão em k Grupos (Espaçamento Máximo)
# ============================================================

def agrupar_k(vertices, arestas: list, k: int) -> tuple[float, list]:
    """
    Divide os casos em exatamente k grupos com ESPAÇAMENTO MÁXIMO.

    O espaçamento de uma divisão em grupos é a menor distância entre dois
    casos de grupos diferentes. Queremos a divisão em k grupos cujo
    espaçamento é o maior possível (grupos bem separados entre si).

    Utilize a classe UnionFind fornecida:
      - Execute o algoritmo de Kruskal, mas interrompa-o quando restarem
        exatamente k componentes: elas são os k grupos.
      - O espaçamento é a distância da PRÓXIMA aresta que ligaria dois grupos
        diferentes. Cuidado: a próxima aresta da lista ordenada pode ligar
        dois casos do mesmo grupo (veja o caso k = 3 em G_FOCOS).
      - Se k = 1, não há dois grupos diferentes e o espaçamento é float('inf').

    Parâmetros:
        vertices : coleção de casos (vértices); suponha que o grafo é conexo
        arestas  : lista de triplas (u, v, distancia)
        k        : número de grupos (1 <= k <= n)

    Retorna:
        tuple[float, list] : (espacamento, grupos)
            - espacamento: menor distância entre casos de grupos diferentes
            - grupos     : lista com os k grupos, cada um uma lista de casos.
                           A ordem dos grupos e dos casos não importa.

    Exemplos:
        agrupar_k(VERTICES_FOCOS, ARESTAS_FOCOS, 3) -> (9, [['A', 'B', 'C'], ['D', 'E', 'F'], ['G']])
        agrupar_k(VERTICES_FOCOS, ARESTAS_FOCOS, 1) -> (inf, [['A', 'B', 'C', 'D', 'E', 'F', 'G']])
    """
    # TODO: implemente esta função usando a classe UnionFind.

    uf = UnionFind(vertices)
    espacamento = float('inf')

    # TODO: Kruskal interrompido quando restarem k grupos (uf.componentes == k)

    # TODO: espaçamento = distância da próxima aresta que liga dois grupos diferentes

    grupos = {}
    for v in vertices:
        pass

    return (espacamento, list(grupos.values()))

    # Complexidade: O( )


print("=" * 60)
print("  Parte 3 — Divisão em k Grupos (Espaçamento Máximo)")
print("=" * 60)
print()
for _k, _esp in [(3, "(9, [['A', 'B', 'C'], ['D', 'E', 'F'], ['G']])"),
                 (4, "(5, [['A', 'B', 'C'], ['D', 'E'], ['F'], ['G']])")]:
    print(f"agrupar_k(VERTICES_FOCOS, ARESTAS_FOCOS, {_k}):")
    print("  obtido  :", agrupar_k(VERTICES_FOCOS, ARESTAS_FOCOS, _k))
    print("  esperado:", _esp, "(em qualquer ordem)")
    print()


# ============================================================
# Funções Auxiliares Fornecidas
# (Não é necessário editar este bloco)
# ============================================================

def carregar_casos(caminho_arquivo: str) -> tuple[dict, list]:
    """
    Lê o arquivo dos casos de dengue.
    Função auxiliar fornecida.

    Formato (linhas iniciadas por '#' são comentários):
        n m
        n linhas: id x y                (posição do caso, em metros)
        m linhas: u v distancia_m       (par de casos próximos)

    Retorna:
        tuple[coords, arestas]:
            - coords : dict mapeando id -> (x, y) em metros, usado na visualização
            - arestas: lista de triplas (u, v, distancia_m), não dirigidas
    """
    with open(caminho_arquivo, "r", encoding="utf-8") as f:
        linhas = [l.split() for l in f if l.strip() and not l.startswith('#')]

    n, m = map(int, linhas[0])
    coords = {}
    for partes in linhas[1:1 + n]:
        coords[int(partes[0])] = (float(partes[1]), float(partes[2]))
    arestas = [tuple(map(int, partes)) for partes in linhas[1 + n:1 + n + m]]
    return (coords, arestas)


def analise_casos(vertices, arestas: list, r, k: int) -> dict:
    """
    Integra as funções implementadas:
      1. AGM dos casos pelo algoritmo de Kruskal (Parte 1);
      2. focos de transmissão com raio r (Parte 2);
      3. divisão em k grupos com espaçamento máximo (Parte 3).
    """
    custo_kruskal, agm_kruskal = kruskal(vertices, arestas)
    focos_r = agrupar_raio(vertices, arestas, r)
    espacamento_k, grupos_k = agrupar_k(vertices, arestas, k)

    return {
        "custo_kruskal": custo_kruskal,
        "agm_kruskal": agm_kruskal,
        "focos_r": focos_r,
        "isolados_r": sum(1 for f in focos_r if len(f) == 1),
        "espacamento_k": espacamento_k,
        "grupos_k": grupos_k,
    }


def _fmt_metros(d: float) -> str:
    if d == float('inf'):
        return "—"
    return f"{d} m"


# ============================================================
# ==================== TESTES FINAIS =========================
# ============================================================

def _titulo(s):
    print(f"\n{'='*60}")
    print(f"  {s}")
    print('='*60)

def _ok(descricao, obtido, esperado):
    status = "✓ OK" if obtido == esperado else "✗ FALHOU"
    print(f"  [{status}] {descricao}")
    if obtido != esperado:
        print(f"          esperado : {esperado}")
        print(f"          obtido   : {obtido}")

def _arestas(resultado):
    """Normaliza (custo, arestas): a ordem das arestas e das extremidades não importa."""
    custo, arestas = resultado
    return (custo, sorted((min(u, v), max(u, v), p) for u, v, p in arestas))

def _grupos(grupos):
    """Normaliza uma lista de grupos: a ordem dos grupos e dos elementos não importa."""
    return sorted(sorted(g) for g in grupos)

def _espacamento(arestas, grupos):
    """Menor distância entre vértices de grupos diferentes (inf se não houver)."""
    grupo_de = {v: i for i, g in enumerate(grupos) for v in g}
    return min((d for u, v, d in arestas if grupo_de[u] != grupo_de[v]), default=float('inf'))


AGM_AULA = (11, [('A', 'S', 1), ('B', 'C', 1), ('B', 'D', 4), ('B', 'S', 3), ('D', 'E', 2)])
AGM_FOCOS = (34, [('A', 'B', 1), ('B', 'C', 3), ('C', 'F', 9), ('D', 'E', 2), ('E', 'F', 5), ('F', 'G', 14)])

_titulo("Testes Finais — Parte 1 (Kruskal)")
_ok("kruskal(G_AULA)", _arestas(kruskal(VERTICES_AULA, ARESTAS_AULA)), AGM_AULA)
_ok("kruskal(G_FOCOS)", _arestas(kruskal(VERTICES_FOCOS, ARESTAS_FOCOS)), AGM_FOCOS)
_ok("kruskal(G_FOCOS) - arestas em ordem crescente de peso",
    [p for *_, p in kruskal(VERTICES_FOCOS, ARESTAS_FOCOS)[1]], [1, 2, 3, 5, 9, 14])
_ok("kruskal(['X'], []) - um único vértice", kruskal(['X'], []), (0, []))
_ok("kruskal(G_AULA + vértice isolado F) - desconexo",
    kruskal(VERTICES_AULA + ['F'], ARESTAS_AULA), (float('inf'), []))


_titulo("Testes Finais — Parte 2 (Focos com Raio r)")
_ok("agrupar_raio(G_FOCOS, r=0) - cada caso é um foco",
    _grupos(agrupar_raio(VERTICES_FOCOS, ARESTAS_FOCOS, 0)), [[v] for v in VERTICES_FOCOS])
_ok("agrupar_raio(G_FOCOS, r=3)", _grupos(agrupar_raio(VERTICES_FOCOS, ARESTAS_FOCOS, 3)),
    [['A', 'B', 'C'], ['D', 'E'], ['F'], ['G']])
_ok("agrupar_raio(G_FOCOS, r=5) - distância igual a r liga os casos",
    _grupos(agrupar_raio(VERTICES_FOCOS, ARESTAS_FOCOS, 5)), [['A', 'B', 'C'], ['D', 'E', 'F'], ['G']])
_ok("agrupar_raio(G_FOCOS, r=10)", _grupos(agrupar_raio(VERTICES_FOCOS, ARESTAS_FOCOS, 10)),
    [['A', 'B', 'C', 'D', 'E', 'F'], ['G']])
_ok("agrupar_raio(G_FOCOS, r=100) - um único foco",
    _grupos(agrupar_raio(VERTICES_FOCOS, ARESTAS_FOCOS, 100)), [VERTICES_FOCOS])


_titulo("Testes Finais — Parte 3 (k Grupos com Espaçamento Máximo)")
_esp, _g = agrupar_k(VERTICES_FOCOS, ARESTAS_FOCOS, 1)
_ok("agrupar_k(G_FOCOS, k=1) - um grupo, espaçamento infinito", (_esp, _grupos(_g)),
    (float('inf'), [VERTICES_FOCOS]))
_esp, _g = agrupar_k(VERTICES_FOCOS, ARESTAS_FOCOS, 2)
_ok("agrupar_k(G_FOCOS, k=2)", (_esp, _grupos(_g)), (14, [['A', 'B', 'C', 'D', 'E', 'F'], ['G']]))
_esp, _g = agrupar_k(VERTICES_FOCOS, ARESTAS_FOCOS, 3)
_ok("agrupar_k(G_FOCOS, k=3) - a aresta D-F (6) é interna a um grupo", (_esp, _grupos(_g)),
    (9, [['A', 'B', 'C'], ['D', 'E', 'F'], ['G']]))
_esp, _g = agrupar_k(VERTICES_FOCOS, ARESTAS_FOCOS, 4)
_ok("agrupar_k(G_FOCOS, k=4) - a aresta A-C (4) é interna a um grupo", (_esp, _grupos(_g)),
    (5, [['A', 'B', 'C'], ['D', 'E'], ['F'], ['G']]))
_esp, _g = agrupar_k(VERTICES_FOCOS, ARESTAS_FOCOS, 7)
_ok("agrupar_k(G_FOCOS, k=7) - cada caso é um grupo", (_esp, _grupos(_g)), (1, [[v] for v in VERTICES_FOCOS]))


_titulo("Testes Finais — Integração (Rede Didática)")
ARESTAS_MINI = [(0, 1, 50), (1, 2, 80), (0, 2, 120), (3, 4, 60), (5, 6, 150),
                (6, 7, 180), (2, 3, 400), (4, 5, 700), (0, 6, 900)]
mini = analise_casos(range(8), ARESTAS_MINI, 200, 2)
_ok("analise_casos(mini) - custo da AGM (Kruskal)", mini["custo_kruskal"], 1620)
_ok("analise_casos(mini) - focos com raio de 200 m", _grupos(mini["focos_r"]), [[0, 1, 2], [3, 4], [5, 6, 7]])
_ok("analise_casos(mini) - espaçamento com 2 grupos", mini["espacamento_k"], 700)
_ok("analise_casos(mini) - 2 grupos", _grupos(mini["grupos_k"]), [[0, 1, 2, 3, 4], [5, 6, 7]])


# ============================================================
# EXECUÇÃO NOS CASOS DE DENGUE (~7.000 casos)
# ============================================================

_titulo("Execução nos Casos de Dengue de Porto Alegre")

RAIO_AEDES = 200   # metros: alcance de voo típico do Aedes aegypti
K_EQUIPES = 8      # equipes de bloqueio disponíveis
caminho_casos = os.path.join(os.path.dirname(os.path.abspath(__file__)), "casos_dengue.txt")
if os.path.exists(caminho_casos):
    coords, arestas = carregar_casos(caminho_casos)
    print(f"  Casos carregados: |V| = {len(coords)} casos, |E| = {len(arestas)} pares de casos próximos")

    t0 = time.perf_counter()
    res = analise_casos(coords.keys(), arestas, RAIO_AEDES, K_EQUIPES)
    tempo_total = (time.perf_counter() - t0) * 1000

    if res["agm_kruskal"] or 0 < len(res["focos_r"]) < len(coords) or res["espacamento_k"] != float('inf'):
        focos_r = res["focos_r"]
        print(f"  Tempo de processamento: {tempo_total:.2f} ms")
        print()
        print(f"  {'AGM dos casos (Kruskal)':<34}: {res['custo_kruskal'] / 1000:.3f} km")
        print(f"  {f'Focos com raio de {RAIO_AEDES} m':<34}: {len(focos_r)} focos"
              f" ({sum(1 for f in focos_r if len(f) >= 10)} com 10 casos ou mais,"
              f" {res['isolados_r']} casos isolados)")
        print(f"  {f'{K_EQUIPES} grupos com espaçamento máximo':<34}: espaçamento de"
              f" {_fmt_metros(res['espacamento_k'])}")

        focos_por_raio = {}
        print()
        print("  Número de focos por raio:")
        for rr in [25, 50, 100, 150, 200, 300, 400, 500, 750, 1000]:
            focos_por_raio[rr] = agrupar_raio(coords.keys(), arestas, rr)
            print(f"    r = {rr:4d} m: {len(focos_por_raio[rr])} focos")

        grupos_por_k = {}
        print()
        print("  Espaçamento por número de grupos:")
        for kk in range(1, 21):
            grupos_por_k[kk] = agrupar_k(coords.keys(), arestas, kk)
            print(f"    k = {kk:2d}: {_fmt_metros(grupos_por_k[kk][0])}")
        print()

        _ok("custo da AGM (Kruskal)", res["custo_kruskal"], 208054)
        _ok("AGM (Kruskal) tem n - 1 arestas", len(res["agm_kruskal"]), len(coords) - 1)
        _ok(f"número de focos com raio de {RAIO_AEDES} m", len(focos_r), 125)
        _ok(f"espaçamento com {K_EQUIPES} grupos", res["espacamento_k"], 2085)
        _ok(f"os {K_EQUIPES} grupos são uma partição dos casos com o espaçamento informado",
            len(res["grupos_k"]) == K_EQUIPES
            and sorted(v for g in res["grupos_k"] for v in g) == sorted(coords)
            and _espacamento(arestas, res["grupos_k"]) == res["espacamento_k"], True)
        _ok(f"agrupar_k com k = {len(focos_r)} reproduz os focos do raio de {RAIO_AEDES} m",
            _grupos(agrupar_k(coords.keys(), arestas, len(focos_r))[1]) == _grupos(focos_r), True)

        if gerar_visualizacao_html is not None:
            arquivo_html = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resultado_lab4.html")
            gerar_visualizacao_html(
                coords=coords,
                arestas=arestas,
                agm=res["agm_kruskal"],
                focos_por_raio=focos_por_raio,
                grupos_por_k=grupos_por_k,
                r_padrao=RAIO_AEDES,
                k_padrao=K_EQUIPES,
                arquivo_saida=arquivo_html
            )
            print()
            print(f"  Visualização gerada em: {arquivo_html}")
    else:
        print()
        print("  Implemente as funções das Partes 1, 2 e 3 para executar o teste")
        print("  nos casos de dengue e gerar a visualização correspondente.")
else:
    print(f"  Arquivo {caminho_casos} não encontrado.")
print()
