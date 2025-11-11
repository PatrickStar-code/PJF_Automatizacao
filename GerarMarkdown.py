from pathlib import Path
import json,re
from docling.document_converter import DocumentConverter

converter = DocumentConverter()


result = converter.convert("Relatorio.pdf")

document = result.document
markdown_output = document.export_to_markdown()
json_output = document.export_to_dict()
