# SAFIRA — Decisões Arquiteturais

> Documento de referência para desenvolvedores e IAs continuando o projeto.
> Etapa 1 — Fundação (versão 0.1.0)

---

## Contexto do projeto

O SAFIRA é um aplicativo **pessoal, desktop, offline e portátil** de controle financeiro. Os requisitos que mais impactam as decisões arquiteturais são:

- **Portabilidade em pendrive:** nenhum dado ou configuração pode ser gravado fora da pasta do app.
- **Funcionamento offline:** sem dependências de rede para funções essenciais.
- **Baixo consumo de recursos:** sem servidores locais, daemons ou processos auxiliares.
- **Segurança:** dados financeiros sensíveis; senha nunca em texto puro.
- **Evolução incremental:** 3 etapas de desenvolvimento; a fundação não deve ser refeita.

---

## ADR 1 — Interface gráfica: CustomTkinter

**Escolhido:** CustomTkinter (sobre Tkinter nativo).

**Alternativas avaliadas:**

| Opção | Motivo de descarte |
|---|---|
| PyQt5/PyQt6 | Pesado, licença LGPL/GPL pode complicar distribuição comercial futura |
| PySide6 | Mesmo problema de peso e licença |
| Kivy | Mais voltado a mobile/touch; visual fora do padrão desktop |
| Flet | Baseia-se em Flutter/Dart; overhead desnecessário para app local |
| wxPython | Mais pesado que Tkinter; empacotamento mais complexo |
| DearPyGui | Ótimo para dashboards, mas muito orientado a jogos/GPU (anti-requisito) |

**Por que CustomTkinter:**
- Construído sobre `tkinter` (biblioteca padrão do Python → zero dependência extra para a GUI base).
- Visual moderno suficientemente premium para a identidade do SAFIRA.
- Leve: sem servidor de backend, sem processo filho, sem GPU obrigatória.
- Facilmente empacotável com PyInstaller → executável portátil único.
- Funciona 100% offline.

---

## ADR 2 — Banco de dados: SQLite

**Escolhido:** SQLite via módulo `sqlite3` da biblioteca padrão.

**Por que SQLite:**
- Banco de dados em arquivo único (`data/safira.db`) → portável junto com o app.
- Sem servidor, sem daemon, sem porta de rede.
- Suporte nativo no Python — zero dependência extra.
- Confiável o suficiente para dados financeiros pessoais (usado pelo Firefox, WhatsApp, iOS, Android).
- Performance adequada para o volume de dados de uma pessoa física.

**Configurações ativas em toda conexão:**
- `PRAGMA foreign_keys = ON` — o SQLite não garante integridade referencial por padrão; esta pragma é ativada a cada abertura de conexão.
- `row_factory = sqlite3.Row` — permite acesso por nome de coluna, não apenas por índice.

---

## ADR 3 — Migrations: sistema próprio (não Alembic)

**Motivação:** manter o projeto leve e sem dependências desnecessárias.

**Funcionamento:**
- Tabela `schema_migrations` registra versões já aplicadas.
- Cada migration é um módulo Python com `VERSION` (int), `NAME` (str) e `up(cursor)`.
- O `MigrationManager` aplica migrations pendentes em ordem crescente de versão, dentro de transação por migration.
- Uma migration já aplicada **nunca é reescrita** — sempre se cria uma nova migration incremental.

**Para adicionar uma migration (Etapa 2, 3...):**
```python
# app/database/migrations/versions/m0002_nome.py
VERSION = 2
NAME = "descricao_curta"

def up(cursor):
    cursor.execute("ALTER TABLE accounts ADD COLUMN ...")
```
Depois, registrar em `MIGRATIONS` no `migration_manager.py`.

---

## ADR 4 — Criptografia: PBKDF2-HMAC-SHA256 + Fernet

**Regra absoluta:** nenhum algoritmo criptográfico implementado manualmente.

**Para a senha mestre:**
- Algoritmo: PBKDF2-HMAC-SHA256 (via biblioteca `cryptography`).
- Iterações: 200.000 (recomendação OWASP 2023+ para PBKDF2-SHA256).
- Salt: 16 bytes aleatórios por `os.urandom()`, único por usuário.
- Armazenamento: apenas `salt` (base64) e `hash` (base64) — nunca a senha.
- Comparação: `hmac.compare_digest` (resistente a timing attacks).

**Para dados em repouso (Etapas 2/3):**
- A infraestrutura já existe em `crypto_utils.py`: `encrypt_data` e `decrypt_data` usando Fernet (AES-128-CBC + HMAC-SHA256, com IV aleatório por mensagem).
- A chave é derivada da senha mestre via `derive_fernet_key_from_password`.
- Ativação: basta chamar encrypt/decrypt nas operações de leitura/escrita do banco quando essa feature for implementada.

