# floritorrents

Florimovies Torrent é uma aplicação desktop desenvolvida em Python para busca integrada de torrents de filmes, séries e animes. Com uma interface moderna em Tkinter, o aplicativo utiliza diversas APIs – como TMDb, Jikan (MyAnimeList) e Jackett – para reunir resultados completos, incluindo informações detalhadas, imagens de pôster, sinopse e dados sobre torrents. Este projeto facilita a localização e o acesso a conteúdos multimídia de forma rápida e intuitiva.

## Tabela de Conteúdos
- [Recursos](#recursos)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Configuração do Jackett](#configuração-do-jackett)
- [Como Utilizar](#como-utilizar)
- [Configurações Adicionais](#configurações-adicionais)
- [Contribuições](#contribuições)
## Recursos
- **Busca Integrada:** Realize pesquisas de filmes, séries e animes em uma única interface.
- **Resultados Detalhados:** Exibe informações como título, ano, avaliação, sinopse e imagem do pôster.
- **Agregador de Torrents:** Integra serviços como Apibay e Jackett para listar torrents com detalhes de seeds, peers, qualidade e legendas em português.
- **Interface Amigável:** Desenvolvida com Tkinter com configurações de estilo personalizadas para uma melhor experiência do usuário.
- **Tradução Automática:** Sinopses de animes são traduzidas automaticamente para o português com o uso do `googletrans`.

## Requisitos
- **Python 3.x:** Recomenda-se a versão 3.7 ou superior.
- **Bibliotecas Python:**
  - `tkinter` (geralmente incluso na instalação do Python)
  - `requests`
  - `Pillow`
  - `googletrans`
  - Outras bibliotecas padrão (como `threading`, `dataclasses`, etc.)
- **Jackett:** Necessário para a busca de torrents avançada.  
- **APIs de Terceiros:**
  - [TMDb API](https://www.themoviedb.org/documentation/api) – obtenha uma chave de API.
  - [Jikan API](https://docs.api.jikan.moe/) – para dados do MyAnimeList.

## Instalação
1. **Clone ou Baixe o Projeto:**
   ```bash
   git clone https://github.com/seuusuario/florimovies.git
   cd florimovies
   ```
2. **Crie um Ambiente Virtual (opcional, mas recomendado):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```
3. **Instale as Dependências:**
   ```bash
   pip install requests Pillow googletrans
   ```
   Caso identifique outras dependências, adicione-as conforme a documentação do projeto.

## Configuração do Jackett
Jackett é um agregador que integra diversos indexadores de torrents, permitindo uma busca mais abrangente e precisa.

### Passos para Instalar e Configurar o Jackett:
1. **Baixe o Jackett:**
   - Acesse o site oficial do [Jackett](https://jackett.gitbook.io/) e baixe a versão compatível com o seu sistema operacional.
2. **Instale o Jackett:**
   - Siga as instruções de instalação indicadas na documentação.
3. **Inicie o Jackett:**
   - Após a instalação, execute o Jackett. Geralmente, ele abre uma interface web em `http://localhost:9117`.
4. **Obtenha a API Key:**
   - Na interface web do Jackett, localize e copie a sua API Key.
5. **Configure o Aplicativo Florimovies:**
   - No arquivo `florimovies.py`, localize as variáveis de configuração:
     ```python
     self.jackett_api_key = "API"
     self.jackett_host = "http://localhost:9117"
     ```
   - Substitua a chave e, se necessário, o host pelo os dados correspondentes do seu Jackett.

## Como Utilizar
1. **Execute o Aplicativo:**
   - No terminal, dentro da pasta do projeto, execute:
     ```bash
     python florimovies.py
     ```
2. **Realize uma Busca:**
   - Preencha os campos de busca:
     - **Nome:** Digite o nome da mídia desejada.
     - **Ano:** Informe o ano de lançamento (opcional).
     - **Avaliação Mínima:** Informe a nota mínima desejada.
     - **Tipo:** Selecione entre "Todos", "Filmes", "Séries" ou "Anime".
   - Clique no botão **Buscar**.
3. **Visualize os Resultados:**
   - Os resultados serão exibidos em uma tabela central.
   - Ao selecionar um item, detalhes como pôster, informações adicionais e sinopse aparecerão na janela lateral.
4. **Acessando Torrents:**
   - Dê um duplo clique em qualquer item da tabela para abrir uma nova janela exibindo os torrents disponíveis.
   - Na janela de torrents, você verá informações como nome, tamanho, seeds, leechers, fonte, temporada, qualidade e legendas.
   - Para copiar e abrir o link magnet, basta dar um duplo clique sobre o torrent desejado.

## Configurações Adicionais
- **Tradução de Sinopse:** Se o item selecionado for um anime, o aplicativo utiliza o `googletrans` para traduzir automaticamente a sinopse para o português.
- **Chave API do TMDb:** Certifique-se de que sua chave de API do TMDb esteja correta no código para garantir resultados precisos.
- **Personalização:** Você pode ajustar estilos e configurações da interface no método `configure_styles` do arquivo `florimovies.py`.

## SEO e Palavras-Chave
Para melhorar a visibilidade do projeto, considere as seguintes palavras-chave:
- **Torrents de Filmes, Séries e Animes**
- **Busca de Torrents Python**
- **Aplicativo Tkinter para Torrents**
- **Integrador de APIs: TMDb, Jackett, Jikan**
- **Download de Filmes e Séries via Link Magnet**
- **Tutorial de Configuração do Jackett**
- **Search Torrent App em Python**

Estas palavras-chave ajudarão o projeto a ser encontrado por usuários que procuram soluções para busca e download de mídia via torrents.

## Contribuições
Contribuições são sempre bem-vindas! Se você deseja melhorar o projeto, adicionar novas funcionalidades ou corrigir problemas, sinta-se à vontade para enviar **pull requests** ou abrir **issues**.

**Aviso:** Utilize este aplicativo de forma responsável e de acordo com as legislações locais. O autor não se responsabiliza pelo uso indevido do software.
