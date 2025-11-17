from pathlib import Path
from docling.document_converter import DocumentConverter

converter = DocumentConverter()

pdf_path = Path("Relatorio.pdf")

result = converter.convert(pdf_path)

document = result.document
markdown_output = document.export_to_markdown()

# Salvar em arquivo
with open("relatorio.md", "w", encoding="utf-8") as f:
    f.write(markdown_output)

print("Markdown salvo em relatorio.md!")
