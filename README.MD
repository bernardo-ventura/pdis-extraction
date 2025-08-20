# 🛠️ Extração e Classificação de Termos Técnicos de PDIs com Mapeamento OSDU

Este projeto realiza **extração e classificação de termos técnicos da indústria de óleo e gás** a partir de **Planos de Descomissionamento de Instalações (PDIs)**, classificando-os e mapeando-os para esquemas **OSDU (Open Subsurface Data Universe)**.

---

## 📂 Estrutura do Projeto

```
├── .env                       # Arquivo de variáveis de ambiente
├── pdfs/                      # Pasta com os PDFs de entrada
├── extracted-data/            # Dados extraídos dos PDFs
├── data-definitions/          # Definições de esquemas OSDU
│   └── SchemaRegistrationResources/
├── extrair_termos.py
├── agrupar_termos.py
├── filtrar_elementos_recorrentes.py
├── classificar_termos.py
├── mapear_termos_osdu.py
└── extrair_osdu.py
```

---

## 🧭 Resumo do Workflow

O projeto executa um pipeline de processamento para transformar documentos técnicos (PDIs) em dados estruturados e mapeados para padrões internacionais (OSDU). O fluxo segue estas etapas principais:

1. **Extração**: Os termos técnicos são extraídos automaticamente dos PDFs dos PDIs.
2. **Agrupamento**: Termos similares são agrupados para eliminar redundâncias e padronizar nomenclatura.
3. **Filtragem**: Apenas os termos recorrentes e relevantes são mantidos para análise.
4. **Classificação**: Cada termo é classificado em uma área temática (ambiental, técnico, social, etc.) usando IA.
5. **Indexação dos Schemas OSDU**: Os metadados dos esquemas OSDU são extraídos e organizados para consulta.
6. **Mapeamento**: Os termos classificados são relacionados aos schemas OSDU mais adequados, facilitando integração e interoperabilidade.

O resultado final é um conjunto de arquivos JSON que representam o conhecimento técnico dos PDIs, pronto para ser utilizado em sistemas, análises ou integrações com plataformas OSDU.

---

## 📥 Download dos Schemas OSDU

