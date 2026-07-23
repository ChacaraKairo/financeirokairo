# 13. Decisões arquiteturais

Este documento registra decisões estruturais do projeto. Cada decisão deve indicar contexto, escolha, consequências e condições para revisão.

## ADR-001 — Aplicação desktop local e offline

**Status:** aceita.

### Contexto

O sistema manipula dados financeiros pessoais e deve funcionar sem dependência de serviços externos.

### Decisão

A primeira versão será uma aplicação desktop Linux, local-first e offline por padrão.

### Consequências

- maior controle e privacidade dos dados;
- necessidade de estratégia própria de backup e restauração;
- sincronização entre dispositivos fica fora do MVP;
- integrações futuras devem ser opcionais e explícitas.

## ADR-002 — Python 3.12 e PySide6

**Status:** aceita.

### Contexto

O produto exige interface desktop rica, tabelas, gráficos, importação de dados e distribuição para Linux.

### Decisão

Usar Python 3.12+ com PySide6/Qt 6 para a aplicação desktop.

### Consequências

- acesso ao ecossistema Python para dados e relatórios;
- uso de modelos Qt para tabelas de alto volume;
- necessidade de controlar operações pesadas fora da thread da interface;
- empacotamento deve ser testado em ambiente Linux limpo.

## ADR-003 — SQLite como banco principal

**Status:** aceita.

### Contexto

A aplicação é local, de usuário único ou família, e não necessita de servidor de banco no MVP.

### Decisão

Usar SQLite com chaves estrangeiras habilitadas e modo WAL.

### Consequências

- instalação simples e arquivo de dados portátil;
- transações ACID adequadas ao domínio;
- necessidade de backup consistente para banco em uso;
- consultas, índices e paginação devem ser planejados para crescimento da base.

## ADR-004 — SQLAlchemy 2 e Alembic

**Status:** aceita.

### Contexto

O projeto precisa separar persistência das regras de negócio e evoluir o esquema com segurança.

### Decisão

Usar SQLAlchemy 2 para persistência e Alembic para migrações.

### Consequências

- repositórios devem esconder detalhes de ORM da aplicação;
- entidades de domínio não devem depender desnecessariamente de modelos ORM;
- toda alteração de esquema deve incluir migração e teste.

## ADR-005 — Arquitetura modular em camadas

**Status:** aceita.

### Contexto

Misturar widgets, SQL e regras financeiras aumenta acoplamento e dificulta testes.

### Decisão

Separar o sistema em Presentation, Application, Domain e Infrastructure.

### Consequências

- widgets não acessam banco diretamente;
- casos de uso coordenam transações e serviços;
- regras centrais podem ser testadas sem interface;
- interfaces de repositório pertencem às camadas internas e implementações à infraestrutura.

## ADR-006 — Dinheiro sem ponto flutuante binário

**Status:** aceita.

### Contexto

Valores financeiros não podem sofrer erros de arredondamento típicos de `float`.

### Decisão

Persistir dinheiro em centavos inteiros. Usar `Decimal` apenas quando cálculos intermediários exigirem escala decimal.

### Consequências

- conversões de entrada e saída precisam ser centralizadas;
- arredondamento deve declarar regra explícita;
- APIs e importadores devem validar escala e moeda.

## ADR-007 — Catálogo canônico de produtos

**Status:** aceita.

### Contexto

Descrições de compras variam entre estabelecimentos e arquivos, dificultando comparação histórica.

### Decisão

Separar produto-base, marca, variante, embalagem, quantidade, unidade, código de barras e aliases.

### Consequências

- comparação de preço pode usar unidade normalizada;
- reconhecimento exige pipeline de normalização e confirmação;
- correções do usuário devem alimentar aliases e regras auditáveis;
- marca desconhecida não pode ser inventada automaticamente.

## ADR-008 — Importação em staging e confirmação

**Status:** aceita.

### Contexto

Arquivos importados podem conter dados inválidos, duplicados ou ambíguos.

### Decisão

Toda importação relevante deve passar por validação, staging, pré-visualização e confirmação antes de criar registros definitivos.

### Consequências

- falhas não deixam dados parciais;
- decisões automáticas podem ser revisadas;
- lotes e linhas importadas precisam de rastreabilidade;
- arquivos devem possuir versão de contrato e hash de origem.

## ADR-009 — Automação explicável

**Status:** aceita.

### Contexto

Categorização e reconhecimento errados podem comprometer relatórios e confiança do usuário.

### Decisão

Sugestões automáticas devem apresentar origem, confiança e possibilidade de correção.

### Consequências

- correspondências devem registrar método e pontuação;
- limites de confiança são configuráveis e calibráveis;
- confirmações e correções geram eventos de aprendizado;
- o sistema não deve ocultar decisões irreversíveis.

## ADR-010 — Relatórios derivados da mesma fonte transacional

**Status:** aceita.

### Contexto

Dashboards e exportações inconsistentes reduzem a confiabilidade do sistema.

### Decisão

Indicadores, gráficos e exportações devem usar consultas e regras compartilhadas, evitando cálculos duplicados na interface.

### Consequências

- serviços de relatório centralizam agregações;
- resultados podem ser testados com cenários conhecidos;
- otimizações futuras podem usar views ou tabelas derivadas sem alterar a semântica.

## Processo para novas decisões

Novas decisões devem ser adicionadas com:

1. identificador sequencial;
2. status: proposta, aceita, substituída ou rejeitada;
3. contexto;
4. decisão;
5. consequências;
6. referência para decisão substituta, quando aplicável.