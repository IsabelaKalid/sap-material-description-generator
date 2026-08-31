import os
import re
import time
from datetime import datetime
from difflib import get_close_matches

import pandas as pd
from tqdm import tqdm
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import HumanMessage

# =====================================================
# CONFIGURAÇÃO DE IA (Utilizando Variáveis de Ambiente)
# AI CONFIGURATION (Using Environment Variables)
# =====================================================

AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "YOUR_API_KEY_HERE")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "https://your-azure-openai-endpoint.openai.azure.com/")
AZURE_DEPLOYMENT_NAME = os.getenv("AZURE_DEPLOYMENT_NAME", "your-deployment-name")

llm = AzureChatOpenAI(
    azure_deployment=AZURE_DEPLOYMENT_NAME,
    openai_api_version="2024-08-01-preview",
    api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    temperature=0
)

# =====================================================
# CAMINHOS DOS ARQUIVOS (Caminhos relativos/genéricos)
# FILE PATHS (Relative/generic paths)
# =====================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

arquivo_excel = os.path.join(BASE_DIR, "data", "ASINS_PARA_CADASTRO.xlsx")
arquivo_exemplos = os.path.join(BASE_DIR, "data", "exemplos_descricoes.xlsx")

# SUFIXO GENÉRICO DE CADASTRO (Substituído o padrão interno)
# GENERIC REGISTRATION SUFFIX (Replaced internal pattern)
SUFIXO_CADASTRO = "A-ERP"

# =====================================================
# TABELA DE CORES/ACABAMENTOS (baseada no histórico real)
# COLOR/FINISH TABLE (based on real historical data)
# =====================================================

TABELA_CORES = """
PT=PRETO      BR=BRANCO     AZ=AZUL       RO=ROSA       CZ=CINZA
VD=VERDE      AM=AMARELO    MR=MARROM     VM=VERMELHO   LR=LARANJA
RX=ROXO       DO=DOURADO    PR=PRATA      COL=SORTIDO/COLORIDO
BG=BEGE       GR=GRAFITE    TR=TRANSPARENTE  MD=MADEIRA
CR=CREME      LI=LILÁS      CAQ=CÁQUI     OU=OURO       IN=INOX
LV=LAVANDA    CF=CAFÉ       BZ=BRONZE     NAT=NATURAL   CROM=CROMADO

Cores combinadas usam "/": PT/DO, PT/VM, AZ/CZ, BR/VD, etc.
Modificador de tom vem DEPOIS da cor base: AZ ESC (azul escuro),
CZ CL (cinza claro), VD ESC (verde escuro).
""".strip()

# =====================================================
# PROMPT BASE
# BASE PROMPT
# =====================================================

PROMPT_BASE = f"""
Você é especialista em cadastro SAP.

Sua função é gerar DESCRIÇÕES CURTAS para SAP.

══════════════════════════════════════
FORMATO OBRIGATÓRIO — ORDEM FIXA:
[TIPO DO PRODUTO] [MARCA] [DEMAIS DETALHES] {SUFIXO_CADASTRO}
══════════════════════════════════════

A MARCA É SEMPRE A SEGUNDA PALAVRA (ou grupo de palavras). SEMPRE. SEM EXCEÇÃO.

❌ ERRADO: COFRE BIOMÉTRICO ORARAER LX-11 PT {SUFIXO_CADASTRO}
✅ CERTO:  COFRE ORARAER BIOMETRICO LX-11 PT {SUFIXO_CADASTRO}

══════════════════════════════════════
REGRAS SOBRE A MARCA:
══════════════════════════════════════
- A MARCA vem SEMPRE logo após o tipo do produto
- A MARCA aparece UMA ÚNICA VEZ na descrição — NUNCA repita
- Se a marca tiver mais de uma palavra, coloque todas juntas após o tipo,
  e não repita nenhuma delas depois
- Se a MARCA informada tiver palavras que NÃO aparecem em lugar nenhum da
  descrição longa (ex: nome de linha de produto grudado no cadastro da marca),
  use apenas a parte que realmente é o nome comercial do produto

══════════════════════════════════════
REGRAS OBRIGATÓRIAS:
══════════════════════════════════════
1. ORDEM FIXA: [TIPO] [MARCA] [DETALHES] {SUFIXO_CADASTRO}
2. A primeira palavra = tipo do produto (NÃO abreviar)
3. Logo após o tipo = MARCA, apenas uma vez
4. Tudo em MAIÚSCULO
5. Máximo 40 caracteres no total (incluindo espaços e {SUFIXO_CADASTRO})
6. Nunca retornar texto acima de 40 caracteres
7. Nunca cortar palavra pela metade
8. Sempre terminar com {SUFIXO_CADASTRO}
9. Nunca remover: Tipo do produto, Marca, {SUFIXO_CADASTRO}
10. Abrevie sempre que necessário para caber em 40 caracteres
11. NUNCA repita nenhuma informação (cor, palavra, marca) duas vezes
12. COR é obrigatória quando mencionada na descrição longa — use sempre a sigla
13. COMPRIMENTO/TAMANHO deve ser incluído quando possível

══════════════════════════════════════
CORES E ACABAMENTOS:
══════════════════════════════════════
{TABELA_CORES}

══════════════════════════════════════
ABREVIAÇÕES — USE SEMPRE QUE NECESSÁRIO:
══════════════════════════════════════
sem fio → S/FIO | dobrável → DOBR | masculino → MASC | feminino → FEM
unissex → UN | resistente → RESIST | para → P/ | conjunto → CJ
carregador → CARREG | notebook → NOTE | câmera → CAM | analógico → ANALÓ
elétrico/a → ELÉTR | portátil → PORTÁT | organizador → ORGANIZ
transporte → TRANSP | térmico/a → TERM/TÉRM | inoxidável → INOX
silicone → SILIC | antiaderente → ANTIAD | ergonômico → ERGON
giratório → GIRAT | escritório → ESCRIT | inteligente → INTELIG
ajustável → AJUST | armazenamento → ARMAZ | exercícios → EXERC
polegadas → " ou POL | instrumento → INSTR | unidades → UNI/UN

══════════════════════════════════════
ESTRATÉGIA QUANDO PASSAR DE 40 CARACTERES:
══════════════════════════════════════
PASSO 1: Abrevie palavras longas
PASSO 2: Remova adjetivos secundários
PASSO 3: Remova medidas/quantidades menos importantes
PASSO 4: Remova palavras menos relevantes
⚠️ NUNCA remova: Tipo do produto, Marca, Cor, {SUFIXO_CADASTRO}

══════════════════════════════════════
EXEMPLOS REAIS DO SEU CADASTRO (mesmo tipo de produto — siga o padrão):
══════════════════════════════════════
{{EXEMPLOS}}

══════════════════════════════════════
RETORNE SOMENTE A DESCRIÇÃO CURTA.
NÃO EXPLIQUE.
NÃO USE ASPAS.
"""

