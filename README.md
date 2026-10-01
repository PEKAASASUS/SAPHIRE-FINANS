# 🔷 SAFIRA — Controle Financeiro Pessoal

> Aplicativo desktop de finanças pessoais. Local, offline, portátil e seguro.

---

## Visão geral

O SAFIRA é um aplicativo Python para controle financeiro pessoal que funciona inteiramente offline, podendo ser executado diretamente de um pendrive. Todos os dados ficam dentro da pasta do próprio aplicativo — nada é gravado no sistema operacional do usuário ou enviado pela rede.

**Versão atual:** 0.1.0 — Etapa 1 (Fundação)

---

## Tecnologias utilizadas

| Componente | Tecnologia | Justificativa |
|---|---|---|
| Linguagem | Python 3.10+ | Portabilidade, ecossistema, facilidade de empacotamento |
| Interface gráfica | [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) | Baseado em Tkinter (stdlib), leve, visual moderno, offline, fácil de empacotar |
| Banco de dados | SQLite 3 (stdlib) | Local, sem servidor, confiável, zero dependências extras |
| Criptografia | [cryptography](https://cryptography.io/) | Biblioteca auditada; PBKDF2-HMAC-SHA256 + Fernet/AES |

---

## Estrutura de diretórios

```
SAFIRA/
│
├── main.py                          ← Ponto de entrada
├── requirements.txt                 ← Dependências Python
├── README.md                        ← Este arquivo
├── ARCHITECTURE.md                  ← Decisões arquiteturais detalhadas
│
├── app/                             ← Todo o código do aplicativo
│   ├── config/
│   │   ├── paths.py                 ← Caminhos portáteis (única fonte de verdade)
│   │   └── settings.py             ← Constantes e configuração local
│   │
│   ├── core/
│   │   ├── app_controller.py        ← Orquestrador de inicialização
│   │   └── session.py              ← Estado de sessão em memória
│   │
│   ├── database/
│   │   ├── connection.py            ← Conexão SQLite singleton
│   │   └── migrations/
│   │       ├── migration_manager.py ← Aplica e rastreia migrations
│   │       └── versions/
│   │           └── m0001_initial_schema.py ← Esquema inicial
│   │
│   ├── models/
│   │   └── user.py                 ← Modelo de dados do usuário
│   │
│   ├── security/
│   │   ├── auth_service.py          ← Regras de autenticação
│   │   ├── crypto_utils.py          ← Primitivas criptográficas
│   │   ├── lock_manager.py          ← Bloqueio automático por inatividade
│   │   └── password_manager.py     ← Hashing e verificação de senha
│   │
│   ├── services/
│   │   └── user_service.py         ← Acesso ao banco (tabela users)
│   │
│   ├── ui/
│   │   ├── main_window.py           ← Janela principal e orquestração de UI
│   │   ├── theme.py                 ← Design system (cores, fontes, espaçamento)
│   │   │
│   │   ├── components/              ← Widgets reutilizáveis
│   │   │   ├── auth_layout.py       ← Layout base das telas de autenticação
│   │   │   ├── buttons.py           ← Botões (Primary, Secondary, Danger, Ghost)
│   │   │   ├── cards.py             ← Container card
│   │   │   ├── dialogs.py           ← Diálogos modais (mensagem e confirmação)
│   │   │   ├── header.py            ← Cabeçalho com título e controles de sessão
│   │   │   ├── inputs.py            ← Campos de texto (LabeledEntry, PasswordEntry)
│   │   │   └── status_badge.py     ← Badge de status (sucesso/erro/atenção)
│   │   │
│   │   ├── navigation/
│   │   │   ├── router.py            ← Roteador de telas (troca de frames)
│   │   │   └── sidebar.py          ← Barra lateral com todos os itens de menu
│   │   │
│   │   └── screens/
│   │       ├── home_screen.py       ← Home (minimalista — Etapa 1)
│   │       ├── lock_screen.py       ← Tela de bloqueio
│   │       ├── login_screen.py      ← Tela de login
│   │       ├── placeholder_screen.py← Fábrica de telas placeholder
│   │       └── setup_master_password_screen.py ← Criação da senha mestre
│   │
│   └── utils/
│       └── logger.py               ← Logger local (sem telemetria)
│
├── assets/
│   └── icons/                       ← Ícones e imagens (Etapas 2/3)
│
├── config/                          ← Configuração local não sensível (app_config.json)
│
├── data/                            ← Banco de dados e logs (gerados em tempo de execução)
│   ├── safira.db                    ← Banco SQLite
│   └── logs/
│       └── safira.log               ← Log com rotação (1 MB × 3 arquivos)
│
└── tests/                           ← Testes automatizados (unittest)
    ├── test_auth_service.py
    ├── test_crypto_utils.py
    ├── test_database_migrations.py
    ├── test_password_manager.py
    ├── test_paths.py
    ├── test_session_and_lock.py
    └── test_user_service.py
```

---

## Como executar

### Pré-requisitos

- Python 3.10 ou superior
- pip

### Instalação

```bash
# 1. Navegue até a pasta do SAFIRA
cd SAFIRA

# 2. (Recomendado) Crie um ambiente virtual
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Execute
python main.py
```

### Execução dos testes

```bash
# Na pasta SAFIRA
python -m unittest discover -s tests -p "test_*.py" -v
```

---

## Dependências

```
customtkinter>=5.2.2,<6.0.0   # interface gráfica
cryptography>=42.0.0           # criptografia (PBKDF2 + Fernet/AES)
```

Tudo mais (`sqlite3`, `logging`, `hashlib`, `os`, `json`) faz parte da biblioteca padrão do Python.

---

## Localização dos dados

| Arquivo | Caminho | Conteúdo |
|---|---|---|
| Banco de dados | `data/safira.db` | Todos os dados do usuário (SQLite) |
| Log da aplicação | `data/logs/safira.log` | Eventos e erros (rotação 1 MB × 3) |
| Configuração local | `config/app_config.json` | Preferências não sensíveis (auto-lock, tema) |

**Importante:** todos esses caminhos são relativos à pasta onde o SAFIRA está instalado, nunca ao diretório do usuário ou do sistema operacional. Mover a pasta do SAFIRA (ou o pendrive) não quebra o funcionamento.

---

## Funcionamento da segurança

### Senha mestre

1. O usuário define uma senha mestre no primeiro uso.
2. Um **salt aleatório de 16 bytes** é gerado por `os.urandom()`.
3. A senha é derivada com **PBKDF2-HMAC-SHA256** (200.000 iterações).
4. Apenas o `salt` e o `hash` resultante são armazenados no banco — **a senha nunca é gravada em nenhum lugar**.
5. No login, o mesmo processo é aplicado à senha digitada e o resultado é comparado usando `hmac.compare_digest` (comparação em tempo constante, resistente a timing attacks).

### Sessão e bloqueio

- A sessão vive apenas em memória (nunca persistida em disco).
- **Bloquear:** mantém o usuário "logado" em memória, mas esconde a interface atrás da tela de bloqueio. Desbloquear exige a senha mestre.
- **Logout:** encerra a sessão completamente e retorna à tela de login.
- **Bloqueio automático:** um verificador periódico (a cada 1 segundo) compara o tempo de inatividade com o limite configurado (padrão: 5 minutos). Qualquer evento de mouse/teclado reseta o contador.

### Infraestrutura para criptografia em repouso

`app/security/crypto_utils.py` já expõe `encrypt_data` e `decrypt_data` (Fernet/AES-128-CBC) e `derive_fernet_key_from_password`. Essa infraestrutura está pronta para cifrar os dados financeiros em disco nas Etapas 2 e 3, sem necessidade de refatorar a arquitetura de segurança.

---

## Como adicionar novas telas

1. Crie um arquivo em `app/ui/screens/nome_da_tela.py`.
2. Defina uma classe que herde de `ctk.CTkFrame`.
3. No `main_window.py`, localize o método `_register_screens` e registre a nova tela no router:
   ```python
   self._router.register("chave_da_tela", lambda master: NovaTela(master, ...))
   ```
4. Se a tela já tiver um item correspondente na sidebar (`NAV_ITEMS` em `sidebar.py`), ela será ativada automaticamente quando o usuário clicar no menu.

---

## Como adicionar novos módulos de negócio

1. **Modelo de dados:** crie `app/models/nome_do_modelo.py` com um dataclass.
2. **Migration:** crie `app/database/migrations/versions/m000N_nome.py` com `VERSION`, `NAME` e `up(cursor)`. Registre-a na lista `MIGRATIONS` em `migration_manager.py`.
3. **Serviço/repositório:** crie `app/services/nome_service.py` para o acesso ao banco.
4. **Lógica de negócio (opcional):** se houver regras complexas, crie um serviço em `app/core/` ou `app/security/`.
5. **Tela:** siga o processo descrito na seção anterior.