Para executar o pipeline, é necessário baixar os arquivos de schemas OSDU.  
Baixe o conteúdo do repositório oficial [osdu/schema](https://community.opengroup.org/osdu/data/data-definitions) 

```bash
git clone https://community.opengroup.org/osdu/data/data-definitions.git
```

A única pasta utilizada dentro de data-definitions é a SchemaRegistrationResources/shared-schemas/osdu,
são desses arquivos que extraímos os termos da OSDU. Então, as outras pastas de data-definitions podem ser deletadas

Como fazer isso rapidamente:

Você pode rodar algo assim no terminal (a partir da raiz do seu projeto):

```bash
cd data-definitions
rm -rf Authoring Examples Generated E-R Guides ReferenceValues *.md *.yml .git* pom.xml mvnw*
```

Ou fazer isso direto pelo VS Code, com Delete nas pastas/arquivos não utilizados.

Se preferir, baixe manualmente e coloque na estrutura indicada acima.

---

## 🔑 Configuração da API Gemini

Todos os scripts que utilizam IA generativa (extração, classificação, mapeamento) dependem da configuração da API Gemini. Para isso, é necessário:

1. Criar um arquivo `.env` na raiz do projeto com sua chave:
   ```
   GEMINI_API_KEY=seu_token_aqui
   ```

2. No início do script, carregar e configurar a chave:
   ```python
   from dotenv import load_dotenv
   import os
   import google.generativeai as genai

   load_dotenv()
   api_key = os.getenv("GEMINI_API_KEY")
   genai.configure(api_key=api_key)
   ```

> **Nota:** Consulte esta seção sempre que um script mencionar configuração da API Gemini.

---

## 🚀 Etapas Detalhadas


## Extração de Termos Técnicos de PDIs (`extrair_termos.py`)

O script `extrair_termos.py` é o ponto de entrada do pipeline de processamento, responsável por extrair termos técnicos estruturados a partir de Planos de Descomissionamento de Instalações (PDIs) em formato PDF.

### Objetivo

O script analisa documentos PDF para identificar e extrair automaticamente:
- **Conceitos/definições** técnicas
- **Processos/atividades** sequenciais
- **Atores** envolvidos nas operações
- **Artefatos** físicos ou documentais mencionados

### Dependências e Configuração

```python
import fitz  # PyMuPDF para extração de texto de PDFs
import google.generativeai as genai  # API Gemini do Google
from dotenv import load_dotenv
import os, json, time, re
```

O script utiliza:
- **PyMuPDF (fitz)**: biblioteca de alto desempenho para leitura de PDFs
- **Google Generative AI**: API Gemini para processamento de linguagem natural
- **python-dotenv**: para gerenciar a chave da API de forma segura

Este script utiliza a configuração da API Gemini conforme descrito em Configuração da API Gemini.

### Processo de Extração

#### 1. Extração de Texto dos PDFs

```python
def extrair_texto_pdf(caminho_pdf):
    doc = fitz.open(caminho_pdf)
    texto = ""
    for pagina in doc:
        texto += pagina.get_text()
    return texto
```

Esta função abre cada página do PDF e extrai seu conteúdo textual, concatenando-o em uma única string.

#### 2. Divisão em Blocos Processáveis

```python
def dividir_texto(texto, tamanho_max=8000):
    return [texto[i:i+tamanho_max] for i in range(0, len(texto), tamanho_max)]
```

Como os PDIs são documentos extensos e os modelos de IA têm limitações de tamanho de contexto, o texto é dividido em blocos de ~8000 caracteres para processamento individual.

#### 3. Geração de Prompts Especializados

```python
def gerar_prompt(texto):
    return f"""
A partir do seguinte texto técnico, extraia:

- Conceitos ou definições (ex: \"equipamento é definido como...\")
- Sequência de atividades ou processos (ex: \"primeiro faz-se X, depois Y\")
- Atores envolvidos (ex: \"técnico\", \"responsável\", \"operador\")
- Artefatos citados (ex: \"manual\", \"equipamento\", \"sistema\")

Formate a resposta em JSON com os campos: "conceitos", "processos", "atores", "artefatos".

Texto:
{texto}
"""
```

Esta função cria instruções específicas para a API Gemini, solicitando a extração das quatro categorias de informação e definindo o formato JSON esperado para a resposta.

#### 4. Processamento com IA Generativa

```python
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
```

Para cada bloco de texto:
- Cria um prompt específico
- Envia para o modelo Gemini 1.5 Flash (modelo de alta velocidade)
- Armazena a resposta
- Inclui pausas (1.5s) para evitar exceder limites de taxa da API

#### 5. Limpeza e Processamento das Respostas

```python
def limpar_json_bruto(texto):
    texto_limpo = re.sub(r"```json\\s*", "", texto, flags=re.IGNORECASE)
    texto_limpo = re.sub(r"```", "", texto_limpo)
    return texto_limpo.strip()
```

A API Gemini frequentemente retorna JSON em formato Markdown (entre delimitadores ```json). Esta função remove essas marcações para permitir o parsing do JSON.

#### 6. Combinação dos Resultados

```python
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
```

Esta função:
- Cria um dicionário estruturado para as quatro categorias
- Para cada resposta da API:
  - Limpa o formato Markdown
  - Converte para objeto Python
  - Adiciona os elementos de cada categoria ao dicionário final
- Trata erros de parsing JSON, exibindo diagnósticos úteis

### Execução Principal

```python
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
```

O fluxo de execução completo:
1. Verifica a existência da pasta "pdfs"
2. Lista todos os arquivos PDF na pasta
3. Para cada PDF:
   - Extrai o texto completo
   - Divide em blocos gerenciáveis
   - Processa cada bloco com a API Gemini
   - Combina os resultados em um único conjunto de dados
   - Salva como JSON estruturado

### Arquivo de Saída

