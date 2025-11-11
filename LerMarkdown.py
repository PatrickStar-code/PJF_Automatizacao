import re
import json
from pathlib import Path

input_file = Path("output.md")
markdown_text = input_file.read_text(encoding="utf-8")

team_blocks = re.split(r'\*\*Estabelecimento\s*:\*\*', markdown_text)
teams = []

team_pattern = re.compile(
    r'CNES\s*:\s*(\d+)\s*-\s*([^\n]+)\n'     # ← agora pega só até o fim da linha
    r'.*?70\s*-\s*(.*?)\s+INE\s*:\s*(\d+)\s*/\s*\d+\s*-\s*(.*?)\s+\*\*Munic',
    re.DOTALL
)

member_pattern = re.compile(
    r'([A-ZÀ-Ú\s]+?)(\d{6})\s*-\s*([A-ZÀ-Ú\s]+(?:DE|DA|DO|DAS|DOS)?[A-ZÀ-Ú\s]*)\s+'
    r'(\d+)\s+(\d+)\s+(\d+)\s+([\d/]+)',
    re.MULTILINE
)

for block in team_blocks:
    if not block.strip():
        continue

    team_match = team_pattern.search(block)
    if not team_match:
        continue

    code, unit, type_, ine, area = team_match.groups()

    if " - " in area:
        area = area.split(" - ", 1)[1].strip()

    unit = unit.strip()

    members = []
    for m in member_pattern.finditer(block):
        members.append({
            "name": m.group(1).strip(),
            "cbo": m.group(2).strip(),
            "role": m.group(3).strip(),
            "hours": int(m.group(4)),
            "microarea": int(m.group(5)),
            "other": int(m.group(6)),
            "start_date": m.group(7).strip()
        })

    teams.append({
        "name": type_.strip(),
        "ine": ine.strip(),
        "unid": unit,   # agora ficará só “UBS GRAMA”
        "area": area.strip(),
        "members": members
    })

output = {"teams": teams}
output_file = Path("teams_output.json")
output_file.write_text(json.dumps(output, indent=4, ensure_ascii=False), encoding="utf-8")

print(f"✅ {len(teams)} equipes extraídas e salvas em {output_file.resolve()}")
