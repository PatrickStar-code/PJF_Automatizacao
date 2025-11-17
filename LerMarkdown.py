import re
import json
from pathlib import Path

input_file = Path("output.md")
text = input_file.read_text(encoding="utf-8")

teams = []

# Separar blocos de equipe
blocks = re.split(r'\n70\s*-\s*', text)
blocks = blocks[1:]  # remove o que vem antes da primeira equipe

for block in blocks:
    block = "70 - " + block  # restaura início removido no split

    # --- EXTRAI CABEÇALHO ---
    header_regex = re.compile(
        r'70\s*-\s*(.+?)\s*\n'                       # Tipo da equipe
        r'.*?INE\s*:\s*(\d+)\s*/\s*\d+\s*-\s*(.+?)\s*\n'  # INE / área
        r'.*?CNES\s*:\s*(\d+)\s*-\s*(.+?)\n',        # CNES + unidade
        re.DOTALL
    )

    h = header_regex.search(block)
    if not h:
        continue

    tipo, ine, area, cnes, unidade = h.groups()

    # --- EXTRAI MEMBROS ---
    members = []

    member_regex = re.compile(
        r'\|\s*([A-ZÀ-Ú\s]+?)\s*\|\s*'      # Nome
        r'(\d{6})\s*-\s*([A-ZÀ-Ú\s]+?)\s*\|\s*'  # CBO + Função
        r'(\d+)\s*\|\s*\d+\s*\|\s*\d+\s*\|\s*'   # CH 1 (os outros ignorados)
        r'(\d{2}/\d{2}/\d{4})',                 # Data início
        re.MULTILINE
    )

    for m in member_regex.finditer(block):
        name = m.group(1).strip()
        cbo = m.group(2).strip()
        role = m.group(3).strip()
        hours = int(m.group(4))
        start_date = m.group(5).strip()

        members.append({
            "name": name,
            "cbo": cbo,
            "role": role,
            "hours": hours,
            "microarea": 0,
            "other": 0,
            "start_date": start_date
        })

    teams.append({
        "name": tipo.strip(),
        "ine": ine.strip(),
        "unid": unidade.strip(),
        "area": area.strip(),
        "members": members
    })


# --- SALVA JSON ---
output = {"teams": teams}
Path("teams_output.json").write_text(
    json.dumps(output, indent=4, ensure_ascii=False),
    encoding="utf-8"
)

print(f"✅ Arquivo gerado! {len(teams)} equipes salvas em teams_output.json")
