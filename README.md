# Luna Seller AI

Aplicativo simples para ajudar na criação de anúncios de produtos.

## Primeira versão

- recebe a foto do produto para conferência;
- organiza as informações principais;
- gera um título curto;
- cria uma descrição profissional;
- sugere palavras-chave;
- permite baixar o rascunho;
- mantém a publicação manual para revisão da Selma.

Nesta etapa, o aplicativo não publica automaticamente no Mercado Livre e não usa API paga.

## Como executar no Windows

1. Abra a pasta do projeto no terminal.
2. Instale as dependências:

```bash
pip install -r requirements.txt
```

3. Inicie o aplicativo:

```bash
streamlit run app.py
```

4. O navegador abrirá a tela do Luna Seller AI.

## Próximas etapas

Depois da validação desta tela, poderemos adicionar geração com inteligência artificial, histórico de produtos e integração gradual com o Mercado Livre.
