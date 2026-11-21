"""Publica no Instagram @radar_mondo o que o gerar.py criou para itens/<id>.json.

  python publicar.py <id>
Story sempre; post (carrossel: notícia + slide fixo de seguir) ou reel quando o item pede.
Imagens vão por URL pública (MIDIA, Cloudflare Pages publicado pelo workflow antes daqui); o reel vai por upload direto.
Credenciais: IG_TOKEN e IG_USER_ID (Secrets) ou credenciais/instagram.txt + config.json no PC.
Registro: publicados.json (não publica duas vezes).
"""
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

if os.name == "nt":
    try:
        import truststore
        truststore.inject_into_ssl()
    except ImportError:
        pass

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG = json.load(open(os.path.join(BASE, "config.json"), encoding="utf-8"))
GRAPH = "https://graph.facebook.com/v23.0"
UA = {"User-Agent": "RadarMondo/1.0"}
REG = os.path.join(BASE, "publicados.json")


def credencial():
    tok, uid = os.environ.get("IG_TOKEN"), os.environ.get("IG_USER_ID")
    if not tok:
        tok = open(os.path.join(BASE, "credenciais", "instagram.txt"), encoding="utf-8").read().strip().strip("()<>\"' ")
        uid = uid or CONFIG["user_id"]
    return tok, uid


def api(metodo, caminho, tok, **params):
    url = f"{GRAPH}/{caminho}"
    corpo = None
    if metodo == "GET":
        url += "?" + urllib.parse.urlencode(dict(params, access_token=tok))
    else:
        corpo = urllib.parse.urlencode(dict(params, access_token=tok)).encode()
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=corpo, headers=UA, method=metodo), timeout=120) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"Instagram {e.code}: {e.read().decode('utf-8', 'replace')[:400]}")


def esperar(tok, cid, limite=600):
    fim = time.time() + limite
    while time.time() < fim:
        st = api("GET", cid, tok, fields="status_code").get("status_code")
        if st == "FINISHED":
            return
        if st in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"container {cid}: {st}")
        time.sleep(6)
    raise RuntimeError(f"container {cid} não ficou pronto")


def publicar_container(tok, uid, cid):
    esperar(tok, cid)
    return api("POST", f"{uid}/media_publish", tok, creation_id=cid)["id"]


def subir_reel(tok, uid, mp4, legenda, capa_url=None):
    params = dict(media_type="REELS", upload_type="resumable", caption=legenda, share_to_feed="true")
    if capa_url:
        params["cover_url"] = capa_url
    c = api("POST", f"{uid}/media", tok, **params)
    req = urllib.request.Request(c["uri"], data=open(mp4, "rb").read(), method="POST",
                                 headers=dict(UA, Authorization=f"OAuth {tok}", offset="0", file_size=str(os.path.getsize(mp4))))
    with urllib.request.urlopen(req, timeout=300) as r:
        r.read()
    return c["id"]


def main():
    iid = sys.argv[1]
    item = json.load(open(os.path.join(BASE, "itens", f"{iid}.json"), encoding="utf-8"))
    pasta = os.path.join(BASE, "saida", iid)
    formato = json.load(open(os.path.join(pasta, "gerado.json"), encoding="utf-8"))["formato"]
    reg = json.load(open(REG, encoding="utf-8")) if os.path.exists(REG) else {}
    r = reg.setdefault(iid, {})
    tok, uid = credencial()
    midia = f"{CONFIG['midia']}/{iid}"
    legenda = item.get("legenda", "").strip()[:2200]

    if formato == "post" and not r.get("feed"):
        filhos = [api("POST", f"{uid}/media", tok, image_url=f"{midia}/{f}", is_carousel_item="true")["id"] for f in ("post.jpg", "post2.jpg", "cta.jpg") if os.path.exists(os.path.join(pasta, f))]
        for f in filhos:
            esperar(tok, f, 300)
        c = api("POST", f"{uid}/media", tok, media_type="CAROUSEL", children=",".join(filhos), caption=legenda)["id"]
        r["feed"] = publicar_container(tok, uid, c)
        print(" post publicado:", r["feed"])
    if formato == "reel" and not r.get("feed"):
        c = subir_reel(tok, uid, os.path.join(pasta, "reel.mp4"), legenda, f"{midia}/capa.jpg")
        r["feed"] = publicar_container(tok, uid, c)
        print(" reel publicado:", r["feed"])
    if formato in ("post", "reel"):
        r["formato"] = formato
    json.dump(reg, open(REG, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if not r.get("story"):
        c = api("POST", f"{uid}/media", tok, media_type="STORIES", image_url=f"{midia}/story.jpg")["id"]
        r["story"] = publicar_container(tok, uid, c)
        print(" story publicado:", r["story"])
    r["quando"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes")
    json.dump(reg, open(REG, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
