# HealthMind

Ferramenta de triagem e aprendizado clínico voltada para fins educacionais.
Não substitui avaliação profissional.

## Requisitos

- Python 3.12 instalado
- Conta na OpenAI e variável de ambiente `OPENAI_API_KEY` configurada

## Passo a passo para executar

No Windows:

1. Abra o PowerShell na pasta do projeto `HealthMind`.
2. Crie o ambiente virtual (somente na primeira vez):

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
3. Defina a variável de ambiente `OPENAI_API_KEY` (substituir pela chave correta):

    ```powershell
       setx OPENAI_API_KEY "SUA_CHAVE_AQUI"

Feche e abra o PowerShell novamente.

4. Ative o ambiente e execute o app:
    
    ```powershell
       .\.venv\Scripts\activate
       python app.py
   
5. Abra o link mostrado no terminal no navegador (ex.: http://127.0.0.1:7860).
