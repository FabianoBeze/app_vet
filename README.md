# Sistema de Gerenciamento de Clínica Veterinária

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/license-MIT-0f7a53)](LICENSE)

Sistema web de código aberto (licença MIT), desenvolvido em Flask, para gerenciar o
cadastro de animais, clínicas e agendamentos de procedimentos. A aplicação foi refatorada
para uma arquitetura modular e inclui funcionalidades de segurança, como a verificação de
atendimentos por token.

## Arquitetura

O projeto foi estruturado de forma modular para separar as responsabilidades e facilitar a manutenção:

- `run.py`: Ponto de entrada da aplicação, responsável por inicializar o banco de dados e executar o servidor Flask.
- `main.py`: Contém as definições de rotas (endpoints) e a lógica de renderização das páginas.
- `models.py`: Define os modelos de dados do SQLAlchemy (`User`, `Clinic`, `Animal`).
- `services.py`: Contém a lógica de negócios e as funções de acesso ao banco de dados (criação de usuários, manipulação de animais, etc.).
- `extensions.py`: Configura e inicializa as extensões do Flask (SQLAlchemy, LoginManager).
- `instance/`: Diretório onde o banco de dados (`pets.db`) e os logs são armazenados.
- `scripts/`: Contém scripts de utilidade para manutenção e testes.

## Funcionalidades Principais

O sistema possui três perfis de usuários com diferentes níveis de acesso:

1.  **Administrador:**
    *   Visão completa de todos os animais, clínicas e agendamentos.
    *   Gerenciamento completo de clínicas (criar, editar, remover).

2.  **Clínica:**
    *   Visualiza uma fila de animais aguardando atendimento e pode reivindicá-los para sua clínica.
    *   Ao reivindicar um animal, um **token de verificação** é gerado.
    *   Gerencia os animais de sua clínica (agenda, marca como concluído).
    *   Visualiza o token na sua dashboard para informar ao tutor.

3.  **Usuário (Tutor do Animal):**
    *   Pode se cadastrar e fazer login.
    *   Cadastra seus próprios animais para entrarem na fila de atendimento.
    *   Visualiza o status e o token de seus animais na sua dashboard.

### Fluxo de Verificação por Token

Para garantir a segurança e a comunicação correta, um token de 6 dígitos é gerado quando uma clínica reivindica um animal.

1.  Um tutor cadastra um animal, que entra na fila de espera geral.
2.  Uma clínica visualiza a fila e **reivindica** o animal.
3.  Nesse momento, o sistema gera um token numérico e o associa ao animal.
4.  O token fica visível para a **clínica** (em sua dashboard) e para o **tutor** (na dashboard dele).
5.  A clínica informa o token ao tutor como uma forma de confirmação. O tutor deve apresentar esse token no dia do atendimento.

## Tecnologias Utilizadas

- **Backend:** Python com Flask
- **Banco de Dados:** SQLAlchemy com SQLite
- **Autenticação:** Flask-Login
- **Frontend:** HTML renderizado diretamente no Flask com `render_template_string` para simplicidade.

## Como Executar o Projeto

1.  **Pré-requisitos:**
    *   Python 3.x
    *   Instale as dependências (recomenda-se o uso de um ambiente virtual):
      ```bash
      python -m venv .venv
      # Windows: .venv\Scripts\activate  |  Linux/macOS: source .venv/bin/activate
      pip install -r requirements.txt
      ```

2.  **Execução:**
    *   Clone o repositório.
    *   Execute o arquivo `run.py`:
      ```bash
      python run.py
      ```
    *   Acesse a aplicação em `http://127.0.0.1:5000`.

3.  **Banco de Dados:**
    *   O banco de dados (`pets.db`) será criado automaticamente na pasta `instance` na primeira execução.
    *   Se houver alterações nos modelos (`models.py`), pode ser necessário apagar o arquivo `pets.db` para que o banco seja recriado com a nova estrutura.

## Credenciais de Acesso Padrão

Ao iniciar a aplicação pela primeira vez, um usuário administrador é criado:

- **Administrador:**
    - **Usuário:** `admin`
    - **Senha:** `admin`

Novos usuários (tutores de animais) e clínicas devem ser cadastrados através da interface da aplicação pelo administrador.

## Contribuição

Sugestões e issues são bem-vindas. Para enviar código, abra uma branch a partir da `main`,
descreva a mudança e envie um pull request.

## Licença

Distribuído sob a licença **MIT**. Veja [`LICENSE`](LICENSE).
