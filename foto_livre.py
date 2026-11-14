"""Procura foto LIVRE no Wikimedia Commons (domínio público ou CC). Uso: python foto_livre.py "busca" [n]"""
import sys, json, urllib.parse, urllib.request
try:
    import truststore; truststore.inject_into_ssl()
except ImportError:
    pass
UA = {"User-Agent": "MondoNewsBot/1.0 (free-image lookup)"}
API = "https://commons.wikimedia.org/w/api.php"
def buscar(q, n=8):
    p = {"action": "query", "format": "json", "generator": "search", "gsrsearch": f"filetype:bitmap {q}", "gsrnamespace": 6,
         "gsrlimit": n, "prop": "imageinfo", "iiprop": "url|extmetadata|size", "iiurlwidth": 1600}
    d = json.load(urllib.request.urlopen(urllib.request.Request(API + "?" + urllib.parse.urlencode(p), headers=UA), timeout=30))
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
