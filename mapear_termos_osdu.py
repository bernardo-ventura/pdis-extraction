import json
import os
import math
from dotenv import load_dotenv
import google.generativeai as genai

# Carrega variáveis do .env
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# Configurações
LIMIAR_CONFIANCA = 0.6  # Score mínimo para considerar confiável
TOP_SCHEMAS = 3  # Número de schemas mais similares a retornar

def carregar_schemas_osdu(arquivo_txt):
    """Carrega e estrutura schemas OSDU do arquivo de texto"""
    print(f"Carregando schemas OSDU de {arquivo_txt}...")
    with open(arquivo_txt, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    
    schemas_raw = conteudo.split('---')
    schemas = []
    
    for schema_text in schemas_raw:
        if not schema_text.strip():
            continue
        
        schema = {}
        linhas = schema_text.strip().split('\n')
        
        for linha in linhas:
            if ': ' in linha:
                chave, valor = linha.split(': ', 1)
                schema[chave] = valor
        
        # Cria texto para embedding
        schema['texto_completo'] = f"Kind: {schema.get('Kind', '')} Title: {schema.get('Title', '')} Description: {schema.get('Description', '')}"
        
        schemas.append(schema)
    
    print(f"Carregados {len(schemas)} schemas OSDU")
    return schemas

def cosine_similarity(v1, v2):
    """Calcula similaridade de cosseno sem dependências externas"""
    dot_product = sum(x*y for x, y in zip(v1, v2))
    mag1 = math.sqrt(sum(x*x for x in v1))
    mag2 = math.sqrt(sum(y*y for y in v2))
    if mag1 * mag2 == 0:
        return 0
    return dot_product / (mag1 * mag2)

def gerar_embedding(texto):
    """Gera embedding para um texto usando a API correta"""
    # Usar a API de embeddings do Google
    embedding = genai.embed_content(
        model="models/embedding-001",
        content=texto,
        task_type="retrieval_document"
    )
    return embedding["embedding"]

def expandir_contexto_termo(termo, area):
    """Expande o contexto do termo com base na área"""
    contextos = {
        "ambiental": "relacionado ao meio ambiente, licenciamento ambiental, proteção ambiental",
        "social": "relacionado a impactos sociais, comunidades, aspectos socioeconômicos",
        "saúde e segurança": "relacionado a segurança do trabalho, saúde ocupacional, prevenção de riscos",
        "gerenciamento de resíduos": "relacionado a gestão, tratamento e disposição de resíduos",
        "econômico": "relacionado a custos, benefícios econômicos, viabilidade financeira", 
        "técnico": "relacionado a equipamentos, processos, procedimentos técnicos da indústria de óleo e gás"
    }
    
    # Obter contexto para a área ou usar um padrão
    contexto_area = contextos.get(area, "termo técnico da indústria de óleo e gás")
    
    # Retornar termo expandido
    return f"{termo} - {contexto_area}"

def mapear_termos_para_schemas(termos, schemas):
    """Mapeia cada termo para os schemas mais similares"""
    print("Mapeando termos para schemas OSDU...")
    resultados = {
        "conceitos": [],
        "processos": [],
        "artefatos": [],
        "atores": []
    }
    
    # Verificar se há termos para processar
    total_termos = sum(len(termos.get(cat, [])) for cat in resultados.keys())
    print(f"Total de termos para processar: {total_termos}")
    
    # Calcular embeddings para todos os schemas
    print("Calculando embeddings para schemas...")
    schema_embeddings = []
    batch_size = 10
    
    for i in range(0, len(schemas), batch_size):
        batch = schemas[i:min(i+batch_size, len(schemas))]
        print(f"Processando schemas {i+1}-{i+len(batch)} de {len(schemas)}")
        
        for schema in batch:
            try:
                embedding = gerar_embedding(schema['texto_completo'])
                schema_embeddings.append(embedding)
            except Exception as e:
                print(f"Erro ao gerar embedding para schema: {e}")
                # Adicionar embedding vazio para manter índices alinhados
                schema_embeddings.append([0] * 768)  # Dimensão típica de embeddings
    
    # Processar todos os termos
    for categoria in resultados.keys():
        items = termos.get(categoria, [])
        print(f"Processando categoria: {categoria} ({len(items)} itens)")
        
        for idx, item in enumerate(items):
            termo = item.get("termo", "")
            area = item.get("area", "")
            
            if not termo:
                continue
                
            # Mostrar progresso periodicamente
            if idx % 10 == 0:
                print(f"Processando termo {idx+1}/{len(items)} em {categoria}...")
            
            # Expandir contexto do termo
            termo_expandido = expandir_contexto_termo(termo, area)
            
            try:
                # Gerar embedding para o termo expandido
                termo_embedding = gerar_embedding(termo_expandido)
                
                # Calcular similaridade com todos os schemas
                similaridades = []
                for emb in schema_embeddings:
                    sim = cosine_similarity(termo_embedding, emb)
                    similaridades.append(sim)
                
                # Encontrar os top schemas mais similares
                top_indices = sorted(range(len(similaridades)), key=lambda i: similaridades[i], reverse=True)[:TOP_SCHEMAS]
                top_scores = [similaridades[i] for i in top_indices]
                top_schemas = [schemas[i] for i in top_indices]
                
                # Adicionar mapeamento ao resultado
                item_mapeado = item.copy()
                item_mapeado.update({
                    "termo_expandido": termo_expandido,
                    "alternativas": [],
                    "requer_revisao": top_scores[0] < LIMIAR_CONFIANCA
                })
                
                # Adicionar as alternativas
                for i, (schema, score) in enumerate(zip(top_schemas, top_scores)):
                    schema_info = {
                        "posicao": i + 1,
                        "osdu_kind": schema.get("Kind", ""),
                        "osdu_title": schema.get("Title", ""),
                        "osdu_description": schema.get("Description", ""),
                        "osdu_properties": schema.get("Properties", ""),
                        "osdu_file": schema.get("File", ""),
                        "similaridade": float(score)
                    }
                    item_mapeado["alternativas"].append(schema_info)
                
                # Para compatibilidade com o formato anterior, copiamos o melhor match também para a raiz
                melhor_match = item_mapeado["alternativas"][0]
                for key in melhor_match:
                    if key != "posicao":
                        item_mapeado[key] = melhor_match[key]
                
                resultados[categoria].append(item_mapeado)
                
                # Mostrar alertas para scores baixos
                if item_mapeado["requer_revisao"] and idx % 10 == 0:
                    print(f"  ⚠️ Termo '{termo}' tem score baixo: {top_scores[0]:.4f}")
                
            except Exception as e:
                print(f"Erro ao processar termo '{termo[:30]}...': {e}")
                # Adicionar item sem mapeamento OSDU
                item_mapeado = item.copy()
                item_mapeado.update({
                    "erro": str(e)
                })
                resultados[categoria].append(item_mapeado)
    
    return resultados

def main():
    # Configuração de arquivos
    arquivo_termos = "termos_classificados.json"
    arquivo_schemas = "documentos_osdu.txt"
    arquivo_saida = "termos_mapeados_osdu.json"
    
    # Carregar termos classificados
    print(f"Carregando termos de {arquivo_termos}...")
    try:
        with open(arquivo_termos, 'r', encoding='utf-8') as f:
            termos = json.load(f)
        print("Arquivo de termos carregado com sucesso.")
    except Exception as e:
        print(f"ERRO ao carregar {arquivo_termos}: {e}")
        return
    
    # Carregar e processar schemas OSDU
    schemas = carregar_schemas_osdu(arquivo_schemas)
    
    # Mapear termos para schemas
    resultados = mapear_termos_para_schemas(termos, schemas)
    
    # Salvar resultados
    print(f"Salvando resultados em {arquivo_saida}...")
    with open(arquivo_saida, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, ensure_ascii=False, indent=2)
    
    print("Mapeamento concluído com sucesso!")

if __name__ == "__main__":
    main()