import json

# Define o limiar de recorrência (quantas vezes um elemento deve aparecer para ser considerado recorrente)
LIMIAR_RECORRENCIA = 3  # Elementos com quantidade >= 2 serão mantidos

print("Iniciando filtragem de elementos recorrentes...")

# Carrega o arquivo de grupos agrupados
with open("grupos_agrupados.json", "r", encoding="utf-8") as f:
    dados = json.load(f)

# Estatísticas iniciais
total_elementos = 0
for categoria in dados:
    total_elementos += len(dados[categoria])
print(f"Total de elementos antes da filtragem: {total_elementos}")

# Filtra elementos recorrentes
filtrados = {}
elementos_filtrados = 0
elementos_mantidos = 0

for categoria, grupos in dados.items():
    # Mantém apenas elementos com quantidade >= LIMIAR_RECORRENCIA
    filtrados[categoria] = []
    
    for grupo in grupos:
        if grupo.get("quantidade", 0) >= LIMIAR_RECORRENCIA:
            filtrados[categoria].append(grupo)
            elementos_mantidos += 1
        else:
            elementos_filtrados += 1

# Estatísticas finais
print(f"Total de elementos filtrados (quantidade < {LIMIAR_RECORRENCIA}): {elementos_filtrados}")
print(f"Total de elementos mantidos (padrões recorrentes): {elementos_mantidos}")

# Salva o resultado em um novo arquivo JSON
with open("elementos_recorrentes.json", "w", encoding="utf-8") as f:
    json.dump(filtrados, f, ensure_ascii=False, indent=2)

print("Filtragem concluída! Resultado salvo em 'elementos_recorrentes.json'")