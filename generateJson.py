from bs4 import BeautifulSoup
from pathlib import Path
import re, json


# ============================================================
# 1) Ler HTML (com charset correto para SCNES: latin-1)
# ============================================================
html = Path("CNES.html").read_text(encoding="latin-1")
soup = BeautifulSoup(html, "html.parser")


# ============================================================
# 2) Extrair todas as DIVs com top/left e texto
# ============================================================
items = []

for div in soup.find_all("div"):
    style = div.get("style", "")
    m = re.search(r"top:(\d+)px;left:(\d+)px", style.replace(" ", ""))
    if not m:
        continue

    top = int(m.group(1))
    left = int(m.group(2))

    text = div.get_text(strip=True).replace("\xa0", " ")
    if not text:
        continue

    items.append({"top": top, "left": left, "text": text})


# ============================================================
# 3) Agrupar por linha (top ± 2px)
# ============================================================
rows = {}

for it in items:
    topsim = it["top"]

    found_key = None
    for k in rows.keys():
        if abs(k - topsim) <= 2:
            found_key = k
            break

    if found_key is None:
        rows[topsim] = [it]
    else:
        rows[found_key].append(it)


# Ordenar linhas
lines = []
for k in sorted(rows.keys()):
    cols = sorted(rows[k], key=lambda x: x["left"])
    text = " ".join([c["text"] for c in cols])
    lines.append({"top": k, "cols": cols, "text": text})


# ============================================================
# 4) Interpretar valores (equipes + profissionais)
# ============================================================
teams = []
current_team = None
capture_members = False

for line in lines:
    t = line["text"]

    # ------------------------------------------------------------
    # Detectar início de uma nova equipe
    # ------------------------------------------------------------
    if "CNES :" in t:
        # Salvar equipe anterior
        if current_team:
            teams.append(current_team)

        # Montar nova equipe
        cnes = re.search(r"CNES\s*:\s*(\d+)", t)
        unid = t.split("-")[-1].strip()

        current_team = {
            "cnes": cnes.group(1) if cnes else "",
            "unid": unid,
            "type": "",
            "ine": "",
            "area": "",
            "segmento":"URBANO",
            "members": []
        }

        capture_members = False
        continue

    # ------------------------------------------------------------
    # Tipo da equipe
    # ------------------------------------------------------------
    if "70 - ESF" in t and current_team:
        current_team["type"] = "ESF"

    # ------------------------------------------------------------
    # INE + Área (correto e robusto)
    # ------------------------------------------------------------
    m = re.search(r"INE\s*:\s*(\d+)\s*/\s*\d+\s*-\s*(.+)", t)
    if m and current_team:
        current_team["ine"] = m.group(1).strip()
        current_team["area"] = m.group(2).strip()

    # ------------------------------------------------------------
    # Cabeçalho dos profissionais
    # ------------------------------------------------------------
    if "Nome do Profissional" in t:
        capture_members = True
        continue

    # ------------------------------------------------------------
    # Profissionais
    # ------------------------------------------------------------
    if capture_members:

        # CBO sempre aparece como "999999 - TEXTO"
        if re.search(r"\d{6}\s*-", t):

            cols = line["cols"]

            # A ordem das colunas é fixa no HTML do SCNES
            name = cols[0]["text"]
            cbo_raw = cols[1]["text"]

            cbo = cbo_raw.split("-")[0].strip()
            role = " ".join(cbo_raw.split("-")[1:]).strip()

      
            start_date = cols[5]["text"]

            member = {
                "name": name,
                "cbo": cbo,
                "role": role,
                "start_date": start_date,
            }

            current_team["members"].append(member)


# ============================================================
# 5) Salvar última equipe
# ============================================================
if current_team:
    teams.append(current_team)


# ============================================================
# 6) Gerar JSON final
# ============================================================
Path("teams_output.json").write_text(
    json.dumps({"teams": teams}, indent=4, ensure_ascii=False),
    encoding="utf-8"
)

print("OK! Equipes extraídas:", len(teams))
