# Laboratório Avaliado 4 — Projeto e Análise de Algoritmos I

**Tópicos:** Árvore Geradora Mínima · Algoritmo de Kruskal · Union-Find · Agrupamento com Espaçamento Máximo

---

## Contexto do Problema: Focos de Dengue em Porto Alegre

Porto Alegre enfrentou epidemias de dengue nos últimos verões. Cada caso notificado chega à Vigilância em Saúde com o endereço do paciente, e as ações de bloqueio (visitas casa a casa, eliminação de criadouros) são planejadas por **foco de transmissão**: um conjunto de casos próximos o bastante para que o mesmo mosquito tenha circulado entre eles.

O *Aedes aegypti* costuma voar até cerca de **200 m** do criadouro. Por isso, dois casos a no máximo 200 m um do outro são considerados do mesmo foco, e a relação é **transitiva**: se A está perto de B e B está perto de C, os três estão na mesma cadeia de transmissão, mesmo que A e C estejam longe.

```
     A ───150 m─── B ───180 m─── C          A e C estão a mais de 200 m,
                                             mas os três formam um único foco
```

Neste laboratório, os casos (sintéticos) estão espalhados sobre um mapa esquemático de Porto Alegre:

- cada caso é um **vértice**, com sua posição em metros;
- cada caso é ligado aos casos mais próximos, e o peso da **aresta** é a distância entre eles, em metros. O grafo é **não dirigido** e **conexo**.

A Vigilância quer responder a duas perguntas:

1. **Focos de transmissão:** quais são os focos quando dois casos a no máximo $r = 200$ m são ligados?
2. **Divisão entre as equipes:** há $k = 8$ equipes de bloqueio, e os casos devem ser divididos em $k$ grupos, um por equipe, de forma que grupos diferentes fiquem **o mais longe possível** uns dos outros. O **espaçamento** de uma divisão é a menor distância entre dois casos de grupos diferentes, e queremos a divisão com o **maior espaçamento possível**.

As duas perguntas são respondidas com a árvore geradora mínima: basta executar o **algoritmo de Kruskal e interrompê-lo** no momento certo.

---

## Instruções

1. Faça o clone deste repositório:
   ```bash
   git clone https://github.com/PAA1/lab4-26-2.git
   cd lab4-26-2
   ```

2. Abra o arquivo `lab4.py` e complete as funções indicadas com `# TODO`.

3. Em cada função a ser implementada, **preencha a linha de complexidade assintótica**:
   ```python
   # Complexidade: O( )
   ```
   Utilize $n$ para o número de vértices ($|V|$), $m$ para o número de arestas ($|E|$) e $\alpha(n)$ para o custo amortizado de `find` e `union` da classe `UnionFind` (inversa da função de Ackermann).

4. Teste sua solução executando:
   ```bash
   python3 lab4.py
   ```
   Um `✓ OK` indica que o teste passou. Um `✗ FALHOU` indica erro.

5. **Visualização dos Focos:**
   Ao implementar as funções exigidas, o script executará a solução sobre os casos de dengue (~7.000 casos e ~26.000 pares de casos próximos) e gerará o arquivo:
   ```
   resultado_lab4.html
   ```
   Abra este arquivo em um navegador. Há três modos:
   - **Focos com raio $r$:** use o controle de $r$ para ver como os focos se formam e se fundem;
   - **$k$ grupos com espaçamento máximo:** use o controle de $k$ e observe o par de casos mais próximo entre grupos diferentes, que define o espaçamento;
   - **Árvore geradora mínima:** as $k-1$ maiores arestas da AGM aparecem em vermelho. Compare com o modo anterior.

   Use a roda do mouse para aproximar o mapa e passe o cursor sobre um caso para ver a que foco ele pertence.

6. Ao terminar, **entregue o arquivo `lab4.py`** pela tarefa correspondente no Moodle.

---

## Visão Geral das Partes

