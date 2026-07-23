# Financeiro Kairo

Aplicação desktop local e offline para gestão financeira pessoal e familiar em Linux. O sistema reúne contas, transações, categorias, compras detalhadas, catálogo de produtos, comparação de preços, planejamento, relatórios e backup em uma única base SQLite controlada pelo usuário.

> **Status:** MVP executável. A qualidade e o pacote Linux são validados pelo GitHub Actions.

## Recursos disponíveis

- contas e saldos consolidados;
- receitas, despesas e transferências;
- categorias e subcategorias protegidas contra ciclos;
- compras detalhadas e importação JSON auditável;
- detecção de importações duplicadas;
- produtos, marcas, variantes, aliases e preços normalizados;
- orçamento mensal, metas e contribuições;
- parcelamentos e baixa de parcelas;
- dashboard e relatórios por período e categoria;
- exportação para Excel e PDF;
- backup, validação, rotação e restauração segura;
- interface PySide6 sem SQL direto nos widgets;
- executável Linux gerado com PyInstaller.

## Requisitos

- Python 3.12 ou superior;
- Linux desktop;
- bibliotecas gráficas Qt disponíveis no sistema.

No Kubuntu/Ubuntu:

```bash
sudo apt update
sudo apt install -y python3.12-venv libegl1 libgl1 libxkbcommon-x11-0
```

## Instalação para desenvolvimento

```bash
git clone https://github.com/ChacaraKairo/financeirokairo.git
cd financeirokairo

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"

financeiro-kairo migrate
financeiro-kairo-desktop
```

Os dados ficam, por padrão, em:

```text
~/.local/share/financeiro-kairo/
```

É possível mudar o diretório com:

```bash
export FINANCEIRO_KAIRO_DATA_DIR=/caminho/desejado
```

## Comandos administrativos

```bash
financeiro-kairo migrate
financeiro-kairo init-db
financeiro-kairo backup
financeiro-kairo validate-backup /caminho/backup.sqlite3
financeiro-kairo restore /caminho/backup.sqlite3
financeiro-kairo rotate-backups --keep 30
```

## Executável Linux

A pipeline `Package Linux` gera o artefato:

```text
financeiro-kairo-linux-x86_64.tar.gz
```

Após extrair:

```bash
chmod +x financeiro-kairo
./financeiro-kairo
```

O lançador `packaging/financeiro-kairo.desktop` pode ser copiado para `~/.local/share/applications/`.

## Importação de compras

Use a tela **Compras e importações** para selecionar um JSON. O arquivo é validado antes da gravação e o hash impede importação duplicada. Um exemplo está em [`examples/compra-exemplo.json`](examples/compra-exemplo.json).

## Arquitetura

```text
Presentation (PySide6)
        ↓
ApplicationFacade e serviços
        ↓
Domain
        ↓
SQLAlchemy / SQLite / arquivos
```

Princípios:

- valores monetários em centavos inteiros;
- quantidades físicas com `Decimal`;
- widgets não executam SQL;
- migrações versionadas com Alembic;
- importações e transferências transacionais;
- dados recuperáveis por backup validado.

## Testes

```bash
ruff check src tests migrations
QT_QPA_PLATFORM=offscreen pytest
```

A CI executa instalação, lint, testes unitários, integração, smoke test da interface e build do executável.

## Documentação

Comece pelo [índice da documentação](docs/00-indice.md). Os critérios verificáveis do MVP estão em [Critérios de aceite](docs/14-criterios-aceitacao-mvp.md).

## Licença

Distribuído sob a licença MIT. Consulte [`LICENSE`](LICENSE).
