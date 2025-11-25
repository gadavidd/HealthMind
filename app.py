import yaml
import ssl
import json
import gradio as gr

from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from main import retrieve
from pathlib import Path

ssl._create_default_https_context = ssl._create_unverified_context

# Config.json contém a chave da API para comunicação com o modelo GPT
CONFIG_PATH = Path(__file__).parent / "config.json"
if CONFIG_PATH.exists():
    data = json.loads(CONFIG_PATH.read_text())
    import os
    os.environ["OPENAI_API_KEY"] = data["OPENAI_API_KEY"]

# Carrega Prompt e contexto
BASE_DIR = Path(__file__).resolve().parent

SYSTEM = (BASE_DIR / "modelo.md").read_text(encoding="utf-8")
CTX = yaml.safe_load((BASE_DIR / "contexto_bauru.yml").read_text(encoding="utf-8"))

# Define o modelo GPT 4o mini como LLM
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

# Prompt base
RAG_PROMPT = PromptTemplate.from_template(
    """<|system|>
{system}
<|user|>
Use APENAS o contexto a seguir (trechos recuperados de diretrizes médicas em PDF) para responder.
Inclua marcações [n] ao lado de afirmações específicas e liste as fontes ao final.

[Contexto]
{context}

[Pergunta]
{question}

Formato:
- Resumo
- Pontos-chave (lista)
- Referências (liste [n] utilizados com fonte)
- Aviso: Conteúdo educacional. Não substitui avaliação profissional.
"""
)

# Estrutura adicional de prompt para composição de cada caso
CASE_PROMPT = PromptTemplate.from_template(
    """<|system|>
{system}
<|user|>
Analise o caso abaixo conforme as instruções do sistema HealthMind.

{case}

[Contexto local]
{contexto}
"""
)

# Formata trechos recuperados do índice simples (index_simples.json) para inclusão no prompt
def format_context(entries):
    blocks, cites = [], []

    for i, e in enumerate(entries, start=1):
        meta = e.get("metadata", {}) or {}
        src = meta.get("source", "desconhecida")
        page = meta.get("page", None)

        header = f"[{i}] Fonte: {src}"
        if page is not None:
            header += f" (página {page})"

        blocks.append(f"{header}\n{e['text']}")
        cites.append(header)

    return "\n\n".join(blocks), "\n".join(cites)

# Executa consulta aos PDFs indexados usando RAG Simples
def answer_with_rag(question: str) -> str:
    entries = retrieve(question, k=4)

    if not entries:
        return "Nenhum trecho relevante foi encontrado nos PDFs indexados."

    context, citations = format_context(entries)

    system_with_ctx = SYSTEM + f"\n\n[Contexto local]\n{json.dumps(CTX, ensure_ascii=False)}"

    prompt = RAG_PROMPT.format(
        system=system_with_ctx,
        context=context[:3000],
        question=question
    )

    chain = llm | StrOutputParser()
    result = chain.invoke(prompt)

    if citations:
        result += "\n\n---\nFontes recuperadas:\n" + citations

    return result

# Monta o caso clínico e envia para o LLM com instruções do arquivo modelo.md
def analyze_case(idade, sexo, queixa, sinais, sintomas, historico):

    case = f"""Idade: {idade}
            Sexo: {sexo}
            Queixa principal: {queixa}
            Sinais vitais: {sinais}
            Sintomas associados: {sintomas}
            Histórico relevante: {historico}
            """

    prompt = CASE_PROMPT.format(
        system=SYSTEM,
        case=case,
        contexto=json.dumps(CTX, ensure_ascii=False)
    )

    chain = llm | StrOutputParser()
    return chain.invoke(prompt)

# Cria a interface do Gradio
def create_app():
    custom_css = """
    <style>
    /* Esconde rodapé padrão do Gradio */
    footer, .gradio-container footer {
        display: none !important;
    }

    /* Botão principal */
    #btn-case {
        background-color: #16a34a !important;
        color: white !important;
        border-color: #16a34a !important;
    }
    #btn-case:hover {
        background-color: #15803d !important;
        border-color: #15803d !important;
    }
    </style>
    """

    with gr.Blocks(title="HealthMind", analytics_enabled=False) as demo:
        # Injeta CSS customizado
        gr.HTML(custom_css)

        # Cabeçalho com ícone + título
        with gr.Row():
            gr.Image(
                value="resources/icon.png",
                show_label=False,
                interactive=False,
                height=60,
            )

        with gr.Row():
            with gr.Column(scale=1):
                idade = gr.Number(label="Idade", value=35, precision=0)
                sexo = gr.Radio(
                    choices=["Feminino", "Masculino"],
                    value="Feminino",
                    label="Sexo",
                )
                queixa = gr.Textbox(
                    label="Queixa principal",
                    placeholder="Ex.: Febre e dor de cabeça há 3 dias",
                )
                sinais = gr.Textbox(
                    label="Sinais vitais",
                    placeholder="Ex.: PA 130x85, FC 95, Temp 38.5°C, SpO2 98%",
                )
                sintomas = gr.Textbox(
                    label="Sintomas associados",
                    placeholder="Ex.: náusea, dor retro-orbitária, mialgia",
                )
                historico = gr.Textbox(
                    label="Histórico / comorbidades / medicamentos",
                    placeholder="Ex.: HAS em uso de IECA; sem alergias conhecidas",
                )

                btn_case = gr.Button(
                    "Analisar caso clínico",
                    elem_id="btn-case",
                )

            with gr.Column(scale=1):
                out_case = gr.Markdown(label="Resultado da análise")

        btn_case.click(
            analyze_case,
            inputs=[idade, sexo, queixa, sinais, sintomas, historico],
            outputs=out_case,
        )

        # Aviso em cinza claro no rodapé sobre a ferramenta sem apenas uma ferramenta educacional/triagem
        gr.HTML(
            """
            <div style="margin-top: 2rem; text-align: center;">
                <p style="color: #6b7280; font-size: 0.9rem;">
                    Ferramenta de triagem e aprendizado clínico voltada para fins educacionais.
                    Não substitui avaliação profissional.
                </p>
            </div>
            """
        )

    return demo

# Chama principal para rodar a aplicação
if __name__ == "__main__":
    application = create_app()
    application.launch()
