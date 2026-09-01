#!/usr/bin/env python3
"""
fetch_meta_giacomo.py — puxa os dados da conta CA_Giacomo_Lipo_papada direto da
Graph API do Meta e grava raw_giacomo.json.

Por que Graph API e nao Windsor: a conta 595009265656090 NAO esta liberada no
Windsor (get_data devolve "Account is not available"). Quando ela entrar la, da
pra trocar a fonte sem mexer no gerador — o raw e o contrato.

O que grava:
  estrutura        campanha/conjunto/anuncio ao vivo (status, verba, publico)
  criativos        1 por anuncio: thumb + mp4 baixados pro repo + permalink IG
  totais           acumulado da conta no periodo (nivel conta)
  dias             serie diaria (alcance, impressoes, freq, gasto, video, acoes)
  por_anuncio      acumulado por anuncio (ranking de criativo)

Token: META_ADS_TOKEN (env/Secret) ou Keychain 'meta-ads-token'.
Uso: python3 fetch_meta_giacomo.py [saida/raw_giacomo.json] [gerado_em=YYYY-MM-DD]
"""
import json, os, sys, time, subprocess, urllib.request, urllib.parse, urllib.error
from datetime import date
from collections import defaultdict

API = "https://graph.facebook.com/v21.0"
CONTA = "595009265656090"
INICIO = "2026-09-01"          # 1a campanha do cliente foi ao ar em 01/09/2026
IMPOSTO = 0.1383               # ISS + IOF sobre a midia (padrao GGD)
AQUI = os.path.dirname(os.path.abspath(__file__))
DIR_CRIATIVOS = os.path.join(AQUI, "criativos")

# Metricas de campanha de ALCANCE/reconhecimento (topo de funil)
CAMPOS_INSIGHTS = ",".join([
    "spend", "impressions", "reach", "frequency", "cpm", "cpp", "cpc",
    "clicks", "ctr", "inline_link_clicks", "inline_link_click_ctr",
    "actions", "cost_per_action_type",
    "video_play_actions", "video_thruplay_watched_actions",
    "video_p25_watched_actions", "video_p50_watched_actions",
    "video_p75_watched_actions", "video_p100_watched_actions",
    "video_avg_time_watched_actions",
])


def token():
    t = os.environ.get("META_ADS_TOKEN")
    if not t:
        try:
            t = subprocess.check_output(
                ["security", "find-generic-password", "-s", "meta-ads-token", "-w"],
                text=True)
        except Exception:
            sys.exit("ERRO: token Meta ausente (nem META_ADS_TOKEN nem Keychain).")
    return t.strip()


def get(path, params, tries=4):
    """GET na Graph API com retry em falha transitoria (429/5xx/rede)."""
    last = None
    for i in range(1, tries + 1):
        try:
            qs = urllib.parse.urlencode(params, safe="{}':,")
            req = urllib.request.Request(f"{API}/{path}?{qs}",
                                         headers={"User-Agent": "ggd-giacomo/1.0"})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            corpo = e.read().decode("utf-8", "replace")[:400]
            if e.code in (429, 500, 502, 503, 504) and i < tries:
                last = e; time.sleep(i * 5); continue
            raise RuntimeError(f"Graph API {e.code} em {path}: {corpo}")
        except Exception as e:
            last = e
            if i < tries:
                time.sleep(i * 5); continue
            raise last


def paginar(path, params):
    out, p = [], dict(params)
    p.setdefault("limit", 200)
    while True:
        d = get(path, p)
        out.extend(d.get("data", []))
        prox = (d.get("paging") or {}).get("cursors", {}).get("after")
        if not prox or not d.get("data"):
            return out
        p["after"] = prox


def n(v):
    """String da Graph -> numero (a API devolve tudo como texto)."""
    if v in (None, ""):
        return 0
    try:
        f = float(v)
    except (TypeError, ValueError):
        return 0
    return int(f) if f == int(f) else round(f, 4)


def action(lst, tipo):
    """Le um action_type de dentro de actions/video_*_actions."""
    for a in (lst or []):
        if a.get("action_type") == tipo:
            return n(a.get("value"))
    return 0


def primeiro_valor(lst):
    return n((lst or [{}])[0].get("value")) if lst else 0


def acoes_mapa(lst):
    """Guarda TODAS as acoes cruas — assim o dash mostra o que existir sem
    precisar mexer no fetch quando o Meta comecar a reportar seguidor/perfil."""
    return {a.get("action_type"): n(a.get("value")) for a in (lst or [])}