O script gera arquivos `extracao_estruturada_[nome_do_pdf].json` com a seguinte estrutura:

```json
{
  "conceitos": [
    "Descomissionamento: Processo de desativação permanente de instalações...",
    "Abandono: Ato de deixar permanentemente uma instalação sem uso..."
  ],
  "processos": [
    "Remoção de equipamentos submarinos: Primeiro mobiliza-se a embarcação...",
    "Limpeza de dutos: Inicialmente realiza-se a lavagem com água..."
  ],
  "atores": [
    "Operador",
    "Agência Nacional do Petróleo",
    "Especialista ambiental"
  ],
  "artefatos": [
    "Manifold",
    "Plano de Descomissionamento",
    "Dutos flexíveis"
  ]
}
```

Estes arquivos JSON são a entrada para as etapas subsequentes do pipeline de processamento.

## Agrupamento de Termos Técnicos Extraídos (`agrupar_termos.py`)

O script `agrupar_termos.py` é responsável por consolidar e agrupar os termos extraídos dos PDIs, identificando variações de escrita e redundâncias por meio de fuzzy matching. O objetivo é gerar grupos de termos equivalentes para facilitar análises posteriores.

### Objetivo

- Agrupar termos similares (mesmo conceito, escrita diferente)
- Reduzir redundância e padronizar nomenclatura
- Gerar estatísticas de ocorrência dos termos

### Dependências e Configuração

```python
import os
import json
import unicodedata
from rapidfuzz import fuzz, process
```

O script utiliza:
- **rapidfuzz**: biblioteca eficiente para fuzzy matching (correspondência aproximada de strings)
- **unicodedata**: para normalização de acentuação

### Processo de Agrupamento

#### 1. Carregamento dos Termos

```python
PASTA_JSONS = "extracted-data"
CATEGORIAS = ["conceitos", "processos", "artefatos", "atores"]

# Carrega todos os elementos
elementos = {cat: [] for cat in CATEGORIAS}
arquivos = [f for f in os.listdir(PASTA_JSONS) if f.endswith(".json")]
for nome_arquivo in arquivos:
    caminho = os.path.join(PASTA_JSONS, nome_arquivo)
    with open(caminho, "r", encoding="utf-8") as f:
        dados = json.load(f)
        for cat in CATEGORIAS:
            elementos[cat].extend(dados.get(cat, []))
```

O script percorre todos os arquivos JSON gerados na etapa anterior e carrega os termos de cada categoria.

#### 2. Normalização dos Termos

```python
def normalizar(texto):
    texto = texto.lower()
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    texto = ''.join(c for c in texto if c.isalnum() or c.isspace())
    texto = ' '.join(texto.split())
    return texto
```

A função `normalizar` padroniza os termos para facilitar a comparação:
- Converte para minúsculas
- Remove acentos
- Elimina caracteres especiais
- Normaliza espaços

#### 3. Agrupamento por Similaridade (Fuzzy Matching)

```python
LIMIAR_SIMILARIDADE = 90  # Percentual para considerar elementos semelhantes

for cat in CATEGORIAS:
    for elem in elementos[cat]:
        # Garante que elem é string
        if isinstance(elem, dict):
            elem_str = elem.get("nome", "")
        elif isinstance(elem, str):
            elem_str = elem
        else:
            continue
        if not elem_str.strip():
            continue
        elem_norm = normalizar(elem_str)
        match = process.extractOne(elem_norm, [g[0] for g in grupos[cat]], scorer=fuzz.token_sort_ratio)
        if match and match[1] >= LIMIAR_SIMILARIDADE:
            idx = match[2]
            grupos[cat][idx][1].append(elem_str)
        else:
            grupos[cat].append([elem_norm, [elem_str]])
```

Para cada termo:
- Normaliza o texto
- Compara com os grupos já formados usando fuzzy matching (`token_sort_ratio`)
- Se a similaridade for maior ou igual ao limiar (90%), adiciona ao grupo existente
- Caso contrário, cria um novo grupo

#### 4. Contagem e Estatísticas

