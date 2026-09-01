#!/usr/bin/env python3
"""
gerar_dash_giacomo.py — le raw_giacomo.json e escreve index.html.

Dash da 1a campanha do Dr. Giacomo Trojan: RECONHECIMENTO / topo de funil.
Todo o layout e a leitura dos numeros moram aqui; o fetch so entrega dado cru.

Le  : raw_giacomo.json (mesma pasta)
Grava: index.html      (mesma pasta)  -> relatorios.giogrowthdigital.com.br/giacomo/
"""
import json, os, sys
from datetime import date, datetime

AQUI = os.path.dirname(os.path.abspath(__file__))
MESES = ["jan", "fev", "mar", "abr", "mai", "jun",
         "jul", "ago", "set", "out", "nov", "dez"]

# Status do Meta -> (rotulo pt-BR, cor)
STATUS = {
    "ACTIVE": ("Ativo", "ok"),
    "PAUSED": ("Pausado", "off"),
    "PENDING_REVIEW": ("Em análise", "wait"),
    "IN_PROCESS": ("Processando", "wait"),
    "PENDING_BILLING_INFO": ("Falta pagamento", "bad"),
    "DISAPPROVED": ("Reprovado", "bad"),
    "WITH_ISSUES": ("Com problema", "bad"),
    "CAMPAIGN_PAUSED": ("Campanha pausada", "off"),
    "ADSET_PAUSED": ("Conjunto pausado", "off"),
    "ARCHIVED": ("Arquivado", "off"),
    "DELETED": ("Excluído", "off"),
}
OTIMIZACAO = {
    "REACH": "Alcance (pessoas únicas)",
    "IMPRESSIONS": "Impressões",
    "AD_RECALL_LIFT": "Lembrança do anúncio",
    "THRUPLAY": "ThruPlay",
    "LINK_CLICKS": "Cliques no link",
    "CONVERSATIONS": "Conversas",
}
OBJETIVO = {
    "OUTCOME_AWARENESS": "Reconhecimento",
    "OUTCOME_ENGAGEMENT": "Engajamento",
    "OUTCOME_TRAFFIC": "Tráfego",
    "OUTCOME_LEADS": "Cadastros",
    "OUTCOME_SALES": "Vendas",
}


# ---------- formatacao pt-BR ----------
def br(v, casas=0):
    if v is None or v == "":
        return "—"
    s = f"{float(v):,.{casas}f}"
    return s.replace(",", "@").replace(".", ",").replace("@", ".")


def moeda(v, casas=2):
    return "—" if v in (None, "") else "R$ " + br(v, casas)


def pct(v, casas=1):
    return "—" if v in (None, "") else br(v, casas) + "%"


def data_br(iso):
    try:
        d = date.fromisoformat(iso[:10])
        return f"{d.day:02d}/{d.month:02d}"
    except Exception:
        return iso