def linha(r):
    """Normaliza uma linha de insights (dia OU anuncio OU conta)."""
    ac = acoes_mapa(r.get("actions"))
    return {
        "data": r.get("date_start", ""),
        "campanha": r.get("campaign_name", ""),
        "conjunto": r.get("adset_name", ""),
        "anuncio": r.get("ad_name", ""),
        "ad_id": r.get("ad_id", ""),
        "gasto": n(r.get("spend")),
        "impressoes": n(r.get("impressions")),
        "alcance": n(r.get("reach")),
        "frequencia": n(r.get("frequency")),
        "cpm": n(r.get("cpm")),
        "cpp": n(r.get("cpp")),              # custo por 1.000 pessoas alcancadas
        "cliques": n(r.get("clicks")),
        "ctr": n(r.get("ctr")),
        "cliques_link": n(r.get("inline_link_clicks")),
        "ctr_link": n(r.get("inline_link_click_ctr")),
        # video (retencao)
        "v_play3s": primeiro_valor(r.get("video_play_actions")),
        "v_thruplay": primeiro_valor(r.get("video_thruplay_watched_actions")),
        "v_25": primeiro_valor(r.get("video_p25_watched_actions")),
        "v_50": primeiro_valor(r.get("video_p50_watched_actions")),
        "v_75": primeiro_valor(r.get("video_p75_watched_actions")),
        "v_100": primeiro_valor(r.get("video_p100_watched_actions")),
        "v_tempo_medio": primeiro_valor(r.get("video_avg_time_watched_actions")),
        # reconhecimento / acao
        "conversas": ac.get("onsite_conversion.messaging_conversation_started_7d", 0),
        "engajamento_post": ac.get("post_engagement", 0),
        "reacoes": ac.get("post_reaction", 0),
        "comentarios": ac.get("comment", 0),
        "compartilhamentos": ac.get("post", 0),
        "salvos": ac.get("onsite_conversion.post_save", 0),
        "visitas_perfil": ac.get("onsite_conversion.view_profile", 0)
                          or ac.get("profile_visit", 0),
        "acoes": ac,
    }


def insights(tk, nivel, extra_campos, breakdown_dia, ate):
    campos = CAMPOS_INSIGHTS
    if extra_campos:
        campos += "," + extra_campos
    p = {"level": nivel, "fields": campos, "access_token": tk,
         "time_range": json.dumps({"since": INICIO, "until": ate}).replace('"', "'"),
         "limit": 500}
    if breakdown_dia:
        p["time_increment"] = 1
    return [linha(r) for r in paginar(f"act_{CONTA}/insights", p)]


def baixar(url, destino):
    """Baixa thumb/mp4 pro repo: a URL do fbcdn expira e da 403 por hotlink."""
    if not url or os.path.exists(destino):
        return os.path.exists(destino)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=180) as r, open(destino, "wb") as f:
            f.write(r.read())
        return True
    except Exception as e:
        print(f"  aviso: nao baixou {os.path.basename(destino)} ({e})")
        return False


