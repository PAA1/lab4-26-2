"""
visualizador.py — Módulo de visualização para o Laboratório 4 (PAA 1).

Gera uma página HTML autossuficiente com Canvas 2D para visualização gráfica
dos casos de dengue, da árvore geradora mínima (Parte 1), dos focos obtidos
com raio fixo (Parte 2) e dos k grupos com espaçamento máximo (Parte 3).

Não requer bibliotecas externas.
"""

import json
import os


def _ler_extras(arquivo: str) -> dict:
    """
    Lê do arquivo dos casos as linhas usadas apenas na visualização (mapa esquemático):
        #CIDADE x1 y1 x2 y2 ...           contorno do município
        #AGUA x1 y1 ...                   Lago Guaíba e Delta do Jacuí
        #ILHA x1 y1 ...                   ilhas do delta
        #RIO x1 y1 ... | nome             rios (linha larga)
        #ARROIO x1 y1 ... | nome          arroios (linha fina; o nome é opcional)
        #PARQUE x1 y1 ... | nome          parques e reservas
        #MORRO x y rx ry graus | nome     morros, desenhados com curvas de nível
        #RUA classe x1 y1 ... | nome      ruas (classe 1 = principal, 2 = secundária)
        #PISTA x1 y1 x2 y2                pista do aeroporto
        #ROTULO x y texto                 rótulos principais
        #BAIRRO x y texto                 bairros (visíveis ao aproximar)
        #ROTULO_AGUA x y texto            nomes do lago e do delta
        #MUNICIPIO x y texto              municípios vizinhos
        #LOCAL x y texto                  pontos de referência (visíveis ao aproximar)
    """
    extras = {"cidade": None, "agua": [], "ilhas": [], "rios": [], "arroios": [], "parques": [],
              "morros": [], "ruas": [], "pista": [], "rotulos": [], "bairros": [], "rotulos_agua": [],
              "municipios": [], "locais": []}
    linhas_nomeadas = {"#RIO": "rios", "#ARROIO": "arroios", "#PARQUE": "parques"}
    rotulos = {"#ROTULO": "rotulos", "#BAIRRO": "bairros", "#ROTULO_AGUA": "rotulos_agua",
               "#MUNICIPIO": "municipios", "#LOCAL": "locais"}

    def pares(nums):
        nums = list(map(float, nums))
        return [nums[i:i + 2] for i in range(0, len(nums), 2)]

    with open(arquivo, "r", encoding="utf-8") as f:
        for linha in f:
            if not linha.startswith("#") or " " not in linha:
                continue
            marcador, resto = linha.rstrip("\n").split(" ", 1)
            dados, _, nome = resto.partition(" | ")
            nums = dados.split()
            if marcador == "#CIDADE":
                extras["cidade"] = pares(nums)
            elif marcador == "#AGUA":
                extras["agua"] = pares(nums)
            elif marcador == "#ILHA":
                extras["ilhas"].append(pares(nums))
            elif marcador in linhas_nomeadas:
                extras[linhas_nomeadas[marcador]].append([pares(nums), nome])
            elif marcador == "#MORRO":
                extras["morros"].append([*map(float, nums[:5]), nome])
            elif marcador == "#RUA":
                extras["ruas"].append([int(nums[0]), pares(nums[1:]), nome])
            elif marcador == "#PISTA":
                extras["pista"] = pares(nums)
            elif marcador in rotulos:
                x, y, texto = dados.split(" ", 2)
                extras[rotulos[marcador]].append([float(x), float(y), texto])
    if extras["cidade"] is None:
        raise ValueError("linha #CIDADE não encontrada em " + arquivo)
    return extras


