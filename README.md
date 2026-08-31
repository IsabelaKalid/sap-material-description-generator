# SAP Material Short Description Generator

### AI + Few-Shot RAG

Uma solução automatizada desenvolvida para gerar descrições curtas e padronizadas para cadastro de materiais no SAP, utilizando **Azure OpenAI**, **Few-Shot RAG** e regras determinísticas de validação.

> An automated data pipeline that generates standardized short descriptions (up to 40 characters) for SAP material master registration using Azure OpenAI and Few-Shot RAG.

## 🚀 Principais Funcionalidades

### 🤖 Few-Shot RAG — Recuperação de Contexto

Seleciona dinamicamente exemplos históricos de cadastros semelhantes com base na categoria do produto, utilizando esses exemplos como contexto para orientar a geração das novas descrições.

### 📏 Motor de Regras e Padronização

Aplica regras determinísticas para garantir conformidade com os padrões de cadastro do SAP, incluindo:

* Limite máximo de **40 caracteres**
* Prefixos e sufixos obrigatórios
* Posicionamento obrigatório da marca
* Padronização de cores e siglas
* Formatação consistente das descrições

### 🔄 Pós-Processamento e Tolerância a Falhas

Após a geração pela IA, o resultado passa por uma camada de validação e correção programática que:

* Corrige automaticamente a posição da marca
* Remove excesso de caracteres
* Valida o formato final
* Executa novas tentativas quando necessário
* Garante conformidade com as regras definidas

### 📊 Processamento em Lote

Processa grandes volumes de materiais através de planilhas Excel, utilizando **Pandas** e **TQDM** para acompanhamento do progresso e geração dos arquivos de saída.

---

## 🔄 Fluxo da Solução

```text
Dados dos Materiais
        ↓
Leitura da Planilha Excel
        ↓
Classificação / Identificação da Categoria
        ↓
Recuperação de Exemplos Históricos
        ↓
Few-Shot RAG
        ↓
Azure OpenAI
        ↓
Geração da Descrição
        ↓
Motor de Regras
        ↓
Pós-Processamento
        ↓
Validação dos 40 Caracteres
        ↓
Descrição Final para SAP
```

---

## 🛠️ Tecnologias Utilizadas

* **Python**
* **Pandas** — processamento e manipulação de dados
* **Azure OpenAI** — geração e processamento com LLM
* **Few-Shot RAG** — recuperação de exemplos para contextualização
* **TQDM** — acompanhamento do processamento em lote
* **Excel** — entrada e saída dos dados

---

## 🎯 Objetivo

O projeto foi desenvolvido para automatizar a criação de descrições curtas para o cadastro de materiais no SAP, reduzindo o trabalho manual e garantindo maior consistência na aplicação das regras de nomenclatura.

A combinação entre **LLM + recuperação de exemplos históricos + regras determinísticas** permite utilizar IA sem abrir mão dos padrões rígidos exigidos pelo processo de cadastro.

---

# SAP Material Short Description Generator

### AI + Few-Shot RAG

An automated data pipeline that generates standardized short descriptions of up to **40 characters** for SAP material master registration using **Azure OpenAI** and **Few-Shot RAG**.

### Key Features

* **Few-Shot RAG Context Retrieval:** Dynamically retrieves historical registration examples based on product categories to guide the LLM.
* **Strict Rule Engine & Formatting:** Enforces mandatory prefix/suffix rules, brand placement, color standardization, and SAP character limits.
* **Post-Processing & Fallback Logic:** Programmatically corrects brand positions, removes text overflow, and performs automatic retries to ensure compliance.
* **Batch Excel Processing:** Processes large datasets using Pandas and TQDM with progress tracking and report generation.
