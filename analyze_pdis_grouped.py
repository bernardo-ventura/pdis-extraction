import os
import json
import unicodedata
from rapidfuzz import fuzz, process

PASTA_JSONS = "extracted-data"
CATEGORIAS = ["conceitos", "processos", "artefatos", "atores"]
LIMIAR_SIMILARIDADE = 90  # Percentual para considerar elementos semelhantes

def normalizar(texto):
    texto = texto.lower()
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    texto = ''.join(c for c in texto if c.isalnum() or c.isspace())
    texto = ' '.join(texto.split())
    return texto

print("Iniciando análise dos arquivos JSON...")

# Carrega todos os elementos
elementos = {cat: [] for cat in CATEGORIAS}
arquivos = [f for f in os.listdir(PASTA_JSONS) if f.endswith(".json")]
print(f"Total de arquivos encontrados: {len(arquivos)}")

for idx, nome_arquivo in enumerate(arquivos):
    print(f"Lendo arquivo {idx+1}/{len(arquivos)}: {nome_arquivo}")
    caminho = os.path.join(PASTA_JSONS, nome_arquivo)
    with open(caminho, "r", encoding="utf-8") as f:
        dados = json.load(f)
        for cat in CATEGORIAS:
            elementos[cat].extend(dados.get(cat, []))

for cat in CATEGORIAS:
    print(f"\nTotal de elementos coletados em '{cat}': {len(elementos[cat])}")

# Agrupa elementos semelhantes
grupos = {cat: [] for cat in CATEGORIAS}
contagem = {cat: [] for cat in CATEGORIAS}

for cat in CATEGORIAS:
    print(f"\nAgrupando elementos em '{cat}'...")
    for i, elem in enumerate(elementos[cat]):
        if i % 1000 == 0 and i > 0:
            print(f"  Processados {i} elementos em '{cat}'...")
        # Garante que elem é string
        if isinstance(elem, dict):
            elem_str = elem.get("nome", "")
        elif isinstance(elem, str):
            elem_str = elem
        else:
            continue  # ignora outros tipos
        if not elem_str.strip():
            continue
        elem_norm = normalizar(elem_str)
        match = process.extractOne(elem_norm, [g[0] for g in grupos[cat]], scorer=fuzz.token_sort_ratio)
        if match and match[1] >= LIMIAR_SIMILARIDADE:
            idx = match[2]
            grupos[cat][idx][1].append(elem_str)
        else:
            grupos[cat].append([elem_norm, [elem_str]])
    print(f"  Total de grupos formados em '{cat}': {len(grupos[cat])}")

# Conta ocorrências agrupadas
for cat in CATEGORIAS:
    print(f"\nContando ocorrências agrupadas em '{cat}'...")
    for grupo in grupos[cat]:
        contagem[cat].append({
            "grupo_normalizado": grupo[0],
            "exemplos": list(set(grupo[1])),
            "quantidade": len(grupo[1])
        })
    print(f"  Total de grupos contabilizados em '{cat}': {len(contagem[cat])}")

# Exemplo de saída: top 10 grupos por categoria
for cat in CATEGORIAS:
    print(f"\nTop 10 grupos de '{cat}':")
    top = sorted(contagem[cat], key=lambda x: x["quantidade"], reverse=True)[:10]
    for g in top:
        print(f"- {g['grupo_normalizado']} ({g['quantidade']}): exemplos: {g['exemplos'][:3]}")

print("\nSalvando resultado em 'grupos_agrupados.json'...")
with open("grupos_agrupados.json", "w", encoding="utf-8") as f:
    json.dump(contagem, f, ensure_ascii=False, indent=2)
print("Processo finalizado com sucesso!")
