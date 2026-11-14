"""Coleta manchetes recentes nas fontes (RSS grátis) -> manchetes.json (+ lista na tela). Uso: python coletar.py [horas=2]"""
import sys, json, re, time, email.utils, urllib.request, xml.etree.ElementTree as ET, datetime as dt
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
FEEDS = {
 "ANSA Mondo": "https://www.ansa.it/sito/notizie/mondo/mondo_rss.xml",
 "ANSA Ultima ora": "https://www.ansa.it/sito/ansait_rss.xml",
 "BBC World": "https://feeds.bbci.co.uk/news/world/rss.xml",
 "Al Jazeera": "https://www.aljazeera.com/xml/rss/all.xml",
 "DW": "https://rss.dw.com/rdf/rss-en-all",
 "France24": "https://www.france24.com/en/rss",
 "Guardian World": "https://www.theguardian.com/world/rss",
 "BleepingComputer": "https://www.bleepingcomputer.com/feed/",
 "The Record": "https://therecord.media/feed",
 "Simple Flying": "https://simpleflying.com/feed/",
 "NASA": "https://www.nasa.gov/news-release/feed/",
 "Euronews": "https://www.euronews.com/rss?level=theme&name=news",
 "The Hacker News": "https://feeds.feedburner.com/TheHackersNews",
 "Live Science": "https://www.livescience.com/feeds/all",
}
UA = {"User-Agent": "Mozilla/5.0 (NewsCollector/1.0)"}
horas = float(sys.argv[1]) if len(sys.argv) > 1 else 2
limite = time.time() - horas * 3600
out = []
for fonte, url in FEEDS.items():
    try:
        x = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20).read()
        root = ET.fromstring(x)
        for it in root.iter():
            if not it.tag.endswith("item") and not it.tag.endswith("entry"):
                continue
            g = lambda n: next((c.text or "" for c in it if c.tag.split("}")[-1] == n), "")
            data = g("pubDate") or g("date") or g("published") or g("updated")
            try:
                ts = email.utils.parsedate_to_datetime(data).timestamp()
            except Exception:
                try: ts = dt.datetime.fromisoformat(data.replace("Z", "+00:00")).timestamp()
                except Exception: ts = time.time()
            if ts < limite: continue
            link = g("link") or next((c.get("href") for c in it if c.tag.split("}")[-1] == "link"), "")
            desc = re.sub("<[^>]+>", "", g("description") or g("summary"))[:300]
            out.append({"fonte": fonte, "titulo": g("title").strip(), "resumo": desc.strip(), "link": link, "ts": ts})
    except Exception as e:
        print("ERRO", fonte, str(e)[:80], file=sys.stderr)
out.sort(key=lambda d: -d["ts"])
json.dump(out, open("manchetes.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for d in out: print(f"[{d['fonte']}] {d['titulo']}")
