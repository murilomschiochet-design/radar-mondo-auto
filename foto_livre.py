"""Procura foto LIVRE no Wikimedia Commons (domínio público ou CC). Uso: python foto_livre.py "busca" [n]"""
import sys, json, urllib.error, urllib.parse, urllib.request
import os, ssl
try:
    import truststore; truststore.inject_into_ssl()
except ImportError:
    pass
# na nuvem do Claude a internet passa por um proxy com certificado próprio
for _ca in ("/root/.ccr/ca-bundle.crt", os.environ.get("SSL_CERT_FILE", "")):
    if _ca and os.path.exists(_ca):
        ssl._create_default_https_context = lambda: ssl.create_default_context(cafile=_ca)
        break
UA = {"User-Agent": "RadarMondoBot/1.0 (Instagram @radar_mondo; free-licence image lookup)"}
API = "https://commons.wikimedia.org/w/api.php"
def buscar(q, n=8):
    p = {"action": "query", "format": "json", "generator": "search", "gsrsearch": f"filetype:bitmap {q}", "gsrnamespace": 6,
         "gsrlimit": n, "prop": "imageinfo", "iiprop": "url|extmetadata|size", "iiurlwidth": 1600}
    url = API + "?" + urllib.parse.urlencode(p)
    import time
    for tentativa in range(4):          # o Wikimedia às vezes responde 429 (muitos pedidos): espera e tenta de novo
        try:
            d = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30))
            break
        except urllib.error.HTTPError as e:
            if e.code != 429 or tentativa == 3:
                raise SystemExit(f"Wikimedia respondeu {e.code}. Plano B: abra com WebFetch este endereço e use a mesma regra de licença: {url}")
            time.sleep(8 + tentativa * 12)
    res = []
    for pg in (d.get("query", {}).get("pages", {}) or {}).values():
        ii = pg["imageinfo"][0]; m = ii.get("extmetadata", {})
        lic = m.get("LicenseShortName", {}).get("value", "")
        if not any(x in lic for x in ("Public domain", "CC0", "CC BY")):
            continue
        autor = urllib.parse.unquote(m.get("Artist", {}).get("value", "")).split(">")[-2].split("<")[0] if "<" in m.get("Artist", {}).get("value", "") else m.get("Artist", {}).get("value", "")
        res.append({"titulo": pg["title"], "url": ii.get("thumburl") or ii["url"], "w": ii["width"], "h": ii["height"],
                    "licenca": lic, "autor": autor.strip()[:80], "pagina": ii.get("descriptionurl")})
    return res
if __name__ == "__main__":
    for r in buscar(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 8):
        print(json.dumps(r, ensure_ascii=False))
