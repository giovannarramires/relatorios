#!/usr/bin/env python3
# ============================================================
# Baixa os thumbnails dos criativos (fbcdn) para o repositório,
# servindo-os localmente (o fbcdn tem anti-hotlink 403 + expira).
# Reescreve raw_alarcon.json: thumb -> "criativos/<slug>.jpg".
# Idempotente. Chamado pela automação após o JSON ser gravado.
# Uso: python3 baixar_criativos.py <raw_alarcon.json>
# ============================================================
import json, sys, os, re, urllib.request, ssl

def slugify(nome):
    s = re.sub(r"[^a-zA-Z0-9]+", "_", (nome or "ad").strip().lower()).strip("_")
    return s[:60] or "ad"

def baixar(url, destino):
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Accept": "image/avif,image/webp,image/*,*/*;q=0.8",
    })
    with urllib.request.urlopen(req, timeout=30, context=ctx) as r:
        data = r.read()
    if len(data) < 500:
        raise ValueError(f"resposta muito pequena ({len(data)} bytes)")
    with open(destino, "wb") as f:
        f.write(data)
    return len(data)

def main():
    raw_path = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/Library/GGD/relatorios/alarcon/raw_alarcon.json")
    base = os.path.dirname(os.path.abspath(raw_path))
    cr_dir = os.path.join(base, "criativos")
    os.makedirs(cr_dir, exist_ok=True)

    doc = json.load(open(raw_path, encoding="utf-8"))
    # aceita lista unica (criativos) ou mapa por mes (criativos_por_mes)
    criativos = list(doc.get("criativos", []))
    for lst in doc.get("criativos_por_mes", {}).values():
        criativos.extend(lst)
    ok = fail = 0
    for c in criativos:
        src = c.get("thumb_src") or c.get("thumb", "")
        if not src.startswith("http"):
            continue  # ja e local
        slug = c.get("slug") or slugify(c.get("nome"))
        c["slug"] = slug
        c["thumb_src"] = src
        destino = os.path.join(cr_dir, slug + ".jpg")
        try:
            n = baixar(src, destino)
            c["thumb"] = f"criativos/{slug}.jpg"
            ok += 1
            print(f"  [ok] {slug}.jpg ({n} bytes)")
        except Exception as e:
            fail += 1
            # se ja existe uma versao baixada antes, mantem
            if os.path.exists(destino):
                c["thumb"] = f"criativos/{slug}.jpg"
                print(f"  [warn] {slug}: {e} — mantendo versao anterior")
            else:
                c["thumb"] = ""  # gerador mostra placeholder
                print(f"  [erro] {slug}: {e} — sem imagem")

    json.dump(doc, open(raw_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"Criativos: {ok} baixados, {fail} falhas -> {cr_dir}")

if __name__ == "__main__":
    main()