def esc(t):
    return (str(t or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def div(a, b):
    a, b = float(a or 0), float(b or 0)
    return a / b if b else 0


# ---------- leitura ----------
def soma(dias, campo):
    return sum(float(d.get(campo) or 0) for d in dias)


def semaforo_freq(f):
    """Frequencia e o freio da campanha de alcance: quando sobe, o dinheiro
    para de comprar gente nova e passa a repetir para quem ja viu."""
    if not f:
        return ("", "", "")
    if f < 1.8:
        return ("ok", "Saudável", "ainda comprando gente nova")
    if f < 2.6:
        return ("wait", "Atenção", "começando a repetir para a mesma gente")
    return ("bad", "Saturado", "trocar criativo ou ampliar o público")


# ---------- blocos de HTML ----------
def bloco_status(est):
    linhas = []
    camps = est.get("campanhas", [])
    conjs = est.get("conjuntos", [])
    ads = est.get("anuncios", [])
    for c in camps:
        rot, cor = STATUS.get(c["status"], (c["status"], "off"))
        linhas.append(f'''<div class="st-row">
          <span class="st-tipo">Campanha</span>
          <span class="st-nome">{esc(c["nome"])}</span>
          <span class="st-meta">{OBJETIVO.get(c["objetivo"], c["objetivo"])}</span>
          <span class="pill {cor}">{rot}</span></div>''')
        for s in [x for x in conjs if x.get("campanha_id") == c["id"]]:
            rot, cor = STATUS.get(s["status"], (s["status"], "off"))
            av = "Advantage+ ligado" if s.get("advantage") == 1 else "segmentação manual"
            linhas.append(f'''<div class="st-row filho">
              <span class="st-tipo">Conjunto</span>
              <span class="st-nome">{esc(s["nome"])}</span>
              <span class="st-meta">{esc(s["local"])} · {esc(s["genero"])} {esc(s["idade"])} ·
                 {moeda(s["verba_dia"])}/dia · otimiza por
                 <b>{OTIMIZACAO.get(s["otimizacao"], s["otimizacao"])}</b> · {av}</span>
              <span class="pill {cor}">{rot}</span></div>''')
            for a in [x for x in ads if x.get("conjunto_id") == s["id"]]:
                rot, cor = STATUS.get(a["status"], (a["status"], "off"))
                linhas.append(f'''<div class="st-row neto">
                  <span class="st-tipo">Anúncio</span>
                  <span class="st-nome">{esc(a["nome"])}</span>
                  <span class="st-meta"></span>
                  <span class="pill {cor}">{rot}</span></div>''')
    return "\n".join(linhas) or '<div class="vazio">Nenhuma campanha na conta ainda.</div>'


def bloco_criativos(est, por_ad):
    """Card do criativo: capa grande clicavel que abre o video no Instagram."""
    metricas = {a.get("ad_id"): a for a in por_ad}
    cards = []
    for ad_id, c in est.get("criativos", {}).items():
        m = metricas.get(ad_id, {})
        alc = m.get("alcance", 0)
        thumb = c.get("thumb") or ""
        dur = c.get("duracao") or 0
        capa = (f'<img src="{esc(thumb)}" alt="{esc(c["nome"])}" loading="lazy">'
                if thumb else '<div class="sem-capa">sem prévia</div>')
        link = c.get("instagram") or c.get("facebook") or ""
        # mp4 no repo (quando o video e da nossa BM) -> abre inline; senao, IG
        if c.get("mp4"):
            midia = (f'<video class="cri-video" controls preload="none" '
                     f'poster="{esc(thumb)}"><source src="{esc(c["mp4"])}" '
                     f'type="video/mp4"></video>')
        elif link:
            midia = (f'<a class="cri-capa" href="{esc(link)}" target="_blank" '
                     f'rel="noopener">{capa}<span class="play">▶</span>'
                     f'<span class="ver">ver o vídeo ↗</span></a>')
        else:
            midia = f'<div class="cri-capa">{capa}</div>'

        rot, cor = STATUS.get(c.get("status", ""), (c.get("status", ""), "off"))
        links = []
        if c.get("instagram"):
            links.append(f'<a href="{esc(c["instagram"])}" target="_blank" rel="noopener">Instagram ↗</a>')
        if c.get("facebook"):
            links.append(f'<a href="{esc(c["facebook"])}" target="_blank" rel="noopener">Facebook ↗</a>')
        links.append(f'<a href="https://adsmanager.facebook.com/adsmanager/manage/ads?act={est.get("_conta","")}&selected_ad_ids={ad_id}" target="_blank" rel="noopener">Gerenciador ↗</a>')

        ret = div(m.get("v_100", 0), m.get("v_play3s", 0)) * 100
        cards.append(f'''<div class="cri-card">
          {midia}
          <div class="cri-info">
            <div class="cri-topo">
              <div class="cri-nome">{esc(c["nome"])}</div>
              <span class="pill {cor}">{rot}</span>
            </div>
            <div class="cri-sub">{esc(c.get("tipo","")) or "—"}{f" · {br(dur,0)}s" if dur else ""}</div>
            <div class="cri-nums">
              <div><span>{br(alc)}</span>pessoas alcançadas</div>
              <div><span>{br(m.get("v_play3s",0))}</span>viram 3s</div>
              <div><span>{br(m.get("v_thruplay",0))}</span>ThruPlay</div>
              <div><span>{pct(ret) if m.get("v_play3s") else "—"}</span>foram até o fim</div>
              <div><span>{moeda(m.get("gasto",0))}</span>investido</div>
              <div><span>{moeda(m.get("cpm",0))}</span>CPM</div>
            </div>
            <div class="cri-links">{" · ".join(links)}</div>
          </div></div>''')
    return "\n".join(cards) or '<div class="vazio">Nenhum criativo no ar ainda.</div>'


def barras_retencao(t):
    """Curva de retencao do video: quanto sobra em cada marco."""
    base = float(t.get("v_play3s") or 0)
    if not base:
        return '<div class="vazio">Ainda sem reproduções — o vídeo aparece aqui assim que a campanha começar a entregar.</div>'
    marcos = [("3s", t.get("v_play3s", 0)), ("25%", t.get("v_25", 0)),
              ("50%", t.get("v_50", 0)), ("75%", t.get("v_75", 0)),
              ("100%", t.get("v_100", 0))]
    out = []
    for rot, v in marcos:
        p = div(v, base) * 100
        out.append(f'''<div class="ret-linha">
          <span class="ret-rot">{rot}</span>
          <div class="ret-trilho"><div class="ret-barra" style="width:{max(p,1.2):.1f}%"></div></div>
          <span class="ret-val">{br(v)}<em>{pct(p,0)}</em></span></div>''')
    return "\n".join(out)


def grafico_dias(dias):
    """Barras = pessoas alcancadas por dia; linha = frequencia acumulada."""
    if not dias:
        return '<div class="vazio">O gráfico começa no primeiro dia de entrega.</div>'
    L, A, pad = 1180, 260, 42
    largura = L - pad * 2
    passo = largura / max(len(dias), 1)
    maxa = max([float(d.get("alcance") or 0) for d in dias] + [1])
    barras, rotulos, pts = [], [], []
    acum_imp = acum_alc = 0
    maxf = 1
    freqs = []
    for d in dias:
        acum_imp += float(d.get("impressoes") or 0)
        acum_alc += float(d.get("alcance") or 0)
        f = div(acum_imp, acum_alc)
        freqs.append(f)
        maxf = max(maxf, f)
    for i, d in enumerate(dias):
        v = float(d.get("alcance") or 0)
        h = (v / maxa) * (A - 70)
        x = pad + i * passo + passo * .18
        w = passo * .64
        y = A - 34 - h
        barras.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="4" fill="url(#g)"/>')
        barras.append(f'<text x="{x + w/2:.1f}" y="{y - 6:.1f}" class="gv">{br(v)}</text>')
        rotulos.append(f'<text x="{x + w/2:.1f}" y="{A - 14}" class="gx">{data_br(d.get("data",""))}</text>')
        pts.append(f'{pad + i*passo + passo*.5:.1f},{A - 34 - (freqs[i]/maxf)*(A-70):.1f}')
    linha = (f'<polyline points="{" ".join(pts)}" fill="none" stroke="#d4a24c" '
             f'stroke-width="2.5" stroke-linecap="round"/>') if len(pts) > 1 else ""
    bolinhas = "".join(f'<circle cx="{p.split(",")[0]}" cy="{p.split(",")[1]}" r="3.5" fill="#d4a24c"/>' for p in pts)
    return f'''<svg viewBox="0 0 {L} {A}" class="graf" preserveAspectRatio="xMidYMid meet">
      <defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="#2f6f8f"/><stop offset="100%" stop-color="#123c5a"/>
      </linearGradient></defs>
      {"".join(barras)}{linha}{bolinhas}{"".join(rotulos)}</svg>
      <div class="leg"><span class="ldot bar"></span>pessoas alcançadas no dia
      <span class="ldot lin"></span>frequência acumulada (máx. {br(maxf,2)}×)</div>'''


def tabela_anuncios(por_ad):
    if not por_ad:
        return '<div class="vazio">A tabela por anúncio aparece no primeiro dia de entrega.</div>'
    linhas = []
    for a in por_ad:
        linhas.append(f'''<tr>
          <td class="l">{esc(a.get("anuncio"))}<em>{esc(a.get("conjunto"))}</em></td>
          <td>{br(a.get("alcance"))}</td><td>{br(a.get("impressoes"))}</td>
          <td>{br(a.get("frequencia"),2)}×</td><td>{moeda(a.get("cpm"))}</td>
          <td>{br(a.get("v_thruplay"))}</td>
          <td>{pct(div(a.get("v_100",0), a.get("v_play3s",0))*100)}</td>
          <td>{br(a.get("conversas"))}</td><td class="d">{moeda(a.get("gasto"))}</td>
        </tr>''')
    return f'''<div class="tab-wrap"><table>
      <thead><tr><th class="l">Anúncio</th><th>Alcance</th><th>Impressões</th>
      <th>Freq.</th><th>CPM</th><th>ThruPlay</th><th>Até o fim</th>
      <th>Conversas</th><th class="d">Investido</th></tr></thead>
      <tbody>{"".join(linhas)}</tbody></table></div>'''


# ---------- pagina ----------
def gerar(raw):
    dias = raw.get("dias") or []
    por_ad = raw.get("por_anuncio") or []
    est = raw.get("estrutura") or {}
    est["_conta"] = raw.get("meta_conta", "")
    tx = float(raw.get("meta_imposto_rate") or 0)

    # Totais: preferimos o total da conta (o Meta dedupe o alcance); se ainda
    # nao existe, somamos os dias (soma de alcance diario NAO e alcance unico —
    # por isso o rotulo muda para "alcance somado" nesse caso).
    t = raw.get("total") or {}
    tem_dado = bool(t) and float(t.get("impressoes") or 0) > 0
    if not tem_dado and dias:
        t = {k: soma(dias, k) for k in
             ("gasto", "impressoes", "alcance", "cliques", "cliques_link",
              "v_play3s", "v_thruplay", "v_25", "v_50", "v_75", "v_100",
              "conversas", "engajamento_post", "reacoes", "comentarios",
              "compartilhamentos", "salvos", "visitas_perfil")}
        tem_dado = float(t.get("impressoes") or 0) > 0

    gasto = float(t.get("gasto") or 0)
    imposto = gasto * tx
    alcance = float(t.get("alcance") or 0)
    impressoes = float(t.get("impressoes") or 0)
    freq = float(t.get("frequencia") or 0) or div(impressoes, alcance)
    cpm = float(t.get("cpm") or 0) or div(gasto, impressoes) * 1000
    cpp = float(t.get("cpp") or 0) or div(gasto, alcance) * 1000
    conversas = float(t.get("conversas") or 0)
    fcor, frot, fdica = semaforo_freq(freq)

    hoje = date.fromisoformat(raw["gerado_em"])
    aviso = ""
    if not tem_dado:
        pend = [a for a in est.get("anuncios", []) if a["status"] == "PENDING_REVIEW"]
        motivo = ("o anúncio está <b>em análise</b> pelo Meta — assim que for aprovado "
                  "a entrega começa e este painel se preenche sozinho."
                  if pend else
                  "a campanha ainda não teve entrega no período.")
        aviso = f'''<div class="aviso"><span>⏳</span><div>
          <b>Aguardando a primeira entrega.</b> Os números ainda estão zerados porque {motivo}
          A estrutura abaixo já é a que está no ar de verdade, lida da conta agora.</div></div>'''

    eng = (float(t.get("reacoes") or 0) + float(t.get("comentarios") or 0) +
           float(t.get("compartilhamentos") or 0) + float(t.get("salvos") or 0))

    return f'''<!DOCTYPE html>
<html lang="pt-BR"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Dr. Giácomo Trojan — Reconhecimento</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{--bg:#eef2f7;--surface:#fff;--border:#e3e8ef;--text:#101a26;--text-2:#4a5768;--text-3:#93a1b3;
--shadow-sm:0 1px 3px rgba(0,0,0,.07),0 1px 2px rgba(0,0,0,.04);--shadow:0 4px 12px rgba(0,0,0,.08);
--shadow-lg:0 10px 30px rgba(0,0,0,.13);--radius:14px;
--c1:#123c5a;--c2:#2f8f8a;--c3:#d4a24c;--ink:#08192b;
--ok:#0f8a5f;--wait:#b07d10;--bad:#c0392b;--off:#8593a5}}
body{{font-family:'Inter',-apple-system,sans-serif;background:var(--bg);color:var(--text);min-height:100vh}}
.brandstrip{{background:var(--ink);color:#fff;text-align:center;font-family:'Space Grotesk',sans-serif;
font-weight:700;letter-spacing:5px;font-size:12px;padding:7px 0;text-transform:uppercase}}
.brandstrip span{{color:var(--c3)}}
.header{{background:linear-gradient(135deg,var(--c1) 0%,var(--c2) 135%);padding:0 32px;min-height:78px;
display:flex;align-items:center;justify-content:space-between;gap:14px;position:sticky;top:0;z-index:100;
box-shadow:0 4px 20px rgba(0,0,0,.22);flex-wrap:wrap}}
.header-left{{display:flex;align-items:center;gap:14px;padding:12px 0}}
.logo{{width:50px;height:50px;border-radius:13px;background:var(--ink);display:flex;align-items:center;
justify-content:center;font-family:'Space Grotesk',sans-serif;border:2px solid rgba(255,255,255,.35);flex-shrink:0}}
.logo b{{color:#fff;font-size:21px}}
.header-title{{font-family:'Space Grotesk',sans-serif;font-size:22px;font-weight:700;color:#fff;letter-spacing:.6px}}
.header-sub{{font-size:11.5px;color:rgba(255,255,255,.86);letter-spacing:.3px;margin-top:2px}}
.header-badge{{background:rgba(255,255,255,.18);border:1px solid rgba(255,255,255,.32);color:#fff;
padding:7px 15px;border-radius:20px;font-size:12.5px;font-weight:700;white-space:nowrap;margin:12px 0}}
.container{{max-width:1280px;margin:0 auto;padding:20px 32px 44px}}
.watermark{{font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:11px;letter-spacing:3px;
color:var(--text-3);text-align:right;text-transform:uppercase;opacity:.6;margin:2px 0 14px}}
.watermark span{{color:var(--c2)}}
.aviso{{display:flex;gap:14px;align-items:flex-start;background:#fff8e6;border:1px solid #f0dca8;
border-left:5px solid var(--c3);border-radius:12px;padding:15px 18px;margin-bottom:18px;
font-size:13.5px;line-height:1.55;color:#5d4a1c}}
.aviso span{{font-size:20px;line-height:1}}
.hero{{background:linear-gradient(135deg,var(--ink) 0%,var(--c1) 92%,var(--c2) 165%);border-radius:18px;
padding:22px 26px;color:#fff;box-shadow:var(--shadow-lg);position:relative;overflow:hidden}}
.hero::after{{content:'🦷';position:absolute;right:22px;bottom:-18px;font-size:100px;opacity:.07}}
.hero-label{{font-family:'Space Grotesk',sans-serif;letter-spacing:2px;text-transform:uppercase;
font-size:12px;color:var(--c3);font-weight:700;margin-bottom:14px}}
.hero-label span{{color:rgba(255,255,255,.6);font-weight:600;letter-spacing:.3px;text-transform:none}}
.hero-row{{display:flex;flex-wrap:wrap;gap:12px;align-items:stretch}}
.hero-box{{flex:1;min-width:158px;background:rgba(255,255,255,.07);border:1px solid rgba(255,255,255,.14);
border-radius:12px;padding:15px 18px}}
.hero-box.total{{background:rgba(212,162,76,.2);border-color:rgba(212,162,76,.5)}}
.hb-l{{font-size:11px;text-transform:uppercase;letter-spacing:.5px;color:rgba(255,255,255,.72);font-weight:700;margin-bottom:7px}}
.hb-v{{font-size:25px;font-weight:900;letter-spacing:-.5px}}
.hb-s{{font-size:11px;color:rgba(255,255,255,.6);margin-top:5px}}
.hero-op{{align-self:center;font-size:24px;font-weight:300;color:rgba(255,255,255,.45)}}
.section-header{{display:flex;align-items:baseline;gap:10px;margin:30px 0 14px;flex-wrap:wrap}}
.section-tag{{width:4px;height:20px;background:var(--c2);border-radius:3px;align-self:center}}
.section-title{{font-family:'Space Grotesk',sans-serif;font-size:16px;font-weight:700;letter-spacing:.5px;text-transform:uppercase}}
.section-hint{{font-size:11.5px;color:var(--text-3)}}
.section-hint b{{color:var(--c2)}}
.kpi-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px}}
.kpi{{background:var(--surface);border-radius:var(--radius);padding:18px 20px;box-shadow:var(--shadow-sm);
border-top:3px solid var(--c2)}}
.kpi.destaque{{border-top-color:var(--c3)}}
.kpi-l{{font-size:11px;text-transform:uppercase;letter-spacing:.6px;color:var(--text-3);font-weight:700}}
.kpi-v{{font-family:'Space Grotesk',sans-serif;font-size:29px;font-weight:700;letter-spacing:-.6px;margin:8px 0 4px}}
.kpi-s{{font-size:11.5px;color:var(--text-2);line-height:1.45}}
.grid-2{{display:grid;grid-template-columns:1.05fr .95fr;gap:16px;align-items:start}}
.card{{background:var(--surface);border-radius:var(--radius);padding:20px 22px;box-shadow:var(--shadow-sm)}}
.card h3{{font-family:'Space Grotesk',sans-serif;font-size:13.5px;text-transform:uppercase;letter-spacing:.8px;
color:var(--text-2);margin-bottom:4px}}
.card .cap{{font-size:11.5px;color:var(--text-3);margin-bottom:16px}}
.ret-linha{{display:flex;align-items:center;gap:12px;margin-bottom:11px}}
.ret-rot{{width:40px;font-size:12px;font-weight:700;color:var(--text-2);flex-shrink:0}}
.ret-trilho{{flex:1;height:16px;background:#eef2f7;border-radius:8px;overflow:hidden}}
.ret-barra{{height:100%;border-radius:8px;background:linear-gradient(90deg,var(--c1),var(--c2))}}
.ret-val{{width:104px;text-align:right;font-size:12.5px;font-weight:700;flex-shrink:0}}
.ret-val em{{display:block;font-style:normal;font-size:11px;font-weight:600;color:var(--text-3)}}
.mini{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}}
.mini div{{background:#f6f8fb;border-radius:10px;padding:12px 14px}}
.mini b{{display:block;font-family:'Space Grotesk',sans-serif;font-size:20px;font-weight:700;margin-bottom:2px}}
.mini span{{font-size:11.5px;color:var(--text-2)}}
.st-row{{display:grid;grid-template-columns:76px minmax(150px,1.1fr) 2fr auto;gap:12px;align-items:center;
padding:11px 0;border-bottom:1px solid var(--border);font-size:13px}}
.st-row:last-child{{border-bottom:0}}
.st-row.filho{{padding-left:18px}} .st-row.neto{{padding-left:36px}}
.st-tipo{{font-size:10.5px;text-transform:uppercase;letter-spacing:.6px;color:var(--text-3);font-weight:700}}
.st-nome{{font-weight:700;word-break:break-word}}
.st-meta{{font-size:11.5px;color:var(--text-2);line-height:1.5}}
.pill{{padding:4px 11px;border-radius:20px;font-size:11px;font-weight:700;white-space:nowrap;color:#fff}}
.pill.ok{{background:var(--ok)}} .pill.wait{{background:var(--wait)}}
.pill.bad{{background:var(--bad)}} .pill.off{{background:var(--off)}}
.cri-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}}
.cri-card{{background:var(--surface);border-radius:var(--radius);box-shadow:var(--shadow-sm);overflow:hidden;
display:flex;flex-direction:column}}
.cri-capa{{position:relative;display:block;background:#08192b;aspect-ratio:9/16;max-height:420px;overflow:hidden}}
.cri-capa img{{width:100%;height:100%;object-fit:cover;display:block;transition:transform .3s}}
.cri-capa:hover img{{transform:scale(1.04)}}
.cri-capa .play{{position:absolute;inset:0;margin:auto;width:62px;height:62px;border-radius:50%;
background:rgba(255,255,255,.92);color:var(--c1);font-size:23px;display:flex;align-items:center;
justify-content:center;padding-left:5px;box-shadow:0 6px 20px rgba(0,0,0,.3)}}
.cri-capa .ver{{position:absolute;left:0;right:0;bottom:0;background:linear-gradient(transparent,rgba(8,25,43,.9));
color:#fff;font-size:12.5px;font-weight:700;padding:26px 14px 12px;text-align:center}}
.cri-video{{width:100%;aspect-ratio:9/16;max-height:420px;background:#000;display:block}}
.sem-capa{{display:flex;align-items:center;justify-content:center;height:100%;color:var(--text-3);font-size:12px}}
.cri-info{{padding:15px 17px 16px;display:flex;flex-direction:column;gap:9px}}
.cri-topo{{display:flex;gap:10px;align-items:flex-start;justify-content:space-between}}
.cri-nome{{font-weight:700;font-size:13px;line-height:1.35;word-break:break-word}}
.cri-sub{{font-size:11px;color:var(--text-3);text-transform:uppercase;letter-spacing:.5px;margin-top:-6px}}
.cri-nums{{display:grid;grid-template-columns:repeat(3,1fr);gap:9px}}
.cri-nums div{{background:#f6f8fb;border-radius:9px;padding:9px 10px;font-size:10.5px;color:var(--text-2);line-height:1.3}}
.cri-nums span{{display:block;font-family:'Space Grotesk',sans-serif;font-size:15px;font-weight:700;color:var(--text)}}
.cri-links{{font-size:11.5px;color:var(--text-3)}}
.cri-links a{{color:var(--c2);font-weight:700;text-decoration:none}}
.cri-links a:hover{{text-decoration:underline}}
.graf{{width:100%;height:auto}}
.gv{{font-size:11px;font-weight:700;fill:var(--text-2);text-anchor:middle;font-family:'Inter',sans-serif}}
.gx{{font-size:11px;fill:var(--text-3);text-anchor:middle;font-family:'Inter',sans-serif}}
.leg{{display:flex;align-items:center;gap:8px;font-size:11.5px;color:var(--text-3);margin-top:6px;flex-wrap:wrap}}
.ldot{{width:11px;height:11px;border-radius:3px;display:inline-block}}
.ldot.bar{{background:var(--c1)}} .ldot.lin{{background:var(--c3);border-radius:50%;margin-left:12px}}
.tab-wrap{{overflow-x:auto}}
table{{width:100%;border-collapse:collapse;font-size:12.5px;min-width:760px}}
th{{background:#f6f8fb;padding:11px 12px;text-align:right;font-size:10.5px;text-transform:uppercase;
letter-spacing:.5px;color:var(--text-3);font-weight:700;white-space:nowrap}}
th.l,td.l{{text-align:left}} th.d,td.d{{text-align:right;font-weight:700}}
td{{padding:11px 12px;text-align:right;border-bottom:1px solid var(--border)}}
td.l em{{display:block;font-style:normal;font-size:11px;color:var(--text-3);margin-top:2px}}
tbody tr:hover{{background:#f9fbfd}}
.vazio{{padding:26px;text-align:center;color:var(--text-3);font-size:13px;background:#f6f8fb;border-radius:12px;line-height:1.6}}
.rodape{{margin-top:34px;padding-top:18px;border-top:1px solid var(--border);font-size:11.5px;
color:var(--text-3);display:flex;justify-content:space-between;gap:14px;flex-wrap:wrap}}
@media(max-width:980px){{.kpi-grid{{grid-template-columns:repeat(2,1fr)}}.grid-2{{grid-template-columns:1fr}}
.hero-op{{display:none}}}}
@media(max-width:620px){{.container{{padding:16px 16px 34px}}.header{{padding:0 18px}}
.kpi-grid{{grid-template-columns:1fr}}.st-row{{grid-template-columns:1fr auto;gap:6px}}
.st-tipo{{grid-column:1/-1}}.st-meta{{grid-column:1/-1}}}}
</style></head><body>
<div class="brandstrip">GIO <span>GROWTH</span> DIGITAL</div>
<div class="header">
  <div class="header-left">
    <div class="logo"><b>GG</b></div>
    <div><div class="header-title">DR. GIÁCOMO TROJAN</div>
    <div class="header-sub">Reconhecimento · topo de funil · Meta Ads</div></div>
  </div>
  <div class="header-badge">no ar desde {data_br(raw["inicio"])} · dados até {hoje.day:02d}/{MESES[hoje.month-1]}</div>
</div>
<div class="container">
<div class="watermark">GIO <span>GROWTH</span> DIGITAL</div>
{aviso}

<div class="hero">
  <div class="hero-label">Investimento <span>— o que saiu do caixa no período</span></div>
  <div class="hero-row">
    <div class="hero-box"><div class="hb-l">Mídia</div><div class="hb-v">{moeda(gasto)}</div>
      <div class="hb-s">o que foi para o leilão do Meta</div></div>
    <div class="hero-op">+</div>
    <div class="hero-box"><div class="hb-l">Imposto ({pct(tx*100,2)})</div><div class="hb-v">{moeda(imposto)}</div>
      <div class="hb-s">ISS + IOF sobre a mídia</div></div>
    <div class="hero-op">=</div>
    <div class="hero-box total"><div class="hb-l">Total pago</div><div class="hb-v">{moeda(gasto + imposto)}</div>
      <div class="hb-s">{br(len(dias))} dia(s) com entrega</div></div>
  </div>
</div>

<div class="section-header"><span class="section-tag"></span>
  <span class="section-title">Alcance — o que a campanha existe para fazer</span>
  <span class="section-hint">campanha de reconhecimento se mede por <b>quanta gente nova viu</b>, e por quanto custou cada mil</span></div>
<div class="kpi-grid">
  <div class="kpi destaque"><div class="kpi-l">Pessoas alcançadas</div>
    <div class="kpi-v">{br(alcance)}</div>
    <div class="kpi-s">pessoas diferentes que viram o Dr. pelo menos uma vez</div></div>
  <div class="kpi"><div class="kpi-l">Impressões</div>
    <div class="kpi-v">{br(impressoes)}</div>
    <div class="kpi-s">quantas vezes o anúncio apareceu na tela</div></div>
  <div class="kpi"><div class="kpi-l">Frequência</div>
    <div class="kpi-v">{br(freq,2) if freq else "—"}{"×" if freq else ""}
      {f'<span class="pill {fcor}" style="font-size:10px;vertical-align:middle;margin-left:6px">{frot}</span>' if freq else ""}</div>
    <div class="kpi-s">{fdica or "quantas vezes a mesma pessoa viu"}</div></div>
  <div class="kpi"><div class="kpi-l">Custo por mil alcançadas</div>
    <div class="kpi-v">{moeda(cpp)}</div>
    <div class="kpi-s">CPM (por mil impressões): {moeda(cpm)}</div></div>
</div>

<div class="section-header"><span class="section-tag"></span>
  <span class="section-title">O vídeo que está rodando</span>
  <span class="section-hint">clique na capa para <b>ver o criativo</b> — e veja até onde as pessoas assistem</span></div>
<div class="grid-2">
  <div class="cri-grid">{bloco_criativos(est, por_ad)}</div>
  <div class="card">
    <h3>Retenção do vídeo</h3>
    <div class="cap">de cada 100 que começaram a ver, quantas continuaram</div>
    {barras_retencao(t)}
    <div class="mini" style="margin-top:18px">
      <div><b>{br(t.get("v_thruplay",0))}</b><span>ThruPlay (15s ou até o fim)</span></div>
      <div><b>{br(t.get("v_tempo_medio",0),1)}s</b><span>tempo médio assistido</span></div>
      <div><b>{moeda(div(gasto, t.get("v_thruplay",0)) if t.get("v_thruplay") else 0)}</b><span>custo por ThruPlay</span></div>
      <div><b>{pct(div(t.get("v_play3s",0), impressoes)*100) if impressoes else "—"}</b><span>das impressões viraram 3s de vídeo</span></div>
    </div>
  </div>
</div>

<div class="section-header"><span class="section-tag"></span>
  <span class="section-title">Reconhecimento virou ação?</span>
  <span class="section-hint">topo de funil não vende — mas deixa rastro: <b>engajamento, perfil e conversa</b></span></div>
<div class="kpi-grid">
  <div class="kpi"><div class="kpi-l">Engajamento com o post</div>
    <div class="kpi-v">{br(eng)}</div>
    <div class="kpi-s">{br(t.get("reacoes",0))} reações · {br(t.get("comentarios",0))} comentários ·
      {br(t.get("compartilhamentos",0))} compart. · {br(t.get("salvos",0))} salvos</div></div>
  <div class="kpi"><div class="kpi-l">Visitas ao perfil</div>
    <div class="kpi-v">{br(t.get("visitas_perfil",0))}</div>
    <div class="kpi-s">gente que foi conhecer o @drgiacomogtrojan</div></div>
  <div class="kpi"><div class="kpi-l">Cliques / CTR</div>
    <div class="kpi-v">{br(t.get("cliques",0))}</div>
    <div class="kpi-s">CTR {pct(t.get("ctr") or div(t.get("cliques",0), impressoes)*100)} ·
      {br(t.get("cliques_link",0))} no link</div></div>
  <div class="kpi destaque"><div class="kpi-l">Conversas iniciadas</div>
    <div class="kpi-v">{br(conversas)}</div>
    <div class="kpi-s">{f"custo por conversa {moeda(div(gasto, conversas))}" if conversas else "a campanha de alcance não otimiza por conversa — o que vier aqui é bônus"}</div></div>
</div>

<div class="section-header"><span class="section-tag"></span>
  <span class="section-title">Dia a dia</span>
  <span class="section-hint">barra = gente nova por dia · linha = <b>frequência acumulada</b> (o freio da campanha)</span></div>
<div class="card">{grafico_dias(dias)}</div>

<div class="section-header"><span class="section-tag"></span>
  <span class="section-title">Desempenho por anúncio</span></div>
<div class="card">{tabela_anuncios(por_ad)}</div>

<div class="section-header"><span class="section-tag"></span>
  <span class="section-title">Como a campanha está montada</span>
  <span class="section-hint">lido da conta <b>agora</b> — status, público e verba de verdade</span></div>
<div class="card">{bloco_status(est)}</div>

<div class="rodape">
  <span>Conta Meta {raw.get("meta_conta","")} · atualizado em {hoje.strftime("%d/%m/%Y")}</span>
  <span>Gio Growth Digital</span>
</div>
</div></body></html>'''


def main():
    entrada = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, "raw_giacomo.json")
    saida = sys.argv[2] if len(sys.argv) > 2 else os.path.join(AQUI, "index.html")
    raw = json.load(open(entrada, encoding="utf-8"))
    # trava anti-dado-velho: nao publica raw de outro dia (padrao das automacoes)
    if os.environ.get("EXIGIR_HOJE") == "1" and raw.get("gerado_em") != date.today().isoformat():
        sys.exit(f"ABORTADO: raw e de {raw.get('gerado_em')}, nao de hoje.")
    html = gerar(raw)
    open(saida, "w", encoding="utf-8").write(html)
    print(f"OK: {saida} ({len(html)//1024} KB) — dias={len(raw.get('dias') or [])} "
          f"anuncios={len(raw.get('por_anuncio') or [])}")


if __name__ == "__main__":
    main()
