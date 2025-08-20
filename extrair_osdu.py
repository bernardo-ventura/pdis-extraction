import os
import json
from pathlib import Path

# Caminho para a pasta dos schemas OSDU clonados
SCHEMAS_PATH = Path("data-definitions/SchemaRegistrationResources/shared-schemas/osdu")


# Lista para armazenar os documentos em formato textual
documentos = []

# Itera por todos os arquivos .json dentro da pasta de schemas
for json_path in SCHEMAS_PATH.rglob("*.json"):
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Busca campos dentro de 'schema' se existir, senão usa a raiz
        schema = data.get("schema", data)
        # Tenta pegar o 'kind' na raiz, em schemaInfo ou dentro de properties
        kind = (
            data.get("kind")
            or data.get("schemaInfo", {}).get("schemaIdentity", {}).get("id")
            or schema.get("kind", "")
        )
        title = schema.get("title", "")
        description = schema.get("description", "")
        properties = schema.get("properties", {})
        prop_names = ", ".join(properties.keys()) if isinstance(properties, dict) else ""

        texto = f"""
Kind: {kind}
Title: {title}
Description: {description}
Properties: {prop_names}
File: {json_path.name}
"""
        # Só salva se pelo menos um campo relevante não for vazio
        if title or description or prop_names:
            documentos.append(texto.strip())

    except Exception as e:
        print(f"Erro ao ler {json_path}: {e}")

# Salva em arquivo texto para debug ou indexação
with open("documentos_osdu.txt", "w", encoding="utf-8") as f:
    for doc in documentos:
        f.write(doc + "\n---\n")

print(f"Processados {len(documentos)} documentos OSDU.")