# =====================================================
# BASE DE EXEMPLOS REAIS (RAG simples)
# REAL EXAMPLES BASE (Simple RAG)
# =====================================================

def carregar_base_exemplos(caminho_xlsx: str) -> pd.DataFrame:
    df = pd.read_excel(caminho_xlsx)
    col = "Texto breve material"
    df[col] = df[col].astype(str).str.strip()
    df = df[df[col].str.endswith(SUFIXO_CADASTRO)].copy()
    df["TIPO"] = df[col].str.split().str[0].str.upper()
    return df


def selecionar_exemplos(tipo_produto: str, base: pd.DataFrame, n: int = 8) -> list:
    tipo_produto = tipo_produto.upper().strip()
    col = "Texto breve material"

    exatos = base[base["TIPO"] == tipo_produto][col].tolist()
    if len(exatos) >= n:
        return exatos[:n]

    tipos_unicos = base["TIPO"].unique().tolist()
    parecidos = get_close_matches(tipo_produto, tipos_unicos, n=5, cutoff=0.75)

    extras = []
    for t in parecidos:
        if t == tipo_produto:
            continue
        extras += base[base["TIPO"] == t][col].tolist()

    exemplos = exatos + extras
    if len(exemplos) >= n:
        return exemplos[:n]

    faltam = n - len(exemplos)
    aleatorios = base[col].sample(min(faltam, len(base)), random_state=42).tolist()
    return exemplos + aleatorios


# =====================================================
# PÓS-PROCESSAMENTO ROBUSTO
# ROBUST POST-PROCESSING
# =====================================================

def _normaliza(palavra: str) -> str:
    return palavra.strip(".,;:()[]").upper()


def corrigir_posicao_marca(descricao: str, marca: str) -> str:
    descricao = descricao.upper().strip()
    marca = marca.upper().strip()

    # Expressão regular ajustada dinamicamente para o sufixo genérico
    padrao_sufixo = re.escape(SUFIXO_CADASTRO)
    corpo = re.sub(rf"{padrao_sufixo}\.?$", "", descricao).strip()
    palavras = corpo.split()
    if not palavras:
        return f"{corpo} {SUFIXO_CADASTRO}".strip()

    tipo = palavras[0]
    resto_bruto = palavras[1:]

    palavras_marca = marca.split()
    resto_norm = [_normaliza(p) for p in resto_bruto]

    marca_usada = [p for p in palavras_marca if _normaliza(p) in resto_norm]
    if not marca_usada:
        marca_usada = [palavras_marca[0]] if palavras_marca else []

    marca_usada_norm = {_normaliza(p) for p in marca_usada}
    resto_sem_marca = [p for p in resto_bruto if _normaliza(p) not in marca_usada_norm]

    nova_ordem = [tipo] + marca_usada + resto_sem_marca

    vistos, final = set(), []
    for p in nova_ordem:
        chave = _normaliza(p)
        if chave in vistos:
            continue
        vistos.add(chave)
        final.append(p)

    return " ".join(final) + f" {SUFIXO_CADASTRO}"


