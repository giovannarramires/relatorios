#!/usr/bin/env python3
"""
fetch_windsor.py (Alarcon — controle Meta Ads mensagens) — puxa o histórico por
campanha×mês (2025 + ano corrente) e os criativos por mês da conta CA-Alarcon
pela API REST do Windsor.ai, gravando raw_alarcon.json no MESMO formato da
puxada via Claude/MCP. Substitui a etapa headless p/ rodar na nuvem.

⚠️ A API REST NÃO filtra por account_id server-side — filtramos no código
(conta 3553771504851630). A dimensão 'month' devolve '01'..'12' e agrega por mês
no intervalo. date_from/date_to são honrados.

Depois deste fetch, o pipeline roda baixar_criativos.py (baixa thumbs) e
gerar_dash_alarcon.py — sem mudança.

Chave: WINDSOR_API_KEY (env/Secret) ou Keychain 'windsor-api-key'.
Uso: python3 fetch_windsor.py <saida/raw_alarcon.json> [gerado_em=YYYY-MM-DD]
"""
import json, os, sys, subprocess, urllib.request, urllib.parse, calendar
from datetime import date
from collections import defaultdict

BASE = "https://connectors.windsor.ai"
CONTA = "3553771504851630"   # CA-Alarcon
HIST_YEAR = 2025             # ano histórico fixo


def api_key():
    k = os.environ.get("WINDSOR_API_KEY")
    if not k:
        try:
            k = subprocess.check_output(
                ["security", "find-generic-password", "-s", "windsor-api-key",
                 "-a", "windsor", "-w"], text=True)
        except Exception:
            sys.exit("ERRO: chave da API ausente (nem WINDSOR_API_KEY nem Keychain).")
    return k.strip().split("&")[0].strip()


def num(v):
    if v is None or v == "":
        return 0
    try:
        f = float(v)
    except (TypeError, ValueError):
        return v
    return int(f) if f == int(f) else f


def fetch(key, fields, date_from, date_to, tries=3):
    """Puxa e filtra pela conta. A query de criativos (thumbnail_url) é lenta
    (~75s/mês — o Windsor resolve as URLs), então usamos timeout alto + retry."""
    ask = ["account_id"] + fields
    qs = urllib.parse.urlencode(
        {"api_key": key, "fields": ",".join(ask), "_renderer": "json",
         "date_from": date_from, "date_to": date_to}, safe=',')
    url = f"{BASE}/facebook?{qs}"
    req = urllib.request.Request(url, headers={"User-Agent": "ggd-alarcon/1.0"})
    last = None
    for _ in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                d = json.load(r)
            rows = d.get("data", d) if isinstance(d, dict) else d
            return [r for r in rows if isinstance(r, dict) and str(r.get("account_id")) == CONTA]
        except Exception as e:   # timeout/rede: tenta de novo
            last = e
    raise last


# ---- rows: [month, campaign, spend, impressions, reach, clicks, link, conv7d, connection]
F_ROWS = ["month", "campaign", "spend", "impressions", "reach", "clicks",
          "actions_link_click",
          "actions_onsite_conversion_messaging_conversation_started_7d",
          "actions_onsite_conversion_total_messaging_connection"]


def linhas_ano(key, date_from, date_to):
    out = []
    for r in fetch(key, F_ROWS, date_from, date_to):
        out.append([str(r.get("month") or ""), r.get("campaign") or "",
                    num(r.get("spend")), num(r.get("impressions")),
                    num(r.get("reach")), num(r.get("clicks")),
                    num(r.get("actions_link_click")),
                    num(r.get("actions_onsite_conversion_messaging_conversation_started_7d")),
                    num(r.get("actions_onsite_conversion_total_messaging_connection"))])
    out.sort(key=lambda x: (x[0], x[1]))
    return out


def criativos_do_mes(key, ano, mes, date_to):
    """1 query por mês (dim [ad_name, campaign]) — resposta pequena, robusto.
    Agrega por ad_name, spend>15, top 12. thumb/url/campanha da linha de maior
    gasto. date_to = último dia do mês (ou hoje, no mês corrente)."""
    F = ["ad_name", "campaign", "spend", "impressions", "clicks",
         "actions_link_click",
         "actions_onsite_conversion_messaging_conversation_started_7d",
         "thumbnail_url", "instagram_permalink_url"]
    df = f"{ano}-{mes:02d}-01"
    dt = min(date_to, f"{ano}-{mes:02d}-{calendar.monthrange(ano, mes)[1]:02d}")
    agg = defaultdict(lambda: {"spend": 0.0, "impr": 0.0, "clicks": 0.0,
                               "link": 0.0, "conv": 0.0, "_best": -1.0,
                               "campanha": "", "thumb": "", "url": ""})
    for r in fetch(key, F, df, dt):
        nome = r.get("ad_name") or ""
        if not nome:
            continue
        g = agg[nome]
        sp = float(num(r.get("spend")) or 0)
        g["spend"] += sp
        g["impr"] += float(num(r.get("impressions")) or 0)
        g["clicks"] += float(num(r.get("clicks")) or 0)
        g["link"] += float(num(r.get("actions_link_click")) or 0)
        g["conv"] += float(num(r.get("actions_onsite_conversion_messaging_conversation_started_7d")) or 0)
        if sp > g["_best"]:   # thumb/url/campanha da linha de maior gasto
            g["_best"] = sp
            g["campanha"] = r.get("campaign") or ""
            g["thumb"] = r.get("thumbnail_url") or ""
            g["url"] = r.get("instagram_permalink_url") or ""
    lst = [{"nome": nome, "campanha": g["campanha"], "spend": round(g["spend"], 2),
            "impr": int(g["impr"]), "clicks": int(g["clicks"]), "link": int(g["link"]),
            "conv": int(g["conv"]), "thumb": g["thumb"], "url": g["url"]}
           for nome, g in agg.items() if g["spend"] > 15]
    return sorted(lst, key=lambda c: c["spend"], reverse=True)[:12]


def criativos(key, ano, gerado):
    out = {}
    for mes in range(1, gerado.month + 1):
        lst = criativos_do_mes(key, ano, mes, gerado.isoformat())
        if lst:
            out[f"{ano}-{mes:02d}"] = lst
    return out


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else "raw_alarcon.json"
    gerado = date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else date.today()
    key = api_key()
    ano = gerado.year

    rows = {str(HIST_YEAR): linhas_ano(key, f"{HIST_YEAR}-01-01", f"{HIST_YEAR}-12-31")}
    if ano != HIST_YEAR:
        rows[str(ano)] = linhas_ano(key, f"{ano}-01-01", gerado.isoformat())

    raw = {
        "gerado_em": gerado.isoformat(),
        "conta": "Alarcon",
        "meta_conta": CONTA,
        "ano_atual": ano,
        "mes_atual": gerado.month,
        "rows": rows,
        "criativos_por_mes": criativos(key, ano, gerado),
        "meta_imposto_rate": 0.1383,   # ISS + IOF sobre a mídia (constante do dash)
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False, indent=1)
    ncri = sum(len(v) for v in raw["criativos_por_mes"].values())
    print(f"OK: {out_path} — gerado_em={raw['gerado_em']} "
          f"rows2025={len(rows.get('2025',[]))} rows{ano}={len(rows.get(str(ano),[]))} "
          f"meses_criativos={len(raw['criativos_por_mes'])} criativos={ncri}")


if __name__ == "__main__":
    main()
