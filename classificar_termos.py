import json
import os
import google.generativeai as genai
from dotenv import load_dotenv
import time

# Carrega variáveis do .env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# Função para classificar um termo usando o Gemini
def classificar_termo(termo):
    prompt = f"""
    Classifique o seguinte termo técnico da indústria de óleo e gás em UMA das seguintes áreas temáticas:
    - ambiental
    - social
    - saúde e segurança
    - gerenciamento de resíduos
    - econômico
    - técnico
    - indefinido (caso não se encaixe claramente em nenhuma das anteriores)
    
    Termo: "{termo}"
    
    Responda apenas com o nome da área, sem explicações adicionais.
    """
    
    modelo = genai.GenerativeModel("gemini-1.5-flash")
    resposta = modelo.generate_content(prompt)
    
    # Limpa e normaliza a resposta
    area = resposta.text.strip().lower()
    
    # Verifica se a resposta é uma das áreas válidas
    areas_validas = ["ambiental", "social", "saúde e segurança", "gerenciamento de resíduos", 
                     "econômico", "técnico", "indefinido"]
    
    # Busca correspondência ou define como indefinido
    if area not in areas_validas:
        for area_valida in areas_validas:
            if area_valida in area:
                area = area_valida
                break
        else:
            area = "indefinido"
    
    return area

# Função principal
def main():
    # Carrega o arquivo JSON com os termos
    arquivo_entrada = "elementos_recorrentes.json"
    arquivo_saida = "termos_classificados.json"
    
    print(f"Carregando dados de {arquivo_entrada}...")
    with open(arquivo_entrada, "r", encoding="utf-8") as f:
        dados = json.load(f)
    
    # Estrutura para armazenar os resultados
    resultado = {
        "conceitos": [],
        "processos": [],
        "artefatos": [],
        "atores": []
    }
    
    # Processa cada categoria
    for categoria in resultado.keys():
        print(f"\nProcessando categoria: {categoria}")
        total_itens = len(dados.get(categoria, []))
        
        for i, item in enumerate(dados.get(categoria, [])):
            termo = item.get("grupo_normalizado", "")
            if not termo:
                continue
                
            print(f"  [{i+1}/{total_itens}] Classificando: {termo}")
            try:
                area = classificar_termo(termo)
                
                # Adiciona ao resultado
                resultado[categoria].append({
                    "termo": termo,
                    "area": area
                })
                
                print(f"    → Classificado como: {area}")
                
                # Pausa para evitar limites de rate da API
                time.sleep(1.5)
                
            except Exception as e:
                print(f"    ✗ Erro ao classificar termo: {e}")
                # Adiciona como indefinido em caso de erro
                resultado[categoria].append({
                    "termo": termo,
                    "area": "indefinido"
                })
                time.sleep(3)  # Pausa maior em caso de erro
    
    # Salva o resultado em um novo arquivo JSON
    print(f"\nSalvando resultados em {arquivo_saida}...")
    with open(arquivo_saida, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    
    print("Classificação concluída!")

if __name__ == "__main__":
    main()