def estrutura(tk):
    """Campanha/conjunto/anuncio ao vivo + criativo de cada anuncio."""
    camps = paginar(f"act_{CONTA}/campaigns", {
        "fields": "id,name,objective,status,effective_status,daily_budget,"
                  "lifetime_budget,created_time,start_time,stop_time",
        "access_token": tk})
    adsets = paginar(f"act_{CONTA}/adsets", {
        "fields": "id,name,campaign_id,status,effective_status,daily_budget,"
                  "optimization_goal,billing_event,destination_type,targeting",
        "access_token": tk})
    ads = paginar(f"act_{CONTA}/ads", {
        "fields": "id,name,adset_id,campaign_id,status,effective_status,"
                  "creative{id,object_type,video_id,thumbnail_url,"
                  "instagram_permalink_url,effective_object_story_id}",
        "access_token": tk})

    criativos = {}
    for a in ads:
        c = a.get("creative") or {}
        vid = c.get("video_id")
        slug = "".join(ch if ch.isalnum() else "_" for ch in a.get("name", "ad"))[:60].lower()
        thumb_rel = mp4_rel = ""
        dur = 0
        if vid:
            # A thumb do creative vem 64x64 (imprestavel no card). O objeto de
            # video tem thumbnails 1080x1920 — pegamos a maior/preferida.
            # O mp4 (fields=source) so vem se o video for da BM que autenticou;
            # o do Giacomo mora na "BM 02", entao normalmente NAO vem — o card
            # cai pro link do Instagram, que e o comportamento esperado.
            try:
                src = get(vid, {"fields": "source,length,thumbnails{uri,width,height,is_preferred}",
                                "access_token": tk})
                dur = n(src.get("length"))
                thumbs = (src.get("thumbnails") or {}).get("data", [])
                melhor = sorted(
                    thumbs,
                    key=lambda t: (bool(t.get("is_preferred")),
                                   n(t.get("width")) * n(t.get("height"))),
                    reverse=True)
                if melhor:
                    nomej = f"{slug}.jpg"
                    if baixar(melhor[0].get("uri", ""), os.path.join(DIR_CRIATIVOS, nomej)):
                        thumb_rel = f"criativos/{nomej}"
                nome = f"{slug}.mp4"
                if src.get("source") and baixar(src["source"], os.path.join(DIR_CRIATIVOS, nome)):
                    mp4_rel = f"criativos/{nome}"
            except Exception as e:
                print(f"  aviso: video {vid} ({e})")
        if not thumb_rel and c.get("thumbnail_url"):
            nome = f"{slug}.jpg"
            if baixar(c["thumbnail_url"], os.path.join(DIR_CRIATIVOS, nome)):
                thumb_rel = f"criativos/{nome}"
        criativos[a["id"]] = {
            "ad_id": a["id"], "nome": a.get("name", ""),
            "status": a.get("effective_status", ""),
            "tipo": c.get("object_type", ""),
            "thumb": thumb_rel, "mp4": mp4_rel, "duracao": dur,
            "instagram": c.get("instagram_permalink_url", ""),
            "facebook": (f"https://www.facebook.com/{c['effective_object_story_id']}"
                         if c.get("effective_object_story_id") else ""),
        }

    def limpa_adset(s):
        t = s.get("targeting") or {}
        geo = (t.get("geo_locations") or {})
        cidades = [c.get("name") for c in geo.get("cities", [])]
        regioes = [c.get("name") for c in geo.get("regions", [])]
        gen = {1: "homens", 2: "mulheres"}
        generos = [gen.get(g, str(g)) for g in (t.get("genders") or [])] or ["todos"]
        return {
            "id": s["id"], "nome": s.get("name", ""), "campanha_id": s.get("campaign_id"),
            "status": s.get("effective_status", ""),
            "verba_dia": n(s.get("daily_budget")) / 100,
            "otimizacao": s.get("optimization_goal", ""),
            "cobranca": s.get("billing_event", ""),
            "idade": f"{t.get('age_min','?')}–{t.get('age_max','?')}",
            "genero": ", ".join(generos),
            "local": ", ".join(cidades + regioes) or "—",
            "advantage": ((t.get("targeting_automation") or {})
                          .get("advantage_audience", None)),
        }

    return {
        "campanhas": [{"id": c["id"], "nome": c.get("name", ""),
                       "objetivo": c.get("objective", ""),
                       "status": c.get("effective_status", ""),
                       "verba_dia": n(c.get("daily_budget")) / 100,
                       "criada_em": (c.get("created_time") or "")[:10]} for c in camps],
        "conjuntos": [limpa_adset(s) for s in adsets],
        "anuncios": [{"id": a["id"], "nome": a.get("name", ""),
                      "conjunto_id": a.get("adset_id"),
                      "campanha_id": a.get("campaign_id"),
                      "status": a.get("effective_status", "")} for a in ads],
        "criativos": criativos,
    }


def main():
    saida = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, "raw_giacomo.json")
    gerado = date.fromisoformat(sys.argv[2]) if len(sys.argv) > 2 else date.today()
    ate = gerado.isoformat()
    tk = token()

    print("estrutura + criativos…")
    est = estrutura(tk)
    print("serie diaria…")
    dias = insights(tk, "account", "", True, ate)
    print("por anuncio…")
    por_ad = insights(tk, "ad", "campaign_name,adset_name,ad_name,ad_id", False, ate)
    print("total da conta…")
    total = insights(tk, "account", "", False, ate)

    raw = {
        "gerado_em": ate,
        "cliente": "Dr. Giácomo Trojan",
        "meta_conta": CONTA,
        "inicio": INICIO,
        "meta_imposto_rate": IMPOSTO,
        "estrutura": est,
        "dias": sorted(dias, key=lambda d: d["data"]),
        "por_anuncio": sorted(por_ad, key=lambda a: a["gasto"], reverse=True),
        "total": total[0] if total else None,
    }
    with open(saida, "w", encoding="utf-8") as f:
        json.dump(raw, f, ensure_ascii=False, indent=1)
    print(f"OK: {saida} — gerado_em={ate} dias={len(dias)} anuncios={len(por_ad)} "
          f"criativos={len(est['criativos'])} total={'sim' if raw['total'] else 'ainda sem entrega'}")


if __name__ == "__main__":
    main()