def ajustar_descricao(descricao: str) -> str:
    descricao = str(descricao).upper().strip()
    descricao = descricao.replace("\n", " ")
    descricao = re.sub(r"\s+", " ", descricao)
    descricao = descricao.replace(SUFIXO_CADASTRO, "").strip()

    limite_texto = 40 - len(f" {SUFIXO_CADASTRO}")
    palavras = descricao.split()
    while len(" ".join(palavras)) > limite_texto and len(palavras) > 1:
        palavras.pop()

    return f"{' '.join(palavras).strip()} {SUFIXO_CADASTRO}"


def validar_descricao(descricao: str) -> bool:
    if len(descricao) > 40:
        return False
    if not descricao.endswith(SUFIXO_CADASTRO):
        return False
    corpo = descricao.replace(SUFIXO_CADASTRO, "").split()
    if len(corpo) != len(set(w.upper() for w in corpo)):
        return False
    return True


# =====================================================
# FUNÇÃO PRINCIPAL COM TENTATIVAS (RETRY)
# MAIN GENERATION FUNCTION WITH RETRIES
# =====================================================

def gerar_descricao_curta(descricao_longa: str, marca: str, base_exemplos: pd.DataFrame) -> str:
    tipo_provavel = str(descricao_longa).strip().split()[0] if str(descricao_longa).strip() else ""
    exemplos = selecionar_exemplos(tipo_provavel, base_exemplos, n=8)
    prompt_final = PROMPT_BASE.format(EXEMPLOS="\n".join(exemplos))

    mensagem = f"""
MARCA:
{marca}

DESCRIÇÃO LONGA:
{descricao_longa}
"""

    tentativas = 3
    for tentativa in range(1, tentativas + 1):
        try:
            resposta = llm.invoke([HumanMessage(content=f"{prompt_final}\n\n{mensagem}")])
            descricao = resposta.content.strip()

            descricao = corrigir_posicao_marca(descricao, marca)
            descricao = ajustar_descricao(descricao)

            if validar_descricao(descricao):
                return descricao

            print(f"  ⚠ Validação falhou ({descricao!r}), tentativa {tentativa}/{tentativas}")

        except Exception as erro:
            print(f"  ⚠ Tentativa {tentativa}/{tentativas} falhou: {erro}")

        if tentativa < tentativas:
            time.sleep(2 * tentativa)

    print(f"  ✗ Todas as tentativas falharam para: {str(descricao_longa)[:60]}")
    return f"ERRO {SUFIXO_CADASTRO}"


# =====================================================
# LEITURA DOS ARQUIVOS EXCEL
# READING EXCEL FILES
# =====================================================

print("Lendo base de exemplos reais...")
base_exemplos = carregar_base_exemplos(arquivo_exemplos)
print(f"  {len(base_exemplos)} exemplos válidos carregados.")

print("Lendo arquivo de produtos...")
df = pd.read_excel(arquivo_excel)

colunas_obrigatorias = ["ASIN", "DESCRIÇÃO_LONGA", "MARCA"]
for coluna in colunas_obrigatorias:
    if coluna not in df.columns:
        raise Exception(f"Coluna '{coluna}' não encontrada no arquivo Excel.")

# =====================================================
# EXECUÇÃO DO PROCESSAMENTO
# PROCESS EXECUTION
# =====================================================

descricoes_curtas = []
print("\nGerando descrições...\n")

for _, linha in tqdm(df.iterrows(), total=len(df)):
    descricao_longa = str(linha["DESCRIÇÃO_LONGA"])
    marca = str(linha["MARCA"])
    descricao_curta = gerar_descricao_curta(descricao_longa, marca, base_exemplos)
    descricoes_curtas.append(descricao_curta)

df["DESCRICAO_CURTA"] = descricoes_curtas
df["TAMANHO_DESC"] = df["DESCRICAO_CURTA"].astype(str).str.len()

# =====================================================
# SALVAR RESULTADO
# SAVE RESULT
# =====================================================

pasta = os.path.dirname(arquivo_excel)
if not pasta:
    pasta = os.path.join(BASE_DIR, "output")
    os.makedirs(pasta, exist_ok=True)

nome_original = os.path.splitext(os.path.basename(arquivo_excel))[0]
data_hora = datetime.now().strftime("%d-%m-%y_%H-%M")
novo_arquivo = os.path.join(pasta, f"{nome_original}_{data_hora}.xlsx")

df.to_excel(novo_arquivo, index=False)

print("\nConcluído!")
print(f"\nArquivo salvo em:\n{novo_arquivo}")

erros = df[df["DESCRICAO_CURTA"] == f"ERRO {SUFIXO_CADASTRO}"]
if len(erros):
    print(f"\n⚠ {len(erros)} linha(s) falharam mesmo após 3 tentativas — revise manualmente:")
    print(erros["ASIN"].tolist())