def gerar_visualizacao_html(
    coords: dict,
    arestas: list,
    agm: list,
    focos_por_raio: dict,
    grupos_por_k: dict,
    r_padrao: int = 200,
    k_padrao: int = 8,
    arquivo_saida: str = "resultado_lab4.html",
    titulo: str = "Laboratório 4 — Focos de Dengue em Porto Alegre"
) -> str:
    """
    Gera um arquivo HTML com visualizador Canvas 2D.

    Parâmetros:
        coords         : dict mapeando id do caso -> (x, y) em metros
        arestas        : lista de triplas (u, v, distancia_m) do grafo
        agm            : lista de triplas (u, v, distancia_m) da AGM (Parte 1)
        focos_por_raio : dict r -> lista de focos (Parte 2, agrupar_raio)
        grupos_por_k   : dict k -> (espacamento, grupos) (Parte 3, agrupar_k)
        r_padrao       : raio exibido inicialmente
        k_padrao       : número de grupos exibido inicialmente
        arquivo_saida  : nome do arquivo HTML a ser salvo
        titulo         : título exibido no cabeçalho da página
    """
    extras = _ler_extras(os.path.join(os.path.dirname(os.path.abspath(__file__)), "casos_dengue.txt"))

    ids = sorted(coords)
    indice = {v: i for i, v in enumerate(ids)}
    pts = [[round(coords[v][0], 1), round(coords[v][1], 1)] for v in ids]

    def rotulos(grupos):
        """Rótulo de cada caso = posição do seu grupo na ordem decrescente de tamanho."""
        ordem = sorted(grupos, key=len, reverse=True)
        rot = [-1] * len(ids)
        for g, grupo in enumerate(ordem):
            for v in grupo:
                if v in indice:
                    rot[indice[v]] = g
        return rot, [len(g) for g in ordem]

    def par_mais_proximo(rot):
        melhor = None
        for u, v, d in arestas:
            iu, iv = indice[u], indice[v]
            if rot[iu] != rot[iv] and (melhor is None or d < melhor[2]):
                melhor = [iu, iv, d]
        return melhor

    por_r = {}
    for r, focos in sorted(focos_por_raio.items()):
        rot, tam = rotulos(focos)
        por_r[str(r)] = {"rot": rot, "tam": tam}

    por_k = {}
    for k, (esp, grupos) in sorted(grupos_por_k.items()):
        rot, tam = rotulos(grupos)
        por_k[str(k)] = {
            "esp": None if esp == float('inf') else esp,
            "rot": rot,
            "tam": tam,
            "par": par_mais_proximo(rot),
        }

    r_vals = sorted(focos_por_raio)
    k_vals = sorted(grupos_por_k)
    r_idx = r_vals.index(r_padrao) if r_padrao in r_vals else 0
    k_padrao = k_padrao if k_padrao in k_vals else (k_vals[0] if k_vals else 1)
    agm_idx = [[indice[u], indice[v], d] for u, v, d in agm]
    custo_agm = sum(d for *_, d in agm)

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8">
  <title>{titulo}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background-color: #0f172a;
      color: #f1f5f9;
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow: hidden;
    }}
    header {{
      background: #1e293b;
      border-bottom: 1px solid #334155;
      padding: 12px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 12px;
    }}
    h1 {{ font-size: 1.1rem; font-weight: 600; color: #38bdf8; }}
    .subtitle {{ font-size: 0.8rem; color: #94a3b8; margin-top: 2px; }}
    .stats-bar {{ display: flex; gap: 10px; flex-wrap: wrap; }}
    .stat-chip {{
      background: #0f172a;
      border: 1px solid #334155;
      border-radius: 4px;
      padding: 4px 10px;
      font-size: 0.8rem;
    }}
    .stat-label {{ color: #94a3b8; margin-right: 4px; }}
    .stat-val {{ color: #f8fafc; font-weight: 600; font-variant-numeric: tabular-nums; }}
    .main-container {{ display: flex; flex: 1; overflow: hidden; }}
    .toolbar {{
      background: #1e293b;
      border-right: 1px solid #334155;
      width: 300px;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 16px;
      overflow-y: auto;
    }}
    .toolbar-section {{ display: flex; flex-direction: column; gap: 8px; }}
    .toolbar-title {{
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #94a3b8;
      font-weight: 700;
    }}
    .btn-group {{ display: flex; flex-direction: column; gap: 6px; }}
    button {{
      background: #334155;
      color: #f1f5f9;
      border: 1px solid #475569;
      border-radius: 4px;
      padding: 8px 12px;
      font-size: 0.85rem;
      font-weight: 500;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: all 0.15s ease;
      text-align: left;
    }}
    button:hover {{ background: #475569; border-color: #64748b; }}
    button.active {{ background: #0284c7; border-color: #38bdf8; color: #ffffff; }}
    .swatch {{ width: 14px; height: 10px; border-radius: 2px; flex-shrink: 0; }}
    .legend {{
      display: flex;
      flex-direction: column;
      gap: 6px;
      background: #0f172a;
      border: 1px solid #334155;
      border-radius: 4px;
      padding: 10px;
      font-size: 0.78rem;
    }}
    .legend-item {{ display: flex; align-items: center; gap: 8px; }}
    .legend-line {{ width: 18px; height: 3px; border-radius: 2px; flex-shrink: 0; }}
    .legend-dot {{ width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }}
    .slider-row {{ display: flex; align-items: center; gap: 10px; font-size: 0.85rem; }}
    input[type=range] {{ flex: 1; accent-color: #22d3ee; }}
    .hint {{ font-size: 0.78rem; color: #94a3b8; line-height: 1.4; }}
    .tab-wrap {{ max-height: 230px; overflow-y: auto; }}
    table.tab {{ width: 100%; border-collapse: collapse; font-size: 0.78rem; font-variant-numeric: tabular-nums; }}
    table.tab td, table.tab th {{ padding: 3px 6px; border-bottom: 1px solid #334155; text-align: right; }}
    table.tab th {{ color: #94a3b8; font-weight: 600; position: sticky; top: 0; background: #1e293b; }}
    table.tab tr.sel td {{ color: #22d3ee; font-weight: 700; }}
    table.tab tr {{ cursor: pointer; }}
    .oculto {{ display: none !important; }}
    .canvas-wrapper {{
      flex: 1;
      position: relative;
      background: #e7e5e4;
      overflow: hidden;
    }}
    canvas {{ position: absolute; inset: 0; cursor: grab; }}
    canvas.arrastando {{ cursor: grabbing; }}
    .coord-tip {{
      position: absolute;
      bottom: 12px;
      right: 12px;
      background: rgba(15, 23, 42, 0.92);
      border: 1px solid #334155;
      border-radius: 4px;
      padding: 4px 10px;
      font-size: 0.75rem;
      color: #94a3b8;
      font-family: monospace;
      pointer-events: none;
      max-width: calc(100% - 24px);
    }}
    .zoom-tip {{
      position: absolute;
      top: 12px;
      right: 12px;
      font-size: 0.75rem;
      color: #94a3b8;
      background: rgba(15, 23, 42, 0.8);
      border: 1px solid #334155;
      border-radius: 4px;
      padding: 4px 10px;
      pointer-events: none;
    }}
  </style>
</head>
<body>
  <header>
    <div>
      <h1>{titulo}</h1>
      <div class="subtitle">Projeto e Análise de Algoritmos I — Instituto de Informática — UFRGS · dados sintéticos</div>
    </div>
    <div class="stats-bar">
      <div class="stat-chip"><span class="stat-label">Casos (|V|):</span><span class="stat-val">{len(ids)}</span></div>
      <div class="stat-chip"><span class="stat-label">Pares próximos (|E|):</span><span class="stat-val">{len(arestas)}</span></div>
      <div class="stat-chip"><span class="stat-label">AGM:</span><span class="stat-val">{custo_agm / 1000:.2f} km</span></div>
      <div class="stat-chip"><span class="stat-label" id="chipRLabel">Focos (r):</span><span class="stat-val" id="chipR">—</span></div>
      <div class="stat-chip"><span class="stat-label" id="chipKLabel">Espaçamento (k):</span><span class="stat-val" id="chipK">—</span></div>
    </div>
  </header>

  <div class="main-container">
    <aside class="toolbar">
      <div class="toolbar-section">
        <div class="toolbar-title">Modos de visualização</div>
        <div class="btn-group">
          <button id="btn-raio" class="active" onclick="setMode('raio')">
            <span class="swatch" style="background:linear-gradient(90deg,#2563eb,#dc2626,#16a34a)"></span>Focos com raio r (Parte 2)
          </button>
          <button id="btn-k" onclick="setMode('k')">
            <span class="swatch" style="background:linear-gradient(90deg,#9333ea,#ea580c)"></span>k grupos com espaçamento máximo (Parte 3)
          </button>
          <button id="btn-agm" onclick="setMode('agm')">
            <span class="swatch" style="background:#a8a29e"></span>Árvore geradora mínima (Parte 1)
          </button>
          <button id="btn-casos" onclick="setMode('casos')">
            <span class="swatch" style="background:#78716c"></span>Somente os casos
          </button>
        </div>
      </div>

      <div class="toolbar-section" id="secRaio">
        <div class="toolbar-title">Raio de ligação (r)</div>
        <div class="slider-row">
          <input type="range" id="rSlider" min="0" max="{len(r_vals) - 1}" step="1" value="{r_idx}" oninput="setR(this.value)">
          <span id="rVal" style="min-width:4.5em; text-align:right; font-weight:600;"></span>
        </div>
        <div class="tab-wrap"><table class="tab" id="tabR"></table></div>
      </div>

      <div class="toolbar-section oculto" id="secK">
        <div class="toolbar-title">Número de grupos (k)</div>
        <div class="slider-row">
          <input type="range" id="kSlider" min="{k_vals[0] if k_vals else 1}" max="{k_vals[-1] if k_vals else 1}" step="1" value="{k_padrao}" oninput="setK(this.value)">
          <span id="kVal" style="min-width:2em; text-align:right; font-weight:600;">{k_padrao}</span>
        </div>
        <div class="tab-wrap"><table class="tab" id="tabK"></table></div>
      </div>

      <div class="toolbar-section">
        <div class="toolbar-title">Legenda</div>
        <div class="legend">
          <div class="legend-item"><div class="legend-dot" style="background:#2563eb"></div><span>Caso de dengue (cor do foco ou grupo)</span></div>
          <div class="legend-item"><div class="legend-dot" style="background:#ffffff; border:1.5px solid #57534e"></div><span>Caso isolado (foco com 1 caso)</span></div>
          <div class="legend-item"><div class="legend-line" style="background:rgba(37,99,235,0.35); height:10px; border:1px solid #2563eb"></div><span>Contorno do foco ou grupo</span></div>
          <div class="legend-item" id="legAgm"><div class="legend-line" style="background:#a8a29e"></div><span>Aresta da AGM</span></div>
          <div class="legend-item" id="legCorte"><div class="legend-line" style="background:#dc2626; height:4px"></div><span>k − 1 maiores arestas da AGM (removidas)</span></div>
          <div class="legend-item" id="legEsp"><div class="legend-line" style="background:repeating-linear-gradient(90deg,#cbd5e1 0 4px,transparent 4px 7px); height:3px"></div><span>Espaçamento: par mais próximo entre grupos</span></div>
          <div class="legend-item"><div class="legend-line" style="background:#bfdbfe; height:10px; border:1px solid #93c5fd"></div><span>Lago Guaíba e Delta do Jacuí</span></div>
          <div class="legend-item"><div class="legend-line" style="background:#60a5fa"></div><span>Rio Gravataí e arroios</span></div>
          <div class="legend-item"><div class="legend-line" style="background:#dcfce7; height:10px; border:1px solid #86efac"></div><span>Parques e reservas</span></div>
          <div class="legend-item"><div class="legend-dot" style="background:radial-gradient(circle,#a8946f 0 2px,transparent 2px 3.5px,#a8946f 3.5px 4.5px,transparent 4.5px)"></div><span>Morro (curvas de nível)</span></div>
          <div class="legend-item"><div class="legend-line" style="background:#fde3b0; height:5px; border:1px solid #e2b56b"></div><span>Avenida principal</span></div>
          <div class="legend-item"><div style="width:12px; height:12px; flex-shrink:0; background:#fff; border:1px solid #dc2626; border-radius:2px; color:#dc2626; font-size:12px; font-weight:800; line-height:10px; text-align:center">+</div><span>Hospital</span></div>
        </div>
      </div>

      <div class="toolbar-section" style="margin-top: auto;">
        <div class="toolbar-title">Instruções</div>
        <div class="hint">
          Use a roda do mouse para aproximar e arraste para mover o mapa. Clique duas vezes para
          voltar à visão inicial. Aproxime o mapa para ver bairros, nomes de ruas e pontos de referência.
          Posicione o cursor sobre um caso para ver o foco a que ele pertence.
          Os casos e o mapa são esquemáticos (dados sintéticos).
        </div>
      </div>
    </aside>

    <main class="canvas-wrapper" id="canvasWrapper">
      <canvas id="mapa"></canvas>
      <div class="zoom-tip" id="zoomTip">zoom 1.0×</div>
      <div class="coord-tip" id="coordTip">Passe o cursor sobre um caso</div>
    </main>
  </div>

  <script>
    const PTS = {json.dumps(pts, separators=(',', ':'))};
    const IDS = {json.dumps(ids, separators=(',', ':'))};
    const AGM = {json.dumps(agm_idx, separators=(',', ':'))};
    const R_VALS = {json.dumps(r_vals)};
    const POR_R = {json.dumps(por_r, separators=(',', ':'))};
    const POR_K = {json.dumps(por_k, separators=(',', ':'))};
    const MAPA = {json.dumps(extras, ensure_ascii=False, separators=(',', ':'))};
    const PALETA = ['#2563eb', '#dc2626', '#16a34a', '#9333ea', '#ea580c', '#0891b2',
                    '#db2777', '#65a30d', '#7c3aed', '#ca8a04', '#0d9488', '#be123c'];

    let modo = 'raio';
    let rIdx = {r_idx};
    let kAtual = {k_padrao};
    let hover = -1;

    // AGM ordenada por peso decrescente: as k - 1 primeiras são as arestas removidas
    const AGM_DESC = [...AGM].sort((a, b) => b[2] - a[2]);

    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    const inclui = ([x, y]) => {{
      minX = Math.min(minX, x); maxX = Math.max(maxX, x);
      minY = Math.min(minY, y); maxY = Math.max(maxY, y);
    }};
    MAPA.cidade.forEach(inclui);
    PTS.forEach(inclui);
    minX -= 2500; maxX += 2500; minY -= 2600; maxY += 900;

    const canvas = document.getElementById('mapa');
    const ctx = canvas.getContext('2d');
    const wrapper = document.getElementById('canvasWrapper');
    const tip = document.getElementById('coordTip');
    let base = 1, zoom = 1, panX = 0, panY = 0, W = 0, H = 0;

    const tx = x => W / 2 + panX + (x - (minX + maxX) / 2) * base * zoom;
    const ty = y => H / 2 + panY + (y - (minY + maxY) / 2) * base * zoom;
    const s = () => base * zoom;

    function resize() {{
      const dpr = window.devicePixelRatio || 1;
      W = wrapper.clientWidth; H = wrapper.clientHeight;
      canvas.width = W * dpr; canvas.height = H * dpr;
      canvas.style.width = W + 'px'; canvas.style.height = H + 'px';
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      base = Math.min(W / (maxX - minX), H / (maxY - minY));
      render();
    }}

    function poligono(pts) {{
      ctx.beginPath();
      ctx.moveTo(tx(pts[0][0]), ty(pts[0][1]));
      for (let i = 1; i < pts.length; i++) ctx.lineTo(tx(pts[i][0]), ty(pts[i][1]));
      ctx.closePath();
    }}

    // Agrupamento exibido no modo atual
    function agrupamento() {{
      if (modo === 'raio') return POR_R[String(R_VALS[rIdx])] || null;
      if (modo === 'k' || modo === 'agm') return POR_K[String(kAtual)] || null;
      return null;
    }}

    // Envoltória convexa (cadeia monótona) de cada grupo com 3 casos ou mais
    const cacheEnv = {{}};
    function envoltorias(chave, ag) {{
      if (cacheEnv[chave]) return cacheEnv[chave];
      const membros = ag.tam.map(() => []);
      ag.rot.forEach((g, i) => {{ if (g >= 0) membros[g].push(PTS[i]); }});
      const cross = (o, a, b) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
      const res = [];
      membros.forEach((m, g) => {{
        if (m.length < 3) return;
        const p = [...m].sort((a, b) => a[0] - b[0] || a[1] - b[1]);
        const inf = [], sup = [];
        for (const q of p) {{
          while (inf.length >= 2 && cross(inf[inf.length - 2], inf[inf.length - 1], q) <= 0) inf.pop();
          inf.push(q);
        }}
        for (let i = p.length - 1; i >= 0; i--) {{
          const q = p[i];
          while (sup.length >= 2 && cross(sup[sup.length - 2], sup[sup.length - 1], q) <= 0) sup.pop();
          sup.push(q);
        }}
        res.push([g, inf.slice(0, -1).concat(sup.slice(0, -1))]);
      }});
      cacheEnv[chave] = res;
      return res;
    }}

    const cor = g => PALETA[g % PALETA.length];
    const FONTE = '-apple-system, Segoe UI, Roboto, sans-serif';

    function linha(pts) {{
      ctx.beginPath();
      ctx.moveTo(tx(pts[0][0]), ty(pts[0][1]));
      for (let i = 1; i < pts.length; i++) ctx.lineTo(tx(pts[i][0]), ty(pts[i][1]));
    }}

    function centro(pts) {{
      let sx = 0, sy = 0;
      pts.forEach(([x, y]) => {{ sx += x; sy += y; }});
      return [sx / pts.length, sy / pts.length];
    }}

    // Texto com contorno (halo), para ficar legível sobre o mapa
    function rotulo(t, x, y, fonte, corTexto, halo, alinhamento = 'center') {{
      ctx.font = fonte;
      ctx.textAlign = alinhamento; ctx.textBaseline = 'middle';
      ctx.lineJoin = 'round';
      ctx.strokeStyle = halo; ctx.lineWidth = 3;
      ctx.strokeText(t, x, y);
      ctx.fillStyle = corTexto;
      ctx.fillText(t, x, y);
    }}

    // Curva de nível de um morro: elipse levemente irregular, escalada por k
    function curvaDeNivel(m, k, i) {{
      const [cx, cy, rx, ry, graus] = m;
      const a = graus * Math.PI / 180;
      ctx.beginPath();
      for (let j = 0; j <= 72; j++) {{
        const t = 2 * Math.PI * j / 72;
        const r = k * (1 + 0.09 * Math.sin(3 * t + 1.7 * i) + 0.05 * Math.sin(5 * t + 0.9 * i));
        const ex = rx * r * Math.cos(t), ey = ry * r * Math.sin(t);
        const x = cx + ex * Math.cos(a) - ey * Math.sin(a), y = cy + ex * Math.sin(a) + ey * Math.cos(a);
        if (j === 0) ctx.moveTo(tx(x), ty(y)); else ctx.lineTo(tx(x), ty(y));
      }}
      ctx.closePath();
    }}

    function desenhaMapa() {{
      const e = s();
      ctx.lineJoin = 'round'; ctx.lineCap = 'round';

      // Porto Alegre (os municípios vizinhos são o fundo do canvas)
      ctx.fillStyle = '#fafaf9';
      poligono(MAPA.cidade); ctx.fill();

      // Morros e parques
      MAPA.morros.forEach((m, i) => {{
        [1, 0.76, 0.52, 0.28].forEach(k => {{
          curvaDeNivel(m, k, i);
          ctx.fillStyle = 'rgba(168, 148, 112, 0.08)'; ctx.fill();
          ctx.strokeStyle = 'rgba(150, 128, 92, 0.38)'; ctx.lineWidth = 0.8; ctx.stroke();
        }});
      }});
      MAPA.parques.forEach(([pts]) => {{
        poligono(pts);
        ctx.fillStyle = '#dcfce7'; ctx.fill();
        ctx.strokeStyle = '#86efac'; ctx.lineWidth = 1; ctx.stroke();
      }});

      // Divisa municipal
      ctx.setLineDash([6, 4]);
      poligono(MAPA.cidade);
      ctx.strokeStyle = '#a8a29e'; ctx.lineWidth = 1.2; ctx.stroke();
      ctx.setLineDash([]);

      // Lago Guaíba, Delta do Jacuí e ilhas
      poligono(MAPA.agua);
      ctx.fillStyle = '#bfdbfe'; ctx.fill();
      ctx.strokeStyle = '#93c5fd'; ctx.lineWidth = 1.2; ctx.stroke();
      MAPA.ilhas.forEach(il => {{
        poligono(il);
        ctx.fillStyle = '#e4ead9'; ctx.fill();
        ctx.strokeStyle = '#93c5fd'; ctx.lineWidth = 1; ctx.stroke();
      }});

      // Rio Gravataí e arroios
      MAPA.rios.forEach(([pts]) => {{
        linha(pts); ctx.strokeStyle = '#bfdbfe'; ctx.lineWidth = Math.max(3, 130 * e); ctx.stroke();
      }});
      MAPA.arroios.forEach(([pts]) => {{
        linha(pts); ctx.strokeStyle = '#60a5fa'; ctx.lineWidth = Math.max(1, 14 * e); ctx.stroke();
      }});

      // Pista do aeroporto
      if (MAPA.pista.length === 2) {{
        ctx.lineCap = 'butt';
        linha(MAPA.pista); ctx.strokeStyle = '#78716c'; ctx.lineWidth = Math.max(3, 60 * e); ctx.stroke();
        ctx.setLineDash([5, 5]);
        linha(MAPA.pista); ctx.strokeStyle = '#fafaf9'; ctx.lineWidth = 1; ctx.stroke();
        ctx.setLineDash([]);
        ctx.lineCap = 'round';
      }}

      // Ruas: secundárias por baixo, principais por cima (contorno e preenchimento)
      [[2, 16, '#d6d3d1', '#ffffff', 1.6, 0.8], [1, 26, '#e2b56b', '#fde3b0', 2.8, 1.6]].forEach(
        ([classe, larg, borda, interior, minBorda, minInterior]) => {{
          MAPA.ruas.forEach(([c, pts]) => {{
            if (c !== classe) return;
            linha(pts); ctx.strokeStyle = borda; ctx.lineWidth = Math.max(minBorda, (larg + 12) * e); ctx.stroke();
          }});
          MAPA.ruas.forEach(([c, pts]) => {{
            if (c !== classe) return;
            linha(pts); ctx.strokeStyle = interior; ctx.lineWidth = Math.max(minInterior, larg * e); ctx.stroke();
          }});
        }});
    }}

    // Nome de uma via, no meio do seu trecho mais longo e alinhado com ele
    function nomeDaVia(pts, t, corTexto, halo) {{
      let melhor = -1, im = 0;
      for (let i = 0; i + 1 < pts.length; i++) {{
        const d = Math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]);
        if (d > melhor) {{ melhor = d; im = i; }}
      }}
      const [x1, y1] = pts[im], [x2, y2] = pts[im + 1];
      let ang = Math.atan2(ty(y2) - ty(y1), tx(x2) - tx(x1));
      if (ang > Math.PI / 2) ang -= Math.PI;
      else if (ang < -Math.PI / 2) ang += Math.PI;
      ctx.save();
      ctx.translate(tx((x1 + x2) / 2), ty((y1 + y2) / 2));
      ctx.rotate(ang);
      rotulo(t, 0, 0, 'italic 500 11px ' + FONTE, corTexto, halo);
      ctx.restore();
    }}

    function marcadorLocal(x, y, hospital) {{
      if (hospital) {{
        ctx.fillStyle = '#ffffff'; ctx.fillRect(x - 6, y - 6, 12, 12);
        ctx.strokeStyle = '#dc2626'; ctx.lineWidth = 1; ctx.strokeRect(x - 6, y - 6, 12, 12);
        ctx.fillStyle = '#dc2626'; ctx.fillRect(x - 1.5, y - 4, 3, 8); ctx.fillRect(x - 4, y - 1.5, 8, 3);
      }} else {{
        ctx.beginPath(); ctx.arc(x, y, 4, 0, 2 * Math.PI);
        ctx.fillStyle = '#44403c'; ctx.fill();
        ctx.strokeStyle = '#ffffff'; ctx.lineWidth = 1.5; ctx.stroke();
      }}
    }}

    // Rótulos por nível de zoom: quanto mais perto, mais detalhes
    function desenhaRotulos() {{
      const tam = Math.max(11, Math.min(20, 12 * Math.sqrt(zoom)));
      const halo = 'rgba(250, 250, 249, 0.92)';
      MAPA.municipios.forEach(([x, y, t]) =>
        rotulo(t.split('').join('\u2009'), tx(x), ty(y), '700 12px ' + FONTE, '#a8a29e', 'rgba(231, 229, 228, 0.9)'));
      MAPA.rotulos_agua.forEach(([x, y, t]) =>
        rotulo(t, tx(x), ty(y), 'italic 500 ' + (tam + 1) + 'px ' + FONTE, '#3b82f6', 'rgba(191, 219, 254, 0.9)'));
      if (zoom >= 1.3) {{
        MAPA.morros.forEach(([x, y, , , , t]) =>
          rotulo(t, tx(x), ty(y), 'italic 500 11px ' + FONTE, '#8a7350', halo));
        MAPA.parques.forEach(([pts, t]) => {{
          const [x, y] = centro(pts);
          rotulo(t, tx(x), ty(y), 'italic 500 11px ' + FONTE, '#15803d', 'rgba(220, 252, 231, 0.92)');
        }});
      }}
      if (zoom >= 2.2) {{
        MAPA.ruas.forEach(([c, pts, t]) => {{
          if (t && (c === 1 || zoom >= 3.5)) nomeDaVia(pts, t, '#78716c', halo);
        }});
        MAPA.rios.concat(MAPA.arroios).forEach(([pts, t]) => {{
          if (t) nomeDaVia(pts, t, '#2563eb', 'rgba(239, 246, 255, 0.92)');
        }});
      }}
      if (zoom >= 1.6) {{
        MAPA.bairros.forEach(([x, y, t]) =>
          rotulo(t, tx(x), ty(y), '500 11px ' + FONTE, 'rgba(87, 83, 78, 0.8)', halo));
      }}
      MAPA.rotulos.forEach(([x, y, t]) =>
        rotulo(t, tx(x), ty(y), '600 ' + tam + 'px ' + FONTE, 'rgba(68, 64, 60, 0.85)', halo));
      if (zoom >= 1.6) {{
        MAPA.locais.forEach(([x, y, t]) => {{
          const px = tx(x), py = ty(y);
          marcadorLocal(px, py, t.startsWith('Hospital'));
          rotulo(t, px + 9, py, '600 11px ' + FONTE, '#292524', halo, 'left');
        }});
      }}
    }}

    // Barra de escala e seta do norte (fixas na tela)
    function desenhaEscala() {{
      let L = 100;
      [100, 200, 500, 1000, 2000, 5000, 10000].forEach(o => {{ if (o * s() <= 150) L = o; }});
      const comp = L * s(), x0 = 18, y0 = H - 24;
      ctx.fillStyle = 'rgba(255, 255, 255, 0.85)';
      ctx.fillRect(x0 - 8, y0 - 20, comp + 16, 34);
      for (let i = 0; i < 4; i++) {{
        ctx.fillStyle = i % 2 ? '#ffffff' : '#44403c';
        ctx.fillRect(x0 + i * comp / 4, y0, comp / 4, 6);
      }}
      ctx.strokeStyle = '#44403c'; ctx.lineWidth = 1; ctx.strokeRect(x0, y0, comp, 6);
      ctx.font = '600 11px ' + FONTE; ctx.fillStyle = '#44403c'; ctx.textBaseline = 'middle';
      ctx.textAlign = 'left'; ctx.fillText('0', x0, y0 - 9);
      ctx.textAlign = 'right'; ctx.fillText(L >= 1000 ? L / 1000 + ' km' : L + ' m', x0 + comp, y0 - 9);

      const nx = 30, ny = 40;
      ctx.beginPath();
      ctx.moveTo(nx, ny - 15); ctx.lineTo(nx + 8, ny + 8); ctx.lineTo(nx, ny + 3); ctx.lineTo(nx - 8, ny + 8);
      ctx.closePath();
      ctx.fillStyle = '#44403c'; ctx.fill();
      rotulo('N', nx, ny - 24, '700 12px ' + FONTE, '#44403c', 'rgba(255, 255, 255, 0.9)');
    }}

    // Bairro (ou rótulo principal) mais próximo de um ponto, até 2,5 km
    function lugarMaisProximo([x, y]) {{
      let melhor = null, melhorD = 2500;
      MAPA.bairros.concat(MAPA.rotulos).forEach(([bx, by, t]) => {{
        const d = Math.hypot(bx - x, by - y);
        if (d < melhorD) {{ melhorD = d; melhor = t; }}
      }});
      return melhor;
    }}

    function render() {{
      ctx.clearRect(0, 0, W, H);

      desenhaMapa();
      desenhaRotulos();

      const ag = agrupamento();
      const chave = modo === 'raio' ? 'r' + R_VALS[rIdx] : 'k' + kAtual;

      // Contornos dos focos/grupos
      if (ag && modo !== 'agm') {{
        envoltorias(chave, ag).forEach(([g, env]) => {{
          poligono(env);
          ctx.fillStyle = cor(g) + '26';
          ctx.fill();
          ctx.strokeStyle = cor(g) + 'aa';
          ctx.lineWidth = 1.2;
          ctx.stroke();
        }});
      }}

      // AGM e as k - 1 maiores arestas
      if (modo === 'agm') {{
        ctx.strokeStyle = 'rgba(68, 64, 60, 0.75)';
        ctx.lineWidth = 1;
        ctx.beginPath();
        AGM.forEach(([u, v]) => {{
          ctx.moveTo(tx(PTS[u][0]), ty(PTS[u][1]));
          ctx.lineTo(tx(PTS[v][0]), ty(PTS[v][1]));
        }});
        ctx.stroke();
        ctx.strokeStyle = '#dc2626';
        ctx.lineWidth = 3;
        ctx.beginPath();
        AGM_DESC.slice(0, Math.max(0, kAtual - 1)).forEach(([u, v]) => {{
          ctx.moveTo(tx(PTS[u][0]), ty(PTS[u][1]));
          ctx.lineTo(tx(PTS[v][0]), ty(PTS[v][1]));
        }});
        ctx.stroke();
      }}

      // Casos
      const raio = Math.max(1.6, Math.min(5, 9 * s()));
      for (let i = 0; i < PTS.length; i++) {{
        const x = tx(PTS[i][0]), y = ty(PTS[i][1]);
        if (x < -10 || y < -10 || x > W + 10 || y > H + 10) continue;
        let c = '#78716c', isolado = false;
        if (ag) {{
          const g = ag.rot[i];
          isolado = ag.tam[g] === 1;
          c = cor(g);
        }}
        ctx.beginPath();
        ctx.arc(x, y, raio, 0, 2 * Math.PI);
        if (isolado && modo === 'raio') {{
          ctx.fillStyle = '#ffffff'; ctx.fill();
          ctx.strokeStyle = '#57534e'; ctx.lineWidth = 1.2; ctx.stroke();
        }} else {{
          ctx.fillStyle = c; ctx.fill();
        }}
      }}

      // Espaçamento: par de casos mais próximo entre grupos diferentes
      if (modo === 'k' && ag && ag.par) {{
        const [u, v, d] = ag.par;
        const x1 = tx(PTS[u][0]), y1 = ty(PTS[u][1]), x2 = tx(PTS[v][0]), y2 = ty(PTS[v][1]);
        ctx.strokeStyle = '#0f172a';
        ctx.lineWidth = 2.5;
        ctx.setLineDash([7, 5]);
        ctx.beginPath(); ctx.moveTo(x1, y1); ctx.lineTo(x2, y2); ctx.stroke();
        ctx.setLineDash([]);
        [[x1, y1], [x2, y2]].forEach(([x, y]) => {{
          ctx.beginPath(); ctx.arc(x, y, raio + 3, 0, 2 * Math.PI);
          ctx.strokeStyle = '#0f172a'; ctx.lineWidth = 2; ctx.stroke();
        }});
        const texto = 'espaçamento: ' + d + ' m';
        ctx.font = '600 13px -apple-system, Segoe UI, Roboto, sans-serif';
        const w = ctx.measureText(texto).width + 14;
        const lx = (x1 + x2) / 2, ly = (y1 + y2) / 2 - 18;
        ctx.fillStyle = 'rgba(15, 23, 42, 0.92)';
        ctx.fillRect(lx - w / 2, ly - 11, w, 22);
        ctx.fillStyle = '#f1f5f9';
        ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.fillText(texto, lx, ly);
      }}

      if (hover >= 0) {{
        ctx.strokeStyle = '#0f172a';
        ctx.lineWidth = 2;
        ctx.beginPath(); ctx.arc(tx(PTS[hover][0]), ty(PTS[hover][1]), raio + 4, 0, 2 * Math.PI); ctx.stroke();
      }}
      desenhaEscala();
      document.getElementById('zoomTip').textContent = 'zoom ' + zoom.toFixed(1) + '×';
    }}

    const fmt = d => d === null || d === undefined ? '—' : d + ' m';

    function atualizaPainel() {{
      const rr = R_VALS[rIdx], er = POR_R[String(rr)];
      document.getElementById('rVal').textContent = rr + ' m';
      document.getElementById('chipRLabel').textContent = 'Focos (r = ' + rr + ' m):';
      document.getElementById('chipR').textContent = er ? er.tam.length : '—';
      let html = '<tr><th>r</th><th>focos</th><th>≥ 10 casos</th><th>isolados</th></tr>';
      R_VALS.forEach((r, i) => {{
        const e = POR_R[String(r)];
        html += `<tr class="${{i === rIdx ? 'sel' : ''}}" onclick="setR(${{i}})"><td>${{r}} m</td>` +
                `<td>${{e.tam.length}}</td><td>${{e.tam.filter(t => t >= 10).length}}</td>` +
                `<td>${{e.tam.filter(t => t === 1).length}}</td></tr>`;
      }});
      document.getElementById('tabR').innerHTML = html;

      const ek = POR_K[String(kAtual)];
      document.getElementById('chipKLabel').textContent = 'Espaçamento (k = ' + kAtual + '):';
      document.getElementById('chipK').textContent = ek ? fmt(ek.esp) : '—';
      html = '<tr><th>k</th><th>espaçamento</th><th>maior grupo</th><th>menor</th></tr>';
      for (const k in POR_K) {{
        const e = POR_K[k];
        html += `<tr class="${{Number(k) === kAtual ? 'sel' : ''}}" onclick="setK(${{k}})"><td>${{k}}</td>` +
                `<td>${{fmt(e.esp)}}</td><td>${{e.tam[0]}}</td><td>${{e.tam[e.tam.length - 1]}}</td></tr>`;
      }}
      document.getElementById('tabK').innerHTML = html;
    }}

    function setMode(m) {{
      modo = m;
      ['raio', 'k', 'agm', 'casos'].forEach(id =>
        document.getElementById('btn-' + id).classList.toggle('active', id === m));
      document.getElementById('secRaio').classList.toggle('oculto', m !== 'raio');
      document.getElementById('secK').classList.toggle('oculto', m !== 'k' && m !== 'agm');
      render();
    }}

    function setR(i) {{
      rIdx = Number(i);
      document.getElementById('rSlider').value = rIdx;
      atualizaPainel();
      render();
    }}

    function setK(v) {{
      kAtual = Number(v);
      document.getElementById('kVal').textContent = kAtual;
      document.getElementById('kSlider').value = kAtual;
      atualizaPainel();
      render();
    }}

    // Zoom e arraste
    let arrasto = null;
    canvas.addEventListener('wheel', (e) => {{
      e.preventDefault();
      const rect = canvas.getBoundingClientRect();
      const mx = e.clientX - rect.left - W / 2, my = e.clientY - rect.top - H / 2;
      const fator = Math.exp(-e.deltaY * 0.0015);
      const novo = Math.min(60, Math.max(1, zoom * fator));
      const f = novo / zoom;
      panX = mx - (mx - panX) * f;
      panY = my - (my - panY) * f;
      zoom = novo;
      render();
    }}, {{ passive: false }});
    canvas.addEventListener('mousedown', (e) => {{
      arrasto = {{ x: e.clientX, y: e.clientY, px: panX, py: panY }};
      canvas.classList.add('arrastando');
    }});
    window.addEventListener('mouseup', () => {{ arrasto = null; canvas.classList.remove('arrastando'); }});
    canvas.addEventListener('dblclick', () => {{ zoom = 1; panX = 0; panY = 0; render(); }});

    canvas.addEventListener('mousemove', (e) => {{
      if (arrasto) {{
        panX = arrasto.px + e.clientX - arrasto.x;
        panY = arrasto.py + e.clientY - arrasto.y;
        render();
        return;
      }}
      const rect = canvas.getBoundingClientRect();
      const px = e.clientX - rect.left, py = e.clientY - rect.top;
      let melhor = -1, melhorD = 8;
      for (let i = 0; i < PTS.length; i++) {{
        const d = Math.hypot(tx(PTS[i][0]) - px, ty(PTS[i][1]) - py);
        if (d < melhorD) {{ melhorD = d; melhor = i; }}
      }}
      if (melhor !== hover) {{ hover = melhor; render(); }}
      if (melhor < 0) {{ tip.textContent = 'Passe o cursor sobre um caso'; return; }}
      const er = POR_R[String(R_VALS[rIdx])], ek = POR_K[String(kAtual)];
      const lugar = lugarMaisProximo(PTS[melhor]);
      const partes = [`Caso ${{IDS[melhor]}}` + (lugar ? ` (${{lugar}})` : '')];
      if (er) {{
        const t = er.tam[er.rot[melhor]];
        partes.push(t === 1 ? `isolado com r = ${{R_VALS[rIdx]}} m` : `foco de ${{t}} casos com r = ${{R_VALS[rIdx]}} m`);
      }}
      if (ek) partes.push(`grupo ${{ek.rot[melhor] + 1}} de ${{kAtual}} (${{ek.tam[ek.rot[melhor]]}} casos)`);
      tip.textContent = partes.join(' | ');
    }});
    canvas.addEventListener('mouseleave', () => {{ hover = -1; render(); }});

    window.addEventListener('resize', resize);
    atualizaPainel();
    resize();
  </script>
</body>
</html>
"""

    with open(arquivo_saida, "w", encoding="utf-8") as f:
        f.write(html)

    return arquivo_saida