```python
for cat in CATEGORIAS:
    for grupo in grupos[cat]:
        contagem[cat].append({
            "grupo_normalizado": grupo[0],
            "exemplos": list(set(grupo[1])),
            "quantidade": len(grupo[1])
        })
```

Para cada grupo, registra:
- Termo normalizado
- Exemplos originais encontrados
- Quantidade de ocorrências

#### 5. Saída dos Resultados

```python
with open("grupos_agrupados.json", "w", encoding="utf-8") as f:
    json.dump(contagem, f, ensure_ascii=False, indent=2)
```

O resultado é salvo em `grupos_agrupados.json`, contendo os grupos de termos similares e suas estatísticas de ocorrência.

### Arquivo de Saída

O arquivo gerado tem a seguinte estrutura:

```json
{
  "conceitos": [
    {
      "grupo_normalizado": "descomissionamento",
      "exemplos": ["Descomissionamento", "Descomissionamento de Instalações"],
      "quantidade": 12
    },
    // ...
  ],
  "processos": [ ... ],
  "artefatos": [ ... ],
  "atores": [ ... ]
}
```

Cada grupo representa um conjunto de termos equivalentes, facilitando análises, visualizações e etapas posteriores do pipeline.

## Filtragem de Elementos Recorrentes (`filtrar_elementos_recorrentes.py`)

O script `filtrar_elementos_recorrentes.py` tem como objetivo identificar e manter apenas os termos que aparecem de forma recorrente nos PDIs, eliminando padrões pouco relevantes ou termos que ocorrem isoladamente. Isso garante que as próximas etapas do pipeline trabalhem apenas com elementos representativos.

### Objetivo

- Filtrar grupos de termos para manter apenas os que aparecem com frequência significativa
- Reduzir ruído e focar em padrões recorrentes

### Dependências

```python
import json
```

### Processo de Filtragem

#### 1. Definição do Limiar de Recorrência

```python
LIMIAR_RECORRENCIA = 3  # Elementos com quantidade >= 3 serão mantidos
```

O limiar define o número mínimo de ocorrências para que um termo seja considerado recorrente. Pode ser ajustado conforme a necessidade do projeto.

#### 2. Carregamento dos Grupos Agrupados

```python
with open("grupos_agrupados.json", "r", encoding="utf-8") as f:
    dados = json.load(f)
```

O script lê o arquivo `grupos_agrupados.json` gerado na etapa anterior, que contém todos os grupos de termos e suas estatísticas de ocorrência.

#### 3. Filtragem dos Elementos

```python
filtrados = {}
for categoria, grupos in dados.items():
    filtrados[categoria] = []
    for grupo in grupos:
        if grupo.get("quantidade", 0) >= LIMIAR_RECORRENCIA:
            filtrados[categoria].append(grupo)
```

Para cada grupo, verifica se a quantidade de ocorrências é maior ou igual ao limiar. Apenas esses grupos são mantidos.

#### 4. Estatísticas de Filtragem

O script exibe estatísticas sobre o número de elementos mantidos e filtrados, auxiliando na avaliação do impacto do limiar escolhido.

```python
print(f"Total de elementos filtrados (quantidade < {LIMIAR_RECORRENCIA}): {elementos_filtrados}")
print(f"Total de elementos mantidos (padrões recorrentes): {elementos_mantidos}")
```

#### 5. Saída dos Resultados

```python
with open("elementos_recorrentes.json", "w", encoding="utf-8") as f:
    json.dump(filtrados, f, ensure_ascii=False, indent=2)
```

O resultado é salvo em `elementos_recorrentes.json`, contendo apenas os grupos de termos recorrentes.

### Arquivo de Saída

O arquivo gerado tem a seguinte estrutura:

```json
{
  "conceitos": [
    {
      "grupo_normalizado": "descomissionamento",
      "exemplos": ["Descomissionamento", "Descomissionamento de Instalações"],
      "quantidade": 12
    },
    // ...
  ],
  "processos": [ ... ],
  "artefatos": [ ... ],
  "atores": [ ... ]
}
```

