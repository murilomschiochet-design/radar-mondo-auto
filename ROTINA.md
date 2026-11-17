# Rotina de hora em hora do Claude — Instagram @radar_mondo (notícias do mundo, em italiano)

Você roda de hora em hora, das 06:00 às 23:00 (Roma). A cada rodada: escolhe **a notícia mais quente da última hora** que ainda não foi dada, escreve em **italiano** e grava `itens/<id>.json`. O push dispara o GitHub Actions, que gera as artes e publica na hora.

## Linha editorial (o mais importante)
- Mundo, geopolítica **neutra**, hackers e segurança digital, aviação, espaço e ciência, tecnologia, grandes fatos e curiosidades do que está acontecendo agora. **Não** é página de política partidária: nada de opinião, nada de "lado", nada de adjetivo contra ou a favor de governo ou partido.
- **Nunca invente nada.** Cada fato precisa estar na matéria que você abriu. Número, nome e citação exatamente como na fonte.
- **Nunca afirme "ninguém confirmou", "nenhum governo", "é a primeira vez" ou parecido sem conferir as manchetes das últimas 24 h** (`python coletar.py 24`): muitas vezes um lado já confirmou ontem. Escreva exatamente quem confirmou e quem não confirmou.
- Notícia de última hora sem confirmação: só se vier de agência ou veículo grande (ANSA, BBC, AP, Reuters, Al Jazeera, DW, France24, Guardian, Euronews) **ou** de 2 fontes. Boato nunca vira fato: se for usar, escreva "secondo …" / "non confermato".
- Sem mortes ou violência explícita nas imagens, sem fotos de vítimas, sem crianças identificáveis.
- **Não repita** assunto já publicado nas últimas 24 h (veja `itens/` e `publicados.json`), a não ser que haja um fato novo importante (aí diga o que mudou).

## Passo 1 — horário e o que já saiu
- Hora em Roma: `python -c "import datetime,zoneinfo;print(datetime.datetime.now(zoneinfo.ZoneInfo('Europe/Rome')))"`. Se for antes das 06:00 ou depois das 23:59, **pare** ("fora do horário").
- `<id>` = data e hora de Roma no formato `AAAAMMDD-HH` (ex.: `20261115-06`). Se `itens/<id>.json` já existir, **pare**.
- Leia `publicados.json` e os títulos dos `itens/*.json` das últimas 24 h.

## Passo 2 — coletar e escolher
- `python coletar.py 2` (manchetes das últimas 2 h em `manchetes.json`). Se o comando falhar, use WebFetch nos RSS listados em `coletar.py`.
- Escolha **uma** notícia: a mais relevante e mais nova que não foi dada. Prefira o que interessa a um leitor italiano curioso (grande impacto, fato inédito, algo que todo mundo vai comentar).
- Abra a matéria (WebFetch) e, se for notícia quente, confira em uma segunda fonte.
- Se não houver nada forte e novo, **não publique** nesta hora: escreva no relatório "nessuna notizia nuova" e pare.

## Passo 3 — formato
- **Story: sempre** (texto em caixas brancas sobre fundo preto).
- **Post ou Reel: só notícia forte** (fato grande no mundo, ataque hacker relevante, pane ou recorde na aviação/espaço, curiosidade que viraliza) **e** só se respeitar o intervalo:
  - até `fim_semana1` do `config.json` (22/11): pelo menos `intervalo_feed_min` (90 min) desde o último post/reel em `publicados.json` (campo `quando` dos itens com `formato` post/reel);
  - depois: pelo menos 60 min.
- **REEL é o formato principal do feed** (em conta pequena o reel entrega 10x mais que o carrossel: 155 views contra menos de 10). Em toda rodada com notícia boa e com o intervalo cumprido, faça **reel** além do story:
  - `"reel_texto"` (padrão): imagem parada de 10 s no estilo do story, fundo preto e caixas brancas. Escreva `reel_blocos`: 3 a 5 blocos curtos, o primeiro é o gancho ("🔴 ULTIM'ORA: …", "⚠️ …"), o último diz o que acontece agora.
  - `"reel"` com foto livre: só quando a notícia tem uma imagem livre muito forte (avião, foguete, lugar).
- **Carrossel (post): quase nunca.** Só se a notícia precisar de uma foto para ser entendida e não couber em reel.
- **Foto livre obrigatória** para post/reel: `python foto_livre.py "busca em inglês" 8` (Wikimedia Commons: domínio público, CC0, CC BY, CC BY-SA). Escolha só foto que realmente tenha a ver (o lugar, o objeto, a instituição). Nunca foto de agência (Reuters, AP, Getty, ANSA) nem print de TV/rede social. Se o `foto_livre.py` falhar (ex.: erro 429 do Wikimedia), ele mostra o endereço da busca: abra com WebFetch e escolha pela mesma regra de licença. Sem foto boa → fica só o story.

## Passo 4 — escrever `itens/<id>.json`
```json
{
 "id": "20261115-06",
 "formato": "story | post | reel | reel_texto",
 "chip": "Aviazione",
 "titulo": "Manchete do post/reel, até ~110 caracteres, clara e sem clickbait falso",
 "fontes": ["ANSA", "BBC"],
 "links": ["https://..."],
 "story": {"blocos": ["⚠️ Primeiro bloco: o fato principal.", "Segundo bloco: o dado que explica.", "Terceiro (opcional): o que acontece agora."]},
 "fatos": [["✈️ Fato 1 do reel."], ["Fato 2.", "Complemento curto."], ["Fato 3."]],
 "reel_blocos": ["🔴 ULTIM'ORA: gancho curto.", "O fato principal.", "O número ou a frase que impressiona.", "Cosa succede adesso."],
 "fotos": [{"url": "url da foto do foto_livre.py", "credito": "Foto: Autor (CC BY 4.0)", "pos": "50% 40%"}],
 "legenda": "2 a 4 frases contando a notícia.\n\nFonte: ANSA, BBC\n\n#notizie #mondo #ultimora #… (4 a 6)"
}
```
- Tudo em **italiano**, frases curtas, tom de agência (neutro). `story.blocos`: 2 a 4 blocos de até ~150 caracteres; o primeiro começa com um emoji que combine (⚠️ 🔴 ✈️ 🚀 💻 🌍 🔬 🌪️).
- `chip`: uma palavra: `Mondo`, `Aviazione`, `Hacker`, `Spazio`, `Tecnologia`, `Scienza`, `Economia`, `Clima`, `Curiosità`.
- `formato: "story"` → `titulo`, `fatos` e `fotos` podem ficar vazios. `post` → precisa de `titulo` e 1 foto. `reel` → `titulo`, 2 ou 3 grupos em `fatos` e 1 a 3 fotos. `reel_texto` → `reel_blocos` (3 a 5) e `legenda`; sem foto.
- Na `legenda` de post/reel, termine com "Seguici @radar_mondo per non perdere le notizie del mondo, ora per ora."

## Passo 5 — validar e publicar
```bash
python -c "import json,sys;d=json.load(open(sys.argv[1],encoding='utf-8'));assert d['formato'] in ('story','post','reel','reel_texto');assert 1<=len(d['story']['blocos'])<=4;assert d['formato'] in ('story','reel_texto') or (d['titulo'] and d['fotos']);print('ok')" itens/<id>.json
git add itens/<id>.json && git commit -m "noticia <id>" && git push origin main
```
(Se o push falhar por mudanças remotas: `git pull --rebase` e push de novo.)

## Passo 6 — relatório (português, curto)
Hora, a notícia escolhida (título em italiano + fonte), o formato e por quê; ou "nessuna notizia nuova".
