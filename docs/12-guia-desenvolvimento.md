# 12. Guia de desenvolvimento

## 1. Finalidade

Este guia define a forma recomendada de preparar o ambiente, organizar mudanças e validar contribuições para o Financeiro Kairo. Os comandos exatos poderão ser ajustados quando o código inicial e o `pyproject.toml` forem adicionados.

## 2. Pré-requisitos

- Python 3.12 ou superior.
- Git.
- SQLite 3.
- Bibliotecas de sistema exigidas pelo PySide6 na distribuição Linux utilizada.
- Ambiente virtual isolado.

Ferramentas de qualidade recomendadas:

- `ruff` para lint e formatação;
- `mypy` para análise estática;
- `pytest` e `pytest-cov` para testes;
- `pre-commit` para verificações locais;
- `Alembic` para migrações.

## 3. Preparação do ambiente

Exemplo usando `venv`:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

Nunca instale dependências de desenvolvimento globalmente quando puder usar o ambiente virtual.

## 4. Configuração local

Configurações locais não devem ser versionadas. O projeto deverá fornecer um arquivo de exemplo, como `.env.example` ou uma configuração padrão documentada.

Variáveis previstas:

```text
FINANCEIRO_KAIRO_DATA_DIR
FINANCEIRO_KAIRO_DATABASE_PATH
FINANCEIRO_KAIRO_BACKUP_DIR
FINANCEIRO_KAIRO_LOG_LEVEL
FINANCEIRO_KAIRO_ENV
```

Nenhuma configuração obrigatória para build ou testes deve depender de arquivo secreto ausente no repositório.

## 5. Estrutura do código

```text
src/financeiro_kairo/
├── presentation/
├── application/
├── domain/
├── infrastructure/
├── shared/
└── main.py
```

### Presentation

Responsável por janelas, diálogos, widgets, modelos de tabela e viewmodels. Não contém SQL nem regras financeiras centrais.

### Application

Coordena casos de uso, transações, DTOs, comandos e consultas. Depende de contratos do domínio.

### Domain

Contém entidades, objetos de valor, políticas e regras invariantes. Deve permanecer independente de PySide6 e SQLAlchemy sempre que possível.

### Infrastructure

Implementa persistência, importadores, exportadores, relatórios, logging, backup e integrações técnicas.

## 6. Fluxo de implementação

Para cada funcionalidade:

1. identificar requisito e critério de aceite;
2. modelar regras e invariantes no domínio;
3. definir comando, consulta ou caso de uso;
4. implementar contrato e repositório necessários;
5. criar migração, quando houver alteração de esquema;
6. implementar interface sem duplicar regra de negócio;
7. escrever testes proporcionais ao risco;
8. atualizar a documentação afetada;
9. executar verificações locais.

## 7. Banco de dados e migrações

- Nunca altere manualmente uma base de usuário como estratégia de atualização.
- Toda mudança estrutural deve gerar uma revisão Alembic.
- Migrações devem possuir nomes descritivos.
- Migrações devem ser testadas partindo de uma base vazia e de uma base na versão anterior.
- Dados essenciais de referência devem ser inseridos por mecanismo idempotente.
- O aplicativo deve validar a versão do esquema antes de abrir a janela principal.

Exemplos futuros:

```bash
alembic revision --autogenerate -m "create transactions table"
alembic upgrade head
alembic downgrade -1
```

## 8. Convenções de código

- Use nomes explícitos em inglês no código e português na interface e documentação do usuário.
- Funções devem ter responsabilidade limitada.
- Entidades e objetos de valor devem proteger suas invariantes.
- Use `Decimal` para quantidades e cálculos que não sejam armazenados diretamente em centavos.
- Evite `float` para dinheiro.
- Exceções de domínio devem ser específicas e traduzidas para mensagens amigáveis na camada de apresentação.
- Consultas devem evitar o padrão N+1.
- Tabelas grandes devem usar paginação ou carregamento incremental.

## 9. Validações locais

Conjunto esperado de verificações:

```bash
ruff format --check .
ruff check .
mypy src
pytest
```

Antes de uma versão distribuível, também devem ser executados:

- teste de migração completa;
- teste de importação com arquivos válidos e inválidos;
- teste de backup e restauração;
- teste em ambiente Linux limpo;
- verificação do pacote gerado.

## 10. Estratégia de testes

### Unitários

Regras financeiras, objetos de valor, normalização, reconhecimento, recorrências e comparação de preços.

### Integração

SQLAlchemy, SQLite, migrações, transações, importação, backup e exportação.

### Interface

Cadastro de transação, transferência, importação revisada, filtros, restauração e tratamento de erro.

Use banco SQLite temporário por teste. Testes não devem depender do banco pessoal do desenvolvedor.

## 11. Commits e pull requests

Commits devem ser pequenos, coerentes e descritivos. Prefixos recomendados:

```text
feat: nova funcionalidade
fix: correção de comportamento
docs: documentação
refactor: reorganização sem mudança funcional
test: testes
chore: manutenção técnica
```

O pull request deve explicar:

- o problema ou objetivo;
- o que foi alterado;
- impacto para usuário e desenvolvedor;
- migrações ou riscos;
- verificações executadas;
- documentação atualizada.

## 12. Definição de pronto

Uma entrega está pronta quando:

- os critérios de aceite foram atendidos;
- testes relevantes passam;
- lint, formatação e tipagem passam;
- migrações foram validadas;
- erros possuem tratamento adequado;
- documentação foi atualizada;
- não há dados pessoais ou arquivos locais no commit;
- o fluxo pode ser demonstrado em ambiente limpo.