Apenas os grupos com quantidade maior ou igual ao limiar são mantidos, tornando o conjunto de dados mais robusto para classificação e mapeamento.

## Classificação Temática dos Termos (`classificar_termos.py`)

O script `classificar_termos.py` é responsável por atribuir uma área temática a cada termo recorrente extraído dos PDIs, utilizando IA generativa para garantir uma classificação precisa e padronizada.

### Objetivo

- Classificar cada termo em uma área temática relevante
- Padronizar a categorização para facilitar análises e mapeamento

### Dependências e Configuração

```python
import json
import os
import google.generativeai as genai
from dotenv import load_dotenv
import time
```

O script utiliza:
- **Google Generative AI**: API Gemini para classificação automática
- **python-dotenv**: para gerenciar a chave da API

Este script utiliza a configuração da API Gemini conforme descrito em Configuração da API Gemini.


### Processo de Classificação

#### 1. Carregamento dos Termos Recorrentes

```python
arquivo_entrada = "elementos_recorrentes.json"
with open(arquivo_entrada, "r", encoding="utf-8") as f:
    dados = json.load(f)
```

O script lê o arquivo `elementos_recorrentes.json` gerado na etapa anterior, contendo apenas os termos recorrentes.

#### 2. Classificação com IA Generativa

```python
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
    Termo: \"{termo}\"
    Responda apenas com o nome da área, sem explicações adicionais.
    """
    modelo = genai.GenerativeModel("gemini-1.5-flash")
    resposta = modelo.generate_content(prompt)
    area = resposta.text.strip().lower()
    # Verifica se a resposta é uma das áreas válidas
    areas_validas = ["ambiental", "social", "saúde e segurança", "gerenciamento de resíduos", "econômico", "técnico", "indefinido"]
    if area not in areas_validas:
        for area_valida in areas_validas:
            if area_valida in area:
                area = area_valida
                break
        else:
            area = "indefinido"
    return area
```

Para cada termo, o script:
- Gera um prompt específico para classificação
- Envia para o modelo Gemini
- Normaliza e valida a resposta
- Garante que a área seja uma das opções padronizadas

#### 3. Processamento das Categorias

```python
for categoria in resultado.keys():
    for item in dados.get(categoria, []):
        termo = item.get("grupo_normalizado", "")
        area = classificar_termo(termo)
        resultado[categoria].append({
            "termo": termo,
            "area": area
        })
        time.sleep(1.5)  # Pausa para evitar limites de rate da API
```

O script percorre todas as categorias e classifica cada termo recorrente, armazenando o resultado em uma estrutura organizada.

#### 4. Tratamento de Erros

Em caso de erro na classificação, o termo é marcado como "indefinido" e o script faz uma pausa maior para evitar bloqueios da API.

#### 5. Saída dos Resultados

```python
with open(arquivo_saida, "w", encoding="utf-8") as f:
    json.dump(resultado, f, ensure_ascii=False, indent=2)
```

O resultado é salvo em `termos_classificados.json`, contendo cada termo e sua área temática.

### Arquivo de Saída

O arquivo gerado tem a seguinte estrutura:

```json
{
  "conceitos": [
    { "termo": "descomissionamento", "area": "técnico" },
    { "termo": "licenciamento ambiental", "area": "ambiental" }
  ],
  "processos": [ ... ],
  "artefatos": [ ... ],
  "atores": [ ... ]
}
```

Cada termo recorrente é classificado em uma área temática, facilitando o mapeamento para esquemas OSDU e análises setoriais.

## Extração de Metadados dos Schemas OSDU (`extrair_osdu.py`)

O script `extrair_osdu.py` é responsável por percorrer todos os arquivos de schema OSDU presentes na pasta de definições e extrair metadados relevantes de cada um, consolidando essas informações em um arquivo texto para indexação, consulta ou debug.

### Objetivo

- Extrair e consolidar metadados dos schemas OSDU
- Facilitar o mapeamento de termos técnicos para esquemas OSDU
- Gerar um arquivo de referência para consulta rápida

