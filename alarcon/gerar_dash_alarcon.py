#!/usr/bin/env python3
# ============================================================
# Gerador do Dash de Controle — Meta Ads · ALARCON
# Le raw_alarcon.json e escreve index.html (pagina unica,
# navegacao por mes clicavel + comparativo mes a mes + YoY).
# Uso: python3 gerar_dash_alarcon.py <raw_alarcon.json> <dir_saida>
# ============================================================
import json, sys, os, re

MESES_PT = ["","Janeiro","Fevereiro","Março","Abril","Maio","Junho","Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
MES_ABREV = ["","Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]

def tipo_de(nome):
    n = (nome or "").upper()
    if "MENSAGEM" in n: return "msg"
    if "SEGUIDOR" in n or "TRAFEGO" in n: return "seg"
    if "ENGAJ" in n: return "eng"
    if "ALCANCE" in n or "DISTRIBUICAO" in n or "VVIEW" in n or "VIEW" in n: return "alc"
    return "out"

def limpa_nome(nome):
    nome = nome or ""
    # "[GGD][MENSAGEM][DIRECT][ONETIME]" -> "Mensagem · Direct · Onetime"
    if nome.startswith("[GGD]") and nome.rstrip().endswith("]"):
        tags = [t for t in re.findall(r"\[([^\]]+)\]", nome) if t != "GGD"]
        return " · ".join(t.replace("_", " ").title() for t in tags)
    limpo = nome.replace("[GGD]", "").strip()
    return (limpo[:42] + "…") if len(limpo) > 43 else limpo

def num_or_zero(v):
    return v or 0

def build_meses(rows_por_ano, ano_atual, mes_atual):
    """rows_por_ano: dict '2025' -> [ [month, campaign, spend, impr, reach, clicks, link, conv, conex], ... ]"""
    meses = []
    for ano_str in sorted(rows_por_ano):
        ano = int(ano_str)
        por_mes = {}
        for r in rows_por_ano[ano_str]:
            mm, nome, spend, impr, reach, clicks, link, conv, conex = r[:9]
            m = int(mm)
            por_mes.setdefault(m, []).append({
                "nome": limpa_nome(nome), "raw": nome, "tipo": tipo_de(nome),
                "spend": round(spend or 0, 2), "impr": num_or_zero(impr), "reach": num_or_zero(reach),
                "clicks": num_or_zero(clicks), "link": num_or_zero(link),
                "conv": num_or_zero(conv), "conex": num_or_zero(conex),
            })
        for m in sorted(por_mes):
            atual = (ano == ano_atual and m == mes_atual)
            meses.append({
                "id": f"{ano}-{m:02d}", "ano": ano, "mes": m,
                "label": f"{MESES_PT[m]} {ano}", "abrev": MES_ABREV[m], "atual": atual,
                "campanhas": sorted(por_mes[m], key=lambda c: -c["spend"]),
            })
    return meses

def main():
    raw_path = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/Library/GGD/relatorios/alarcon/raw_alarcon.json")
    out_dir  = sys.argv[2] if len(sys.argv) > 2 else os.path.expanduser("~/Library/GGD/relatorios/alarcon")
    doc = json.load(open(raw_path, encoding="utf-8"))

    if "meses" in doc:                       # formato ja processado (compat)
        meses = doc["meses"]
    else:                                    # formato cru do Windsor
        meses = build_meses(doc["rows"], doc.get("ano_atual"), doc.get("mes_atual"))

    # criativos por mes (mapa id->lista). Aceita tambem lista unica antiga.
    cpm = doc.get("criativos_por_mes")
    if cpm is None:
        cpm = {doc.get("mes_criativos", ""): doc.get("criativos", [])} if doc.get("criativos") else {}
    for mid, lst in cpm.items():
        for c in lst:
            if not c.get("tipo"):
                c["tipo"] = tipo_de(c.get("campanha") or c.get("raw") or "")

    dados_json = json.dumps(meses, ensure_ascii=False)
    criativos_json = json.dumps(cpm, ensure_ascii=False)
    gerado = doc.get("gerado_em", "")
    html = (TEMPLATE.replace("__DADOS__", dados_json)
                    .replace("__CRIATIVOS__", criativos_json)
                    .replace("__GERADO__", gerado))
    out = os.path.join(out_dir, "index.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print("OK ->", out, "| meses:", len(meses))

TEMPLATE = r"""<!DOCTYPE html>
<html lang="pt-BR">
<!--
  DASH DE CONTROLE — META ADS · ALARCON  ·  Gio Growth Digital
  Gerado automaticamente por gerar_dash_alarcon.py (dados Windsor.ai).
  Fonte: Meta Ads (CA-Alarcon 3553771504851630). NAO editar a mao.
-->
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Alarcon — Controle Meta Ads</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=Space+Grotesk:wght@500;600;700&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{--bg:#eef2f9;--surface:#fff;--border:#e2e8f0;--text:#0f172a;--text-2:#475569;--text-3:#94a3b8;
--shadow-sm:0 1px 3px rgba(0,0,0,.07),0 1px 2px rgba(0,0,0,.04);--shadow:0 4px 12px rgba(0,0,0,.08);--shadow-lg:0 10px 30px rgba(0,0,0,.12);--radius:14px;
--c1:#0d3b66;--c2:#00a6a6;--c3:#f4a259;--ink:#08192b}
body{font-family:'Inter',-apple-system,sans-serif;background:var(--bg);color:var(--text);min-height:100vh}
.brandstrip{background:var(--ink);color:#fff;text-align:center;font-family:'Space Grotesk',sans-serif;font-weight:700;letter-spacing:5px;font-size:12px;padding:7px 0;text-transform:uppercase;opacity:.97}
.brandstrip span{color:var(--c2)}
.header{background:linear-gradient(135deg,var(--c1) 0%,var(--c2) 130%);padding:0 36px;height:76px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;z-index:100;box-shadow:0 4px 20px rgba(0,0,0,.22)}
.header-left{display:flex;align-items:center;gap:15px}
.logo{width:52px;height:52px;border-radius:13px;background:var(--ink);display:flex;align-items:center;justify-content:center;font-family:'Space Grotesk',sans-serif;border:2px solid rgba(255,255,255,.35)}
.logo b{color:#fff;font-size:22px;font-weight:700}
.header-title{font-family:'Space Grotesk',sans-serif;font-size:24px;font-weight:700;color:#fff;letter-spacing:1px}
.header-sub{font-size:11px;color:rgba(255,255,255,.85);letter-spacing:.3px}
.header-badge{background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.32);color:#fff;padding:7px 16px;border-radius:20px;font-size:13px;font-weight:700;white-space:nowrap}
.container{max-width:1280px;margin:0 auto;padding:22px 36px 40px}
.watermark{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:11px;letter-spacing:3px;color:var(--text-3);text-align:right;text-transform:uppercase;opacity:.6;margin:2px 0 14px}
.watermark span{color:var(--c2)}
/* Seletor de mes */
.selector{background:var(--surface);border-radius:var(--radius);padding:16px 20px;box-shadow:var(--shadow-sm);margin-bottom:8px}
.sel-yearrow{display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin:6px 0}
.sel-yearlbl{font-family:'Space Grotesk',sans-serif;font-size:13px;font-weight:700;color:var(--text-3);width:44px;flex-shrink:0}
.mbtn{padding:8px 14px;border-radius:20px;font-size:12.5px;font-weight:700;cursor:pointer;border:1.5px solid var(--border);background:var(--surface);color:var(--text-2);transition:all .15s;user-select:none;white-space:nowrap}
.mbtn:hover{border-color:var(--c2);color:var(--c2)}
.mbtn.active{background:linear-gradient(135deg,var(--c1),var(--c2));border-color:transparent;color:#fff;box-shadow:var(--shadow)}
.mbtn.empty{opacity:.35;cursor:not-allowed}
.mbtn.empty:hover{border-color:var(--border);color:var(--text-2)}
.section-header{display:flex;align-items:baseline;gap:10px;margin:28px 0 14px}
.section-tag{width:4px;height:20px;background:var(--c2);border-radius:3px;align-self:center}
.section-title{font-family:'Space Grotesk',sans-serif;font-size:16px;font-weight:700;letter-spacing:.5px;color:var(--text);text-transform:uppercase}
.section-hint{font-size:11px;color:var(--text-3)}
.section-hint b{color:var(--c2)}
/* KPIs */
.kpi-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}
.kpi{background:var(--surface);border-radius:var(--radius);padding:18px 20px;box-shadow:var(--shadow-sm);position:relative;overflow:hidden}
.kpi-bar{position:absolute;top:0;left:0;right:0;height:3px;background:var(--c2)}
.kpi.hl .kpi-bar{background:var(--c3)}
.kpi.spend .kpi-bar{background:var(--c1)}
.kpi-label{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.6px;color:var(--text-3);margin-bottom:9px}
.kpi-value{font-size:23px;font-weight:900;letter-spacing:-.6px;line-height:1;margin-bottom:9px}
.kpi-sub{font-size:11px;color:var(--text-3);line-height:1.5}
.deltas{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:7px}
.delta{display:inline-flex;align-items:center;gap:3px;font-size:10.5px;font-weight:800;padding:2px 8px;border-radius:7px}
.delta .cap{font-weight:700;opacity:.7;text-transform:uppercase;letter-spacing:.3px;font-size:9px}
.delta.up{background:#dcfce7;color:#16a34a}.delta.down{background:#fee2e2;color:#dc2626}.delta.flat{background:#f1f5f9;color:#64748b}
/* Funil */
.card{background:var(--surface);border-radius:var(--radius);padding:22px 26px;box-shadow:var(--shadow-sm);overflow-x:auto}
.funnel{display:flex;flex-direction:column;gap:9px}
.fstep{display:flex;align-items:center;gap:16px}
.fbar-wrap{flex:1;background:#f1f5f9;border-radius:10px;overflow:hidden;height:50px;position:relative}
.fbar{height:100%;border-radius:10px;display:flex;align-items:center;padding:0 16px;color:#fff;font-weight:800;font-size:16px;letter-spacing:-.3px;transition:width .7s cubic-bezier(.2,.8,.2,1);min-width:110px;white-space:nowrap}
.fstep-meta{width:220px;flex-shrink:0}
.fstep-label{font-size:13px;font-weight:800;color:var(--text)}
.fstep-rate{font-size:11px;color:var(--text-3);margin-top:2px}
.fstep-rate b{color:var(--c2);font-weight:800}
@media(max-width:720px){.fstep{flex-direction:column;align-items:stretch;gap:4px}.fstep-meta{width:auto}}
.card-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;flex-wrap:wrap;gap:14px}
.chart-title{font-size:15px;font-weight:800;color:var(--text)}.chart-subtitle{font-size:12px;color:var(--text-3);margin-top:2px}
.metric-pills{display:flex;gap:6px;flex-wrap:wrap}
.mpill{padding:7px 14px;border-radius:20px;font-size:12px;font-weight:700;cursor:pointer;border:1.5px solid var(--border);background:var(--surface);color:var(--text-2);transition:all .16s;user-select:none;white-space:nowrap}
.mpill:hover{border-color:var(--c2);color:var(--c2)}.mpill.active{background:var(--c2);border-color:var(--c2);color:#fff}
.chart-area{height:300px;position:relative}
table{width:100%;border-collapse:collapse;min-width:720px}
th{text-align:right;font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.5px;color:var(--text-3);padding:10px 12px;border-bottom:2px solid var(--border);white-space:nowrap}
th:first-child{text-align:left}
td{text-align:right;font-size:12.5px;padding:12px;border-bottom:1px solid #f1f5f9;color:var(--text-2);white-space:nowrap}
td:first-child{text-align:left;font-weight:700;color:var(--text);white-space:normal}
tr:last-child td{border-bottom:none}
tbody tr:hover td{background:#f0fdfa}
.tag{display:inline-block;font-size:9px;font-weight:800;padding:2px 7px;border-radius:6px;margin-left:4px;vertical-align:middle}
.tag.msg{background:#cffafe;color:#0e7490}.tag.alc{background:#fef3c7;color:#b45309}.tag.seg{background:#e0e7ff;color:#4338ca}.tag.eng{background:#fce7f3;color:#be185d}.tag.out{background:#f1f5f9;color:#64748b}
tfoot td{font-weight:900;font-size:12.5px;color:var(--text)!important;background:#f0fbfb!important;border-top:2px solid var(--border)!important;border-bottom:none!important}
/* Criativos */
.cr-group-title{font-size:12px;font-weight:800;color:var(--text-2);text-transform:uppercase;letter-spacing:.5px;margin:6px 0 12px;display:flex;align-items:center;gap:8px}
.cr-group-title .tag{margin-left:0}
.cr-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(215px,1fr));gap:16px;margin-bottom:8px}
.cr-card{background:var(--surface);border-radius:var(--radius);box-shadow:var(--shadow-sm);border:1.5px solid var(--border);overflow:hidden;display:flex;flex-direction:column;text-decoration:none;transition:all .2s}
.cr-card:hover{box-shadow:var(--shadow-lg);transform:translateY(-3px);border-color:var(--c2)}
.cr-thumb{width:100%;aspect-ratio:1/1;object-fit:cover;background:#f1f5f9;display:block}
.cr-thumb.ph{display:flex;align-items:center;justify-content:center;color:var(--text-3);font-size:34px}
.cr-rank{position:absolute;top:10px;left:10px;background:var(--c3);color:#fff;font-family:'Space Grotesk';font-weight:700;font-size:12px;width:24px;height:24px;border-radius:8px;display:flex;align-items:center;justify-content:center;box-shadow:var(--shadow)}
.cr-imgwrap{position:relative}
.cr-body{padding:12px 14px 10px}
.cr-name{font-size:12.5px;font-weight:800;color:var(--text);letter-spacing:-.2px;line-height:1.25;word-break:break-word}
.cr-metrics{display:flex;gap:0;margin-top:11px;border-top:1px solid #f1f5f9;padding-top:10px}
.cr-m{flex:1;text-align:center}
.cr-m + .cr-m{border-left:1px solid #f1f5f9}
.cr-m-v{font-size:15px;font-weight:900;color:var(--text);letter-spacing:-.3px}
.cr-m-v.orange{color:var(--c3)}.cr-m-v.teal{color:var(--c2)}
.cr-m-l{font-size:8.5px;font-weight:700;text-transform:uppercase;letter-spacing:.4px;color:var(--text-3);margin-top:3px}
.cr-link{display:flex;align-items:center;justify-content:center;gap:6px;padding:9px;background:#f0fbfb;color:var(--c1);font-size:11.5px;font-weight:800;transition:all .16s}
.cr-card:hover .cr-link{background:var(--c2);color:#fff}
.cr-note{font-size:12.5px;color:var(--text-3);padding:6px 2px}
.foot{text-align:center;font-size:11px;color:var(--text-3);margin-top:36px;line-height:1.8;padding-top:20px;border-top:1px solid var(--border)}
.foot b{color:var(--text-2)}
@media(max-width:1000px){.kpi-grid{grid-template-columns:1fr 1fr}}
@media(max-width:640px){.container{padding:16px}.header{padding:0 16px;height:64px}.header-title{font-size:19px}.kpi-grid{grid-template-columns:1fr 1fr}.sel-yearlbl{width:100%}}
</style>
</head>
<body>
<div class="brandstrip">ALAR<span>CON</span> &nbsp;·&nbsp; DASH DE CONTROLE META ADS &nbsp;·&nbsp; GESTÃO <span>GGD</span></div>
<header class="header">
  <div class="header-left">
    <div class="logo"><b>A</b></div>
    <div>
      <div class="header-title">ALARCON</div>
      <div class="header-sub">Controle Meta Ads · histórico 2025–2026 · comparativo mensal</div>
    </div>
  </div>
  <div class="header-badge" id="periodo">—</div>
</header>

<div class="container">
  <div class="watermark">GIO <span>GROWTH</span> DIGITAL · MONITORAMENTO CONTÍNUO</div>

  <!-- SELETOR DE MES -->
  <div class="selector" id="selector"></div>

  <!-- KPIS -->
  <div class="section-header">
    <span class="section-tag"></span>
    <span class="section-title">Métricas-base</span>
    <span class="section-hint">vs <b>mês anterior</b> e vs <b>mesmo mês do ano anterior</b> (YoY)</span>
  </div>
  <div class="kpi-grid" id="kpis-1"></div>
  <div class="kpi-grid" id="kpis-2" style="margin-top:16px"></div>

  <!-- FUNIL -->
  <div class="section-header">
    <span class="section-tag"></span>
    <span class="section-title">Funil de conversão</span>
    <span class="section-hint" id="funil-hint">—</span>
  </div>
  <div class="card"><div class="funnel" id="funnel"></div></div>

  <!-- HISTORICO -->
  <div class="section-header">
    <span class="section-tag"></span>
    <span class="section-title">Histórico mês a mês</span>
    <span class="section-hint">clique nas métricas · o mês selecionado fica destacado</span>
  </div>
  <div class="card">
    <div class="card-header">
      <div><div class="chart-title">Evolução 2025 → 2026</div><div class="chart-subtitle">todos os meses · Meta Ads</div></div>
      <div class="metric-pills" id="pills"></div>
    </div>
    <div class="chart-area"><canvas id="chart"></canvas></div>
  </div>

  <!-- CAMPANHAS -->
  <div class="section-header">
    <span class="section-tag"></span>
    <span class="section-title">Campanhas do mês</span>
    <span class="section-hint" id="camp-hint">—</span>
  </div>
  <div class="card">
    <table>
      <thead><tr>
        <th>Campanha</th><th>Invest.</th><th>Impr.</th><th>CPM</th><th>Cliques</th><th>CPC</th><th>CTR</th><th>Conversas</th><th>Custo/Conv.</th>
      </tr></thead>
      <tbody id="camp-body"></tbody>
      <tfoot id="camp-foot"></tfoot>
    </table>
  </div>

  <!-- CRIATIVOS -->
  <div class="section-header">
    <span class="section-tag"></span>
    <span class="section-title">Criativos do mês</span>
    <span class="section-hint" id="cr-hint">—</span>
  </div>
  <div class="card"><div id="criativos"></div></div>

  <div class="foot">
    Fonte: <b>Meta Ads</b> · conta CA-Alarcon (3553771504851630) via <b>Windsor.ai</b><br>
    <b>Conversas iniciadas</b> = novas conversas no Direct atribuídas aos anúncios (janela 7 dias) — objetivo principal da conta.<br>
    Valores de <b>investimento em mídia</b> (sem impostos). Atualização automática semanal · <b>Gio Growth Digital</b> · dados de <span id="upd">—</span>
  </div>
</div>

<script>
const MESES = __DADOS__;
const CRIATIVOS_POR_MES = __CRIATIVOS__;
const GERADO = "__GERADO__";
document.getElementById('upd').textContent = GERADO.split('-').reverse().join('/');

/* ---------- helpers ---------- */
const brl = v => "R$ "+(v||0).toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2});
const num = v => (v||0).toLocaleString('pt-BR');
const pct = v => (v||0).toLocaleString('pt-BR',{minimumFractionDigits:2,maximumFractionDigits:2})+"%";
const MES_ABREV = ["","Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"];
const ANOS = [...new Set(MESES.map(m=>m.ano))].sort();

function totais(m){
  const t={spend:0,impr:0,reach:0,clicks:0,link:0,conv:0,conex:0};
  m.campanhas.forEach(c=>{for(const k in t) t[k]+=(c[k]||0);});
  t.cpm = t.impr? t.spend/t.impr*1000 : 0;
  t.cpc = t.clicks? t.spend/t.clicks : 0;
  t.cpcLink = t.link? t.spend/t.link : 0;
  t.ctr = t.impr? t.clicks/t.impr*100 : 0;
  t.custoConv = t.conv? t.spend/t.conv : 0;
  return t;
}
const byId = {}; MESES.forEach(m=> byId[m.id]=m);
let sel = MESES[MESES.length-1].id;   // comeca no mes mais recente

/* ---------- seletor ---------- */
function renderSelector(){
  const sc = document.getElementById('selector');
  sc.innerHTML = ANOS.map(ano=>{
    const btns = [];
    for(let m=1;m<=12;m++){
      const id = ano+"-"+String(m).padStart(2,'0');
      const existe = byId[id];
      const cls = "mbtn"+(id===sel?" active":"")+(existe?"":" empty");
      const on = existe? `onclick="selecionar('${id}')"` : "";
      btns.push(`<div class="${cls}" ${on}>${MES_ABREV[m]}</div>`);
    }
    return `<div class="sel-yearrow"><span class="sel-yearlbl">${ano}</span>${btns.join('')}</div>`;
  }).join('');
}

/* ---------- delta ---------- */
// good: 'up' = maior e melhor (conversas); 'down' = menor e melhor (custos)
function deltaBadge(cap, atual, base, good, fmt){
  if(base==null || base===0 || atual==null) return `<span class="delta flat"><span class="cap">${cap}</span> —</span>`;
  const p = (atual-base)/base*100;
  const subiu = p>=0;
  let klass='flat';
  if(Math.abs(p)>=0.5){
    const bom = good==='up'? subiu : !subiu;
    klass = bom? 'up':'down';
  }
  const arrow = Math.abs(p)<0.5? '→' : (subiu?'▲':'▼');
  return `<span class="delta ${klass}"><span class="cap">${cap}</span> ${arrow} ${Math.abs(p).toLocaleString('pt-BR',{maximumFractionDigits:0})}%</span>`;
}

/* ---------- render principal ---------- */
function selecionar(id){ sel=id; render(); renderSelector(); }

function render(){
  const m = byId[sel];
  const t = totais(m);
  document.getElementById('periodo').textContent = m.label + (m.atual? " · parcial":"");

  // vizinhos: mes anterior (na lista) e mesmo mes ano anterior
  const idx = MESES.findIndex(x=>x.id===sel);
  const prev = idx>0? totais(MESES[idx-1]) : null;
  const prevLbl = idx>0? MESES[idx-1].abrev+"/"+String(MESES[idx-1].ano).slice(2) : "MoM";
  const yoyM = byId[(m.ano-1)+"-"+String(m.mes).padStart(2,'0')];
  const yoy = yoyM? totais(yoyM) : null;

  const kpi = (cls,label,valueHtml,cur,pv,yv,good,fmt,sub)=>`
    <div class="kpi ${cls}"><div class="kpi-bar"></div>
      <div class="kpi-label">${label}</div>
      <div class="kpi-value">${valueHtml}</div>
      <div class="deltas">${deltaBadge(prevLbl,cur,pv,good,fmt)}${deltaBadge('YoY',cur,yv,good,fmt)}</div>
      <div class="kpi-sub">${sub}</div>
    </div>`;

  document.getElementById('kpis-1').innerHTML =
    kpi('spend','Investimento',brl(t.spend), t.spend, prev&&prev.spend, yoy&&yoy.spend,'up',brl, "investimento em mídia no mês") +
    kpi('','CPM',brl(t.cpm), t.cpm, prev&&prev.cpm, yoy&&yoy.cpm,'down',brl,"custo por 1.000 impressões") +
    kpi('','CPC (todos)',brl(t.cpc), t.cpc, prev&&prev.cpc, yoy&&yoy.cpc,'down',brl,"CPC no link: "+brl(t.cpcLink)) +
    kpi('hl','Custo / Conversa',brl(t.custoConv), t.custoConv, prev&&prev.custoConv, yoy&&yoy.custoConv,'down',brl, t.conv+" conversas iniciadas");

  document.getElementById('kpis-2').innerHTML =
    kpi('','Impressões',num(t.impr), t.impr, prev&&prev.impr, yoy&&yoy.impr,'up',num,"alcance ~"+num(t.reach)+"*") +
    kpi('','CTR (todos)',pct(t.ctr), t.ctr, prev&&prev.ctr, yoy&&yoy.ctr,'up',pct,"cliques: "+num(t.clicks)) +
    kpi('','Cliques no link',num(t.link), t.link, prev&&prev.link, yoy&&yoy.link,'up',num,"de "+num(t.clicks)+" cliques totais") +
    kpi('hl','Conversas iniciadas',num(t.conv), t.conv, prev&&prev.conv, yoy&&yoy.conv,'up',num,"novas conexões: "+num(t.conex));

  // funil
  document.getElementById('funil-hint').textContent = "da impressão até a conversa no Direct · "+m.label;
  const steps=[
    {label:"Impressões",v:t.impr,color:"var(--c1)"},
    {label:"Cliques (todos)",v:t.clicks,color:"#1d6ca8"},
    {label:"Cliques no link",v:t.link,color:"var(--c2)"},
    {label:"Conversas iniciadas",v:t.conv,color:"var(--c3)"},
  ];
  const fmax=steps[0].v||1;
  document.getElementById('funnel').innerHTML = steps.map((s,i)=>{
    const w=Math.max(s.v/fmax*100,6);
    const rate = i? `<b>${(s.v/(steps[i-1].v||1)*100).toLocaleString('pt-BR',{maximumFractionDigits:1})}%</b> do passo anterior` : "topo do funil";
    return `<div class="fstep"><div class="fstep-meta"><div class="fstep-label">${s.label}</div><div class="fstep-rate">${rate}</div></div>
      <div class="fbar-wrap"><div class="fbar" style="width:${w}%;background:${s.color}">${num(s.v)}</div></div></div>`;
  }).join('');

  // campanhas
  document.getElementById('camp-hint').textContent = m.campanhas.length+" campanhas ativas · "+m.label;
  document.getElementById('camp-body').innerHTML = m.campanhas.map(c=>{
    const cpm=c.impr?c.spend/c.impr*1000:0, cpc=c.clicks?c.spend/c.clicks:0, ctr=c.impr?c.clicks/c.impr*100:0;
    return `<tr>
      <td>${c.nome}<span class="tag ${c.tipo}">${c.tipo.toUpperCase()}</span></td>
      <td>${brl(c.spend)}</td><td>${num(c.impr)}</td><td>${brl(cpm)}</td>
      <td>${num(c.clicks)}</td><td>${brl(cpc)}</td><td>${pct(ctr)}</td>
      <td>${num(c.conv)}</td><td>${c.conv?brl(c.spend/c.conv):'—'}</td></tr>`;
  }).join('');
  document.getElementById('camp-foot').innerHTML = `<tr>
    <td>TOTAL — ${m.label}</td><td>${brl(t.spend)}</td><td>${num(t.impr)}</td><td>${brl(t.cpm)}</td>
    <td>${num(t.clicks)}</td><td>${brl(t.cpc)}</td><td>${pct(t.ctr)}</td>
    <td>${num(t.conv)}</td><td>${brl(t.custoConv)}</td></tr>`;

  renderCriativos(m);
  renderChart();
}

/* ---------- criativos do mes ---------- */
function crCard(c, rank){
  const cconv = c.conv? c.spend/c.conv : 0;
  const img = c.thumb
    ? `<img class="cr-thumb" src="${c.thumb}" alt="${c.nome}" loading="lazy" referrerpolicy="no-referrer" onerror="var w=this.parentNode;this.remove();w.insertAdjacentHTML('afterbegin','<div class=&quot;cr-thumb ph&quot;>🖼️</div>')">`
    : `<div class="cr-thumb ph">🖼️</div>`;
  const link = c.url? `<div class="cr-link">▶ Ver no Instagram</div>` : "";
  return `<a class="cr-card" href="${c.url||'#'}" target="_blank" rel="noopener">
    <div class="cr-imgwrap">${img}<div class="cr-rank">${rank}</div></div>
    <div class="cr-body">
      <div class="cr-name">${c.nome}</div>
      <div class="cr-metrics">
        <div class="cr-m"><div class="cr-m-v orange">${num(c.conv)}</div><div class="cr-m-l">Conversas</div></div>
        <div class="cr-m"><div class="cr-m-v">${brl(c.spend)}</div><div class="cr-m-l">Investido</div></div>
        <div class="cr-m"><div class="cr-m-v teal">${c.conv?brl(cconv):'—'}</div><div class="cr-m-l">Custo/Conv.</div></div>
      </div>
    </div>${link}</a>`;
}
function renderCriativos(m){
  const box = document.getElementById('criativos');
  const hint = document.getElementById('cr-hint');
  const lista0 = CRIATIVOS_POR_MES[m.id] || [];
  if(!lista0.length){
    hint.textContent = "sem criativos catalogados neste mês";
    box.innerHTML = `<div class="cr-note">Os criativos (com print e link) estão catalogados a partir de 2026. Selecione um mês de 2026 para vê-los.</div>`;
    return;
  }
  hint.innerHTML = "print e link clicável · "+m.label;
  const grupos = [
    {tipo:"msg", titulo:"Mensagem · Direct", tagcls:"msg", sub:"trazem as conversas"},
    {tipo:"alc", titulo:"Alcance · Distribuição", tagcls:"alc", sub:"topo de funil / awareness"},
    {tipo:"seg", titulo:"Seguidores · Tráfego", tagcls:"seg", sub:"crescimento de perfil"},
    {tipo:"eng", titulo:"Engajamento", tagcls:"eng", sub:"engajamento"},
  ];
  let html = "";
  const usados = new Set();
  grupos.forEach(g=>{
    const lista = lista0.filter(c=>c.tipo===g.tipo).sort((a,b)=> b.conv-a.conv || b.spend-a.spend);
    if(!lista.length) return;
    lista.forEach(c=>usados.add(c));
    html += `<div class="cr-group-title"><span class="tag ${g.tagcls}">${g.tipo.toUpperCase()}</span> ${g.titulo} <span style="font-weight:600;color:var(--text-3);text-transform:none;letter-spacing:0">· ${g.sub}</span></div>`;
    html += `<div class="cr-grid">${lista.map((c,i)=>crCard(c,i+1)).join('')}</div>`;
  });
  const resto = lista0.filter(c=>!usados.has(c)).sort((a,b)=>b.spend-a.spend);
  if(resto.length){
    html += `<div class="cr-group-title">Outros criativos</div><div class="cr-grid">${resto.map((c,i)=>crCard(c,i+1)).join('')}</div>`;
  }
  box.innerHTML = html;
}

/* ---------- grafico historico ---------- */
const HMETRICS = {
  conv:{label:"Conversas iniciadas", get:t=>t.conv, fmt:num, type:'bar', color:"#f4a259"},
  spend:{label:"Investimento (R$)", get:t=>t.spend, fmt:brl, type:'bar', color:"#0d3b66"},
  custoConv:{label:"Custo por conversa", get:t=>t.custoConv, fmt:brl, type:'line', color:"#00a6a6"},
  cpm:{label:"CPM", get:t=>t.cpm, fmt:brl, type:'line', color:"#7c9cb5"},
};
let hactive="conv", chart;
function renderChart(){
  const m=HMETRICS[hactive];
  const labels=MESES.map(x=>x.abrev+"/"+String(x.ano).slice(2));
  const vals=MESES.map(x=>+m.get(totais(x)).toFixed(2));
  const cores=MESES.map(x=> x.id===sel? m.color : m.color+"66");
  const data={labels,datasets:[{label:m.label,data:vals,
    backgroundColor:m.type==='bar'?cores:m.color+"22",
    borderColor:m.color,borderWidth:m.type==='bar'?0:2.5,
    fill:m.type!=='bar',tension:.35,
    pointRadius:m.type==='bar'?0:MESES.map(x=>x.id===sel?6:3),
    pointBackgroundColor:m.color,pointBorderColor:'#fff',pointBorderWidth:2,
    borderRadius:6}]};
  const opts={responsive:true,maintainAspectRatio:false,
    plugins:{legend:{display:false},tooltip:{callbacks:{
      title:c=>MESES[c[0].dataIndex].label,
      label:c=>" "+m.fmt(c.parsed.y)}}},
    scales:{y:{beginAtZero:true,grid:{color:"#f1f5f9"},ticks:{font:{size:11},color:"#94a3b8"}},
            x:{grid:{display:false},ticks:{font:{size:10},color:"#94a3b8",maxRotation:0,autoSkip:true,maxTicksLimit:20}}}};
  if(chart){chart.destroy();}
  chart=new Chart(document.getElementById('chart'),{type:m.type,data,options:opts});
}
const pills=document.getElementById('pills');
Object.keys(HMETRICS).forEach(k=>{
  const el=document.createElement('div');
  el.className="mpill"+(k===hactive?" active":"");
  el.textContent=HMETRICS[k].label;
  el.onclick=()=>{hactive=k;[...pills.children].forEach(c=>c.classList.remove('active'));el.classList.add('active');renderChart();};
  pills.appendChild(el);
});

renderSelector();
render();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