| Parte | Função | Descrição |
|-------|--------|-----------|
| 1 | `kruskal` | **A implementar.** Algoritmo de Kruskal utilizando a classe `UnionFind` fornecida, como na Aula 21. |
| 2 | `agrupar_raio` | **A implementar.** Focos de transmissão: casos ligados por cadeias de distâncias de no máximo $r$. |
| 3 | `agrupar_k` | **A implementar.** Divisão dos casos em $k$ grupos com espaçamento máximo. |
| Aux | `UnionFind` | *Já fornecida.* Estrutura Union-Find da Aula 21, com compressão de caminho e união por rank. |
| Aux | `carregar_casos` | *Já fornecida.* Lê o arquivo dos casos: posições (para a visualização) e lista de arestas. |
| Aux | `analise_casos` | *Já fornecida.* Integra as funções implementadas. |

Os grafos são dados por uma lista de vértices e uma **lista de arestas** `(u, v, peso)`.

---

## Dicas de Implementação

- **A classe `UnionFind`.** Ela é fornecida pronta e é usada nas três partes (`kruskal`, `agrupar_raio` e `agrupar_k`):
  ```python
  uf = UnionFind(vertices)     # cada vértice começa em seu próprio conjunto
  uf.union(u, v)               # une os conjuntos de u e v; True se eram diferentes
  uf.find(u) == uf.find(v)     # u e v estão no mesmo conjunto?
  uf.componentes               # número de conjuntos disjuntos
  ```
  Criar a estrutura custa $O(n)$, e cada `find` ou `union` custa $O(\alpha(n))$ amortizado. A documentação da classe, no código, explica esses custos.

- **Parte 1: Kruskal.** Ordene as arestas por peso com `sorted(arestas, key=lambda a: a[2])`. Uma aresta entra na árvore quando `union` retorna `True`. Com `componentes == 1`, a árvore está completa.

- **Parte 2: `agrupar_raio`.** Uma aresta com distância de no máximo $r$ une os focos de suas extremidades. Pense se é necessário ordenar as arestas para isso e o que isso muda na complexidade.

- **Parte 3: cuidado com o espaçamento.** Em `agrupar_k`, interrompa o Kruskal quando `componentes == k`. O espaçamento **não** é a próxima aresta da lista ordenada, e sim a próxima aresta **que liga dois grupos diferentes**. No grafo `G_FOCOS`, com $k = 3$:

  | aresta | peso | ação | grupos |
  |---|---|---|---|
  | A-B | 1 | une | 6 |
  | D-E | 2 | une | 5 |
  | B-C | 3 | une | 4 |
  | A-C | 4 | descarta (mesmo grupo) | 4 |
  | E-F | 5 | une | **3 → para** |
  | D-F | 6 | **interna** a `{D, E, F}` | 3 |
  | C-F | 9 | **liga dois grupos** | espaçamento = 9 |

- **Parte 3: por que dá certo?** O Kruskal sempre junta os dois grupos mais próximos. Seja $d$ o espaçamento obtido e considere qualquer outra divisão em $k$ grupos. Ela separa dois casos $p$ e $q$ que o Kruskal colocou juntos. O caminho entre $p$ e $q$ dentro do grupo do Kruskal só usa arestas de peso no máximo $d$, porque todas foram processadas antes da interrupção. Alguma dessas arestas liga dois grupos da outra divisão, então o espaçamento dela é no máximo $d$.

  Equivalentemente, os $k$ grupos são as componentes que sobram ao **remover as $k-1$ maiores arestas da AGM**. É o que o modo "Árvore geradora mínima" da visualização mostra.

---

## Observações

- Não utilize bibliotecas externas (como `networkx` ou `numpy`). Utilize apenas a biblioteca padrão do Python.
- Não altere as assinaturas das funções nem os blocos de teste.
- As justificativas de complexidade devem ser expressas em termos de $n$ (vértices), $m$ (arestas) e $\alpha(n)$.
- Os casos de dengue e o mapa de Porto Alegre são **sintéticos e esquemáticos**, gerados apenas para este laboratório.
