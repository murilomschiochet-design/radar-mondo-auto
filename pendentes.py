"""Qual notícia publicar nesta rodada.

Só a MAIS NOVA ainda não publicada. As mais antigas que ficaram para trás (falha numa rodada anterior)
são marcadas como "pulada" em publicados.json: notícia velha não sai mais, e nunca saem dois reels juntos.
Imprime "ids=<id>" para o GITHUB_OUTPUT.
"""
import datetime as dt
import glob
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
REG = os.path.join(BASE, "publicados.json")

reg = json.load(open(REG, encoding="utf-8")) if os.path.exists(REG) else {}
ids = [os.path.basename(f)[:-5] for f in sorted(glob.glob(os.path.join(BASE, "itens", "*.json")))
       if not f.endswith("teste.json")]
novos = [i for i in ids if i not in reg]
agora = dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes")
for velho in novos[:-1]:
    reg[velho] = {"pulada": "ficou atrasada (falha numa rodada anterior)", "quando": agora}
if novos[:-1]:
    json.dump(reg, open(REG, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ids=" + (novos[-1] if novos else ""))