---

## ADR 5 — Portabilidade: caminhos relativos à pasta do app

**Problema:** `os.getcwd()`, `~` (home do usuário) ou caminhos absolutos de sistema tornam o app dependente de um computador específico.

**Solução:** `app/config/paths.py` é a **única fonte de verdade** sobre caminhos. Ele detecta automaticamente se o app está rodando via `python main.py` (usa o diretório do projeto) ou empacotado com PyInstaller (usa a pasta do `.exe`). Todo o resto do código importa as constantes de `paths.py`.

**Regra para desenvolvedores:** nunca construir caminhos com `os.getcwd()` ou `Path.home()` em nenhum módulo que não seja `paths.py`.

---

## ADR 6 — Separação de responsabilidades

A arquitetura segue uma hierarquia de camadas sem dependências circulares:

```
UI (main_window, screens, components)
    ↓ usa
AppController / Session / LockManager
    ↓ usa
auth_service / password_manager / crypto_utils
    ↓ usa
user_service (repositório)
    ↓ usa
connection.py (banco) / models/
```

- **UI** nunca acessa o banco diretamente.
- **Services** nunca conhecem a UI.
- **Security** não conhece nem UI nem banco — apenas primitivas e regras.
- **AppController** é o único ponto de montagem: cria conexão, session e lock_manager, e os passa adiante.

---

## ADR 7 — Sessão em memória (não persistida)

A `Session` vive apenas durante a execução do processo. Isso é intencional:

- Evita surface de ataque (token de sessão no disco).
- Simplifica o modelo: no próximo `python main.py`, o usuário sempre começa na tela de login.
- A diferença entre **bloquear** (interface oculta, sessão mantida em memória) e **logout** (sessão destruída) é preservada.

---

## ADR 8 — Router baseado em troca de frames

Optou-se por um roteador simples de troca de frames (`CTkFrame`) em vez de um sistema de navegação por abas ou pilha. Motivos:

- Simples de entender e manter.
- Permite substituir qualquer tela futuramente sem tocar no roteador.
- A sidebar permanece fixa; apenas a área de conteúdo é trocada.

Adicionar uma nova tela na Etapa 2 exige apenas criar o widget e registrá-lo:
```python
router.register("movimentacoes", lambda master: MovimentacoesScreen(master, controller))
```

---

## Estado da Etapa 1

### Implementado e testado
- [x] Portabilidade (paths relativos ao app, verificado com `is_portable_safe()`)
- [x] Banco de dados SQLite + migrations versionadas
- [x] Sistema de segurança completo (hash, salt, derivação, verificação, sem plaintext)
- [x] Session em memória + LockManager (bloqueio manual e automático)
- [x] auth_service (setup, login, troca de senha)
- [x] Design system (cores, fontes, componentes reutilizáveis)
- [x] Navegação completa (sidebar com 12 itens, router, header)
- [x] Telas: setup de senha mestre, login, bloqueio, home minimalista, placeholders
- [x] Logger local (sem telemetria)
- [x] 50 testes automatizados (100% passando)

### Deixado para Etapa 2
- [ ] Home com dados reais (saldo, movimentações recentes, compromissos)
- [ ] Tela de Movimentações (CRUD completo)
- [ ] Tela de Contas
- [ ] Tela de Cartões
- [ ] Tela de Compromissos
- [ ] Ativação da criptografia em repouso (infraestrutura já existe)

### Deixado para Etapa 3
- [ ] Planejamento / Mapa do Dinheiro / Metas / Investimentos / Relatórios / Notificações

---

## Guia de expansão rápida

### Nova tela

```python
# 1. Criar app/ui/screens/minha_tela.py
class MinhaTela(ctk.CTkFrame):
    def __init__(self, master, controller: AppController):
        super().__init__(master, fg_color=Colors.GRAPHITE_LIGHT, corner_radius=0)
        # ... widgets

# 2. Registrar em main_window._register_screens():
self._router.register("chave", lambda m: MinhaTela(m, self.controller))
```

### Novo modelo + serviço + migration

```python
# 1. app/models/categoria.py  (dataclass)
# 2. app/database/migrations/versions/m0002_add_category_data.py  (up function)
# 3. app/services/category_service.py  (CRUD)
# 4. Registrar migration em migration_manager.MIGRATIONS
```

### Novo componente de UI

```python
# app/ui/components/meu_componente.py
class MeuComponente(ctk.CTkFrame):
    def __init__(self, master, ...):
        super().__init__(master, fg_color=Colors.GRAPHITE, ...)
        # Sempre usar constantes de app.ui.theme — nunca cores "cruas"
```
