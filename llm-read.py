import fitz  # PyMuPDF
import google.generativeai as genai
from dotenv import load_dotenv
import os
import json
import time
import re

# Carrega variáveis do .env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# Divide o texto em blocos menores (~8000 caracteres)
def dividir_texto(texto, tamanho_max=8000):
    return [texto[i:i+tamanho_max] for i in range(0, len(texto), tamanho_max)]

# Extrai texto do PDF usando PyMuPDF
def extrair_texto_pdf(caminho_pdf):
    doc = fitz.open(caminho_pdf)
    texto = ""
    for pagina in doc:
        texto += pagina.get_text()
    return texto

# Gera prompt para cada bloco de texto
def gerar_prompt(texto):
    return f"""
A partir do seguinte texto técnico, extraia:

- Conceitos ou definições (ex: "equipamento é definido como...")
- Sequência de atividades ou processos (ex: "primeiro faz-se X, depois Y")
- Atores envolvidos (ex: "técnico", "responsável", "operador")
- Artefatos citados (ex: "manual", "equipamento", "sistema")

Formate a resposta em JSON com os campos: "conceitos", "processos", "atores", "artefatos".

Texto:
{texto}
"""

# Chamada à API do Gemini para cada bloco
def gerar_extracao_gemini_por_bloco(blocos):
    modelo = genai.GenerativeModel("gemini-1.5-flash")  # Use "gemini-1.5-pro" se quiser mais precisão
    resultados = []

    for i, bloco in enumerate(blocos):
        prompt = gerar_prompt(bloco)
        try:
            print(f"Processando bloco {i + 1}/{len(blocos)}...")
            resposta = modelo.generate_content(prompt)
            resultados.append(resposta.text)
            time.sleep(1.5)  # Evita limite de rate da API
        except Exception as e:
            print(f"Erro no bloco {i + 1}: {e}")
            resultados.append(None)
    return resultados

# Limpa marcações Markdown (```json ... ```) da resposta
def limpar_json_bruto(texto):
    texto_limpo = re.sub(r"```json\s*", "", texto, flags=re.IGNORECASE)
    texto_limpo = re.sub(r"```", "", texto_limpo)
    return texto_limpo.strip()

# Junta os blocos em um único JSON com 4 categorias
def combinar_resultados_json(resultados):
    dados_finais = {
        "conceitos": [],
        "processos": [],
        "atores": [],
        "artefatos": []
    }

    for res in resultados:
        if not res:
            continue
        try:
            json_texto = limpar_json_bruto(res)
            dados = json.loads(json_texto)
            for chave in dados_finais:
                if isinstance(dados.get(chave), list):
                    dados_finais[chave].extend(dados.get(chave, []))
        except json.JSONDecodeError as e:
            print("Erro ao converter para JSON:", e)
            print("Texto bruto:", res[:500])
    return dados_finais

# Execução principal
if __name__ == "__main__":
    pasta_pdfs = "pdfs"  # nome da pasta com os PDFs
    if not os.path.exists(pasta_pdfs):
        print(f"Pasta '{pasta_pdfs}' não encontrada.")
        exit(1)

    arquivos_pdf = [f for f in os.listdir(pasta_pdfs) if f.lower().endswith('.pdf')]
    if not arquivos_pdf:
        print(f"Nenhum PDF encontrado na pasta '{pasta_pdfs}'.")
        exit(1)

    for nome_pdf in arquivos_pdf:
        caminho_pdf = os.path.join(pasta_pdfs, nome_pdf)
        print(f"\nProcessando: {nome_pdf}")
        texto = extrair_texto_pdf(caminho_pdf)
        blocos = dividir_texto(texto)
        resultados_brutos = gerar_extracao_gemini_por_bloco(blocos)
        resultado_final = combinar_resultados_json(resultados_brutos)

        nome_saida = f"extracao_estruturada_{os.path.splitext(nome_pdf)[0]}.json"
        with open(nome_saida, "w", encoding="utf-8") as f:
            json.dump(resultado_final, f, ensure_ascii=False, indent=2)
        print(f"Resultado salvo em: {nome_saida}")