### Dependências e Configuração

```python
import os
import json
from pathlib import Path
```

### Processo de Extração

#### 1. Definição do Caminho dos Schemas

```python
SCHEMAS_PATH = Path("data-definitions/SchemaRegistrationResources/shared-schemas/osdu")
```

O script define o caminho para a pasta onde estão os arquivos de schema OSDU.

#### 2. Iteração e Extração dos Metadados

```python
for json_path in SCHEMAS_PATH.rglob("*.json"):
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    schema = data.get("schema", data)
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
    if title or description or prop_names:
        documentos.append(texto.strip())
```

Para cada arquivo JSON:
- Abre e carrega o conteúdo
- Busca os campos relevantes: `kind`, `title`, `description`, `properties`
- Formata os dados em texto estruturado
- Adiciona à lista de documentos se houver informações relevantes

#### 3. Salvamento dos Resultados

```python
with open("documentos_osdu.txt", "w", encoding="utf-8") as f:
    for doc in documentos:
        f.write(doc + "\n---\n")
```

O resultado é salvo em `documentos_osdu.txt`, com cada documento separado por `---` para facilitar a leitura e indexação.

### Arquivo de Saída

O arquivo gerado tem a seguinte estrutura:

```
Kind: wks:reference-data--GCMSMSCompounds:1.0.0
Title: GCMSMSCompounds
Description: Chemical compounds identified through the GCMSMS method of fluid analysis.
Properties: id, kind, version, acl, legal, tags, createTime, createUser, modifyTime, modifyUser, ancestry, meta, data
File: GCMSMSCompounds.1.0.0.json
---
Kind: wks:master-data--GeoPoliticalEntity:1.1.0
Title: GeoPoliticalEntity
Description: A named geographical area which is defined and administered by an official entity.
Properties: id, kind, version, acl, legal, tags, createTime, createUser, modifyTime, modifyUser, ancestry, meta, data
File: GeoPoliticalEntity.1.1.0.json
---
```

Cada bloco representa um schema OSDU, facilitando o mapeamento e consulta dos termos técnicos extraídos dos PDIs.

## Mapeamento de Termos para Schemas OSDU (`mapear_termos_osdu.py`)

O script `mapear_termos_osdu.py` realiza o mapeamento dos termos classificados para os schemas OSDU mais relevantes, utilizando embeddings semânticos e cálculo de similaridade para sugerir os melhores matches.

### Objetivo

- Relacionar cada termo técnico extraído dos PDIs com os schemas OSDU mais similares
- Sugerir alternativas de mapeamento e indicar casos que requerem revisão manual

### Dependências e Configuração

```python
import json
import os
import math
from dotenv import load_dotenv
import google.generativeai as genai
```

O script utiliza:
- **Google Generative AI**: para geração de embeddings semânticos
- **python-dotenv**: para gerenciar a chave da API

Este script utiliza a configuração da API Gemini conforme descrito em Configuração da API Gemini.

### Processo de Mapeamento

#### 1. Carregamento dos Schemas OSDU

```python
def carregar_schemas_osdu(arquivo_txt):
    # ...
    with open(arquivo_txt, 'r', encoding='utf-8') as f:
        conteudo = f.read()
    schemas_raw = conteudo.split('---')
    # ...
```

O script lê o arquivo `documentos_osdu.txt` e estrutura os schemas para processamento.

#### 2. Geração de Embeddings

```python
def gerar_embedding(texto):
    embedding = genai.embed_content(
        model="models/embedding-001",
        content=texto,
        task_type="retrieval_document"
    )
    return embedding["embedding"]
```

Para cada termo expandido e cada schema, o script gera embeddings semânticos usando a API Gemini.

#### 3. Expansão de Contexto dos Termos

```python
def expandir_contexto_termo(termo, area):
    # ...
    return f"{termo} - {contexto_area}"
```

O contexto do termo é expandido conforme sua área temática para melhorar a precisão do mapeamento.

#### 4. Cálculo de Similaridade

