# Financeiro Kairo

Sistema desktop de gestão financeira pessoal e familiar, criado para Linux e orientado a funcionamento local e offline. O projeto integra controle financeiro, planejamento doméstico, registro detalhado de compras, catálogo de produtos, comparação de preços e importações auditáveis.

> **Status:** especificação e planejamento técnico do MVP.

## Visão do produto

O Financeiro Kairo pretende substituir planilhas dispersas por uma aplicação única, simples de usar e robusta internamente. Os dados permanecem sob controle do usuário, as automações são revisáveis e nenhuma decisão de categorização ou reconhecimento deve ocorrer de forma invisível.

### Objetivos principais

- Registrar receitas, despesas, transferências, compras e pagamentos.
- Organizar gastos por categorias, subcategorias, etiquetas e períodos.
- Planejar orçamentos, metas, recorrências e parcelamentos.
- Importar compras detalhadas com validação, pré-visualização e detecção de duplicidade.
- Reconhecer produtos já cadastrados e aprender com confirmações do usuário.
- Separar produto-base, marca, variante, embalagem, quantidade e unidade.
- Comparar preços totais e normalizados por unidade de medida.
- Gerar dashboards, relatórios e exportações.
- Executar localmente, com backup, restauração e trilha de auditoria.

## Diferencial do projeto

O sistema não trata `Arroz Camil Tipo 1 5 kg` como um texto único. A modelagem separa:

- **Produto-base:** Arroz
- **Marca:** Camil
- **Variante:** Tipo 1
- **Quantidade:** 5
- **Unidade:** kg
- **Embalagem:** pacote
- **Categoria:** Alimentação / Mercearia

Essa separação permite comparar produtos equivalentes entre marcas, estabelecimentos, tamanhos de embalagem e períodos diferentes usando preço por quilograma, litro, unidade ou outra unidade-base.

## Escopo do MVP

O MVP contempla:

1. contas e formas de pagamento;
2. receitas, despesas e transferências;
3. categorias, etiquetas e filtros;
4. compras detalhadas por item;
5. catálogo de produtos, marcas e variantes;
6. importação estruturada por JSON;
7. reconhecimento de produtos e categorização assistida;
8. histórico e comparação de preços;
9. orçamentos e metas básicas;
10. relatórios essenciais;
11. backup, restauração e auditoria.

Ficam fora do MVP: sincronização em nuvem, aplicativo móvel, integração bancária automática, OCR de notas fiscais e serviços externos de inteligência artificial.

## Arquitetura e stack

- Python 3.12+
- PySide6 / Qt 6
- SQLite em modo WAL
- SQLAlchemy 2
- Alembic
- Pydantic
- RapidFuzz
- pandas
- PyQtGraph
- ReportLab
- openpyxl
- pytest

A aplicação segue uma arquitetura modular em camadas:

```text
Presentation (PySide6)
        ↓
Application (casos de uso)
        ↓
Domain (entidades e regras)
        ↓
Infrastructure (SQLite, arquivos, relatórios e backup)
```

## Princípios técnicos

- Valores monetários usam centavos inteiros ou `Decimal` com escala explícita.
- Quantidades físicas usam `Decimal`.
- Widgets não executam SQL diretamente.
- Migrações de banco passam pelo Alembic.
- Importações são transacionais e auditáveis.
- Operações pesadas não bloqueiam a interface.
- Toda sugestão automática deve poder ser revisada e corrigida.
- Dados locais devem ser recuperáveis por backup validado.

## Documentação

Comece pelo [índice da documentação](docs/00-indice.md).

### Produto e requisitos

- [Visão geral](docs/01-visao-geral.md)
- [Requisitos funcionais](docs/02-requisitos-funcionais.md)
- [Requisitos não funcionais](docs/11-requisitos-nao-funcionais.md)
- [Critérios de aceite do MVP](docs/14-criterios-aceitacao-mvp.md)

### Arquitetura e dados

- [Arquitetura técnica](docs/03-arquitetura.md)
- [Modelo de dados](docs/04-modelo-de-dados.md)
- [Decisões arquiteturais](docs/13-decisoes-arquiteturais.md)

### Funcionalidades especializadas

- [Importação JSON](docs/05-importacao-json.md)
- [Categorização e aprendizado](docs/06-categorizacao-e-aprendizado.md)
- [Interface e experiência de uso](docs/07-interface-ux.md)
- [Relatórios e análises](docs/08-relatorios-e-analises.md)
- [Segurança e backup](docs/09-seguranca-e-backup.md)

### Execução do projeto

- [Roadmap](docs/10-roadmap.md)
- [Guia de desenvolvimento](docs/12-guia-desenvolvimento.md)

## Exemplo de importação

Consulte [`examples/compra-exemplo.json`](examples/compra-exemplo.json).

## Definição de pronto

Uma funcionalidade é considerada pronta quando:

- atende aos critérios de aceite documentados;
- possui validações e mensagens de erro adequadas;
- respeita as fronteiras arquiteturais;
- possui testes automatizados proporcionais ao risco;
- não compromete integridade, backup ou restauração;
- tem sua documentação atualizada.

## Licença

A licença do projeto ainda deve ser definida antes da primeira distribuição pública.