A similaridade de cosseno é uma métrica que avalia o quão próximos dois vetores estão em um espaço multidimensional, ignorando o tamanho absoluto dos vetores e focando apenas na direção. No contexto deste projeto, cada termo e cada schema OSDU são convertidos em vetores numéricos (embeddings) que representam seu significado semântico.

O cálculo é feito assim:

```python
def cosine_similarity(v1, v2):
    dot_product = sum(x*y for x, y in zip(v1, v2))
    mag1 = math.sqrt(sum(x*x for x in v1))
    mag2 = math.sqrt(sum(y*y for y in v2))
    return dot_product / (mag1 * mag2)
```

- **dot_product**: soma dos produtos dos elementos correspondentes dos dois vetores.
- **mag1** e **mag2**: magnitude (comprimento) de cada vetor.
- O resultado é um valor entre -1 e 1, onde:
  - **1** indica máxima similaridade (mesma direção)
  - **0** indica vetores ortogonais (sem relação)
  - **-1** indica direções opostas (não utilizado aqui)

No pipeline, quanto maior o valor da similaridade de cosseno entre o embedding do termo e o embedding do schema OSDU, mais próximo semanticamente eles são. Assim, os schemas com maior score são sugeridos como os melhores candidatos para mapeamento do termo.

#### 5. Mapeamento dos Termos

```python
def mapear_termos_para_schemas(termos, schemas):
    # ...
    for categoria in resultados.keys():
        for item in termos.get(categoria, []):
            # ...
            termo_expandido = expandir_contexto_termo(termo, area)
            termo_embedding = gerar_embedding(termo_expandido)
            # ...
            similaridades = [cosine_similarity(termo_embedding, emb) for emb in schema_embeddings]
            # ...
            top_indices = sorted(range(len(similaridades)), key=lambda i: similaridades[i], reverse=True)[:TOP_SCHEMAS]
            # ...
```

Para cada termo, o script:
- Expande o contexto
- Gera embedding
- Calcula similaridade com todos os schemas
- Seleciona os TOP_SCHEMAS mais similares
- Indica se o mapeamento requer revisão manual (score baixo)

#### 6. Saída dos Resultados

```python
with open(arquivo_saida, 'w', encoding='utf-8') as f:
    json.dump(resultados, f, ensure_ascii=False, indent=2)
```

O resultado é salvo em `termos_mapeados_osdu.json`, contendo para cada termo:
- Alternativas de schemas OSDU
- Score de similaridade
- Indicação de revisão manual
- Metadados do melhor match

### Arquivo de Saída

O arquivo gerado tem a seguinte estrutura:

```json
{
  "processos": [
    {
      "termo": "gcmsms",
      "area": "técnico",
      "termo_expandido": "gcmsms - relacionado a equipamentos, processos, procedimentos técnicos da indústria de óleo e gás",
      "alternativas": [
        {
          "posicao": 1,
          "osdu_kind": "wks:reference-data--GCMSMSCompounds:1.0.0",
          "osdu_title": "GCMSMSCompounds",
          "osdu_description": "Chemical compounds identified through the GCMSMS method of fluid analysis.",
          "osdu_properties": "id, kind, version, acl, legal, tags, ...",
          "osdu_file": "GCMSMSCompounds.1.0.0.json",
          "similaridade": 0.73
        },
        // ...
      ],
      "requer_revisao": false,
      "osdu_kind": "wks:reference-data--GCMSMSCompounds:1.0.0",
      "osdu_title": "GCMSMSCompounds",
      "osdu_description": "Chemical compounds identified through the GCMSMS method of fluid analysis.",
      "osdu_properties": "id, kind, version, acl, legal, tags, ...",
      "osdu_file": "GCMSMSCompounds.1.0.0.json",
      "similaridade": 0.73
    },
    // ...
  ],
  "conceitos": [ ... ],
  "artefatos": [ ... ],
  "atores": [ ... ]
}
```

Cada termo é mapeado para os schemas OSDU mais similares, com transparência sobre a confiança do mapeamento e alternativas para revisão.
