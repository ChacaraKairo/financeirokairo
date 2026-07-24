# 16. Manual completo do usuário

Este manual explica como instalar, abrir, usar, proteger e manter o Financeiro Kairo no dia a dia.

O Financeiro Kairo é uma aplicação desktop local e offline para gestão financeira pessoal e familiar. Os dados ficam em um banco SQLite no computador do usuário, sem dependência de nuvem.

## 1. Conceitos principais

### Banco local

O app grava as informações em um arquivo SQLite local. Por padrão, o arquivo fica em:

```text
~/.local/share/financeiro-kairo/financeiro-kairo.sqlite3
```

Esse arquivo contém contas, transações, categorias, compras, metas, orçamentos, despesas recorrentes, parcelas e demais dados do sistema.

### Contas

Contas representam onde o dinheiro entra, sai ou é controlado. Exemplos:

- conta corrente;
- poupança;
- dinheiro;
- cartão de crédito;
- carteira digital;
- investimento.

O saldo exibido considera saldo inicial, receitas, despesas e transferências registradas na conta.

### Categorias

Categorias classificam receitas e despesas. Elas ajudam a entender onde o dinheiro está sendo gasto ou recebido.

Categorias podem ter uma categoria superior, formando subcategorias.

### Transações

Transações são lançamentos financeiros individuais:

- receita;
- despesa.

Cada transação possui descrição, valor, data, conta e categoria opcional.

### Compras

Compras registram uma compra detalhada, normalmente importada por JSON, com estabelecimento, data, total e itens.

### Planejamento

O planejamento reúne:

- orçamentos mensais;
- metas financeiras;
- parcelamentos.

### Despesas recorrentes

Despesas recorrentes são contas que se repetem mensalmente, como aluguel, internet, energia, mensalidades e assinaturas.

Elas podem ter valor fixo ou variável.

### Backups

Backup é uma cópia validada do banco SQLite. Ele é essencial porque os dados são locais.

## 2. Requisitos

Para uso em desenvolvimento ou execução local:

- Linux desktop;
- Python 3.12 ou superior;
- ambiente virtual Python;
- bibliotecas gráficas Qt disponíveis no sistema.

No Kubuntu/Ubuntu:

```bash
sudo apt update
sudo apt install -y python3.12-venv libegl1 libgl1 libxkbcommon-x11-0
```

## 3. Instalação para desenvolvimento

Na primeira instalação:

```bash
git clone https://github.com/ChacaraKairo/financeirokairo.git
cd financeirokairo

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

Se o projeto já está baixado:

```bash
cd /home/chacara/Desenvolvimento/Projetos/financeirokairo/financeirokairo
source .venv/bin/activate
```

## 4. Primeira execução

Antes de abrir a interface, aplique as migrações:

```bash
financeiro-kairo migrate
```

Depois abra o app:

```bash
financeiro-kairo-desktop
```

Se quiser apenas criar as tabelas diretamente em um ambiente descartável:

```bash
financeiro-kairo init-db
```

Para uma base persistente de uso real, prefira `financeiro-kairo migrate`.

## 5. Alterar o local dos dados

Por padrão, o banco fica em `~/.local/share/financeiro-kairo/`.

Para usar outro diretório:

```bash
export FINANCEIRO_KAIRO_DATA_DIR=/caminho/desejado
financeiro-kairo migrate
financeiro-kairo-desktop
```

Também é possível configurar:

- `FINANCEIRO_KAIRO_DATABASE_NAME`;
- `FINANCEIRO_KAIRO_BACKUP_DIR`;
- `FINANCEIRO_KAIRO_SQLITE_ECHO`.

## 6. Visão geral da interface

A janela principal possui um menu lateral. Cada item abre um módulo:

1. Visão geral
2. Transações
3. Contas
4. Categorias
5. Compras
6. Planejamento
7. Despesas recorrentes
8. Gráficos
9. Relatórios e cópias
10. Banco de dados
11. Console SQL

Ao trocar de tela, o app tenta atualizar os dados automaticamente.

## 7. Tela Visão geral

A tela **Visão geral** mostra um resumo financeiro do mês atual.

Ela exibe:

- saldo consolidado;
- receitas do mês;
- despesas do mês;
- resultado do mês;
- despesas agrupadas por categoria;
- fatura atual do cartão de crédito.

### Como o saldo consolidado é calculado

O saldo consolidado soma os saldos das contas cadastradas.

Cada saldo considera:

- saldo inicial da conta;
- receitas registradas;
- despesas registradas;
- transferências registradas pelo serviço financeiro.

### Despesas por categoria

A tabela de categorias mostra quanto foi gasto em cada categoria no período mensal atual.

Se uma despesa não tiver categoria, ela aparece como sem categoria nos relatórios internos.

### Fatura do cartão de crédito

A seção **Fatura do cartão de crédito** mostra:

- total atual do mês em cartões de crédito;
- total por cartão;
- lançamentos recentes feitos em contas do tipo cartão de crédito.

Importante: no modelo atual ainda não existe cadastro de dia de fechamento e vencimento da fatura. Portanto, a fatura exibida usa o mês atual como período.

Para uma transação entrar nessa fatura:

1. a conta da transação deve ser do tipo `Cartão de crédito`;
2. a transação deve ser uma despesa;
3. a data deve estar dentro do mês atual.

## 8. Tela Transações

A tela **Transações** serve para consultar, criar, editar e apagar receitas e despesas.

### Campos de uma transação

- **Descrição:** texto que identifica o lançamento.
- **Valor:** valor em reais.
- **Tipo:** despesa ou receita.
- **Conta:** conta vinculada ao lançamento.
- **Categoria:** classificação opcional.
- **Data:** data em que a transação ocorreu.

### Criar transação

1. Abra **Transações**.
2. Clique em **Nova transação**.
3. Informe a descrição.
4. Informe o valor.
5. Escolha se é despesa ou receita.
6. Escolha a conta.
7. Escolha uma categoria, se fizer sentido.
8. Escolha a data.
9. Clique em **Salvar**.

### Buscar transação

1. Digite parte da descrição no campo de busca.
2. Pressione `Enter`.

A lista será atualizada com os resultados encontrados.

### Editar transação

1. Selecione uma linha na tabela.
2. Clique em **Editar**.
3. Altere os campos desejados.
4. Clique em **Salvar**.

### Apagar transação

1. Selecione uma linha.
2. Clique em **Apagar**.
3. Confirme a exclusão.

A exclusão remove o lançamento do banco. Essa ação afeta saldos, relatórios, gráficos e fatura do cartão.

## 9. Tela Contas

A tela **Contas** mostra as contas cadastradas e seus saldos.

### Tipos de conta

- conta corrente;
- poupança;
- dinheiro;
- cartão de crédito;
- carteira digital;
- investimento;
- outro.

### Criar conta

1. Abra **Contas**.
2. Clique em **Nova conta**.
3. Informe o nome.
4. Escolha o tipo.
5. Informe o saldo inicial.
6. Mantenha **Conta ativa** marcado.
7. Clique em **Salvar**.

### Editar conta

1. Selecione a conta.
2. Clique em **Editar**.
3. Ajuste nome, tipo, saldo inicial ou situação.
4. Clique em **Salvar**.

### Apagar conta

1. Selecione a conta.
2. Clique em **Apagar**.
3. Confirme.

Se a conta estiver vinculada a transações, compras, despesas recorrentes ou parcelamentos, o banco pode impedir a exclusão. Nesse caso, mantenha a conta inativa em vez de apagar.

### Conta ativa e inativa

Uma conta inativa deixa de aparecer em seletores de novos lançamentos, mas permanece no histórico.

## 10. Tela Categorias

A tela **Categorias** organiza receitas e despesas.

### Criar categoria

1. Abra **Categorias**.
2. Clique em **Nova categoria**.
3. Informe o nome.
4. Escolha o tipo:
   - receita;
   - despesa;
   - ambos.
5. Escolha uma categoria superior, se for uma subcategoria.
6. Clique em **Salvar**.

### Editar categoria

1. Selecione a categoria.
2. Clique em **Editar**.
3. Altere nome, tipo, categoria superior ou situação.
4. Clique em **Salvar**.

O sistema impede ciclos, por exemplo uma categoria ser filha dela mesma ou de uma descendente.

### Arquivar categoria

1. Selecione a categoria.
2. Clique em **Arquivar selecionada**.

Arquivar é mais seguro do que apagar quando a categoria já foi usada.

### Apagar categoria

1. Selecione a categoria.
2. Clique em **Apagar**.
3. Confirme.

Se a categoria estiver vinculada a dados existentes, a exclusão pode ser recusada pelo banco.

## 11. Tela Compras

A tela **Compras e importações** lista compras registradas e permite importar arquivos JSON.

### O que aparece na tabela

- data da compra;
- estabelecimento;
- quantidade de itens;
- total;
- origem.

### Importar arquivo JSON

1. Abra **Compras**.
2. Clique em **Importar arquivo JSON**.
3. Selecione um arquivo `.json`.
4. Aguarde a validação.
5. Se a importação for aceita, o app exibirá o número da compra importada.

### Validações da importação

O app valida:

- formato JSON;
- campos obrigatórios;
- quantidades positivas;
- valores monetários válidos;
- soma dos itens compatível com o total;
- duplicidade pelo hash do payload.

Se o mesmo conteúdo já tiver sido importado, a importação é bloqueada.

### Formato JSON aceito atualmente

O formato aceito pelo validador atual segue esta estrutura:

```json
{
  "source": "mercado-json",
  "currency": "BRL",
  "purchase": {
    "store_name": "Supermercado Exemplo",
    "purchase_date": "2026-07-22",
    "document_number": "12345",
    "account_id": 1,
    "items": [
      {
        "line_no": 1,
        "description": "ARROZ TIPO 1 5KG",
        "brand": "Camil",
        "quantity": "1",
        "unit_label": "un",
        "unit_price": "29.90",
        "line_total": "29.90",
        "discount": "0.00"
      }
    ],
    "totals": {
      "gross_total": "29.90",
      "discount_total": "0.00",
      "net_total": "29.90"
    }
  }
}
```

Campos importantes:

- `source`: origem da importação. Valores aceitos: `mercado-json`, `api`, `manual`, `csv-convertido`.
- `currency`: atualmente `BRL`.
- `purchase.store_name`: nome do estabelecimento.
- `purchase.purchase_date`: data da compra.
- `purchase.account_id`: conta vinculada, opcional.
- `items`: lista de itens.
- `totals`: totais da compra.

### Editar compra

1. Selecione uma compra.
2. Clique em **Editar**.
3. Altere data, estabelecimento, total, origem, documento ou conta.
4. Clique em **Salvar**.

A edição atual altera o cabeçalho da compra. Os itens importados permanecem vinculados à compra.

### Apagar compra

1. Selecione uma compra.
2. Clique em **Apagar**.
3. Confirme.

Ao apagar uma compra, seus itens também podem ser removidos conforme as regras de relacionamento do banco.

## 12. Tela Planejamento

A tela **Planejamento** possui três abas:

- Orçamentos;
- Metas;
- Parcelas.

### Aba Orçamentos

Use orçamentos para definir limites de gasto por período.

#### Criar orçamento mensal

1. Informe o nome do orçamento.
2. Informe o limite.
3. Clique em **Criar orçamento mensal**.

O app cria o orçamento para o mês atual, do primeiro dia até o último dia do mês.

#### Editar orçamento

1. Selecione um orçamento.
2. Clique em **Editar**.
3. Ajuste nome, início, fim, limite ou situação.
4. Clique em **Salvar**.

#### Apagar orçamento

1. Selecione um orçamento.
2. Clique em **Apagar**.
3. Confirme.

### Aba Metas

Use metas para acompanhar objetivos financeiros.

#### Criar meta

1. Informe o nome da meta.
2. Informe o valor alvo.
3. Clique em **Criar meta**.

#### Contribuir para meta

1. Selecione uma meta.
2. Clique em **Adicionar R$ 100 à selecionada**.

O valor atual da meta aumenta em R$ 100.

#### Editar meta

1. Selecione uma meta.
2. Clique em **Editar**.
3. Ajuste nome, valor atual, valor alvo ou situação.
4. Clique em **Salvar**.

#### Apagar meta

1. Selecione uma meta.
2. Clique em **Apagar**.
3. Confirme.

Contribuições vinculadas podem ser removidas junto da meta conforme as regras do banco.

### Aba Parcelas

Use parcelamentos para controlar compras ou compromissos pagos em várias parcelas.

#### Criar parcelamento

1. Informe a descrição.
2. Informe o valor total.
3. Informe o número de parcelas.
4. Escolha a conta.
5. Clique em **Criar parcelamento**.

O app divide o valor total pelo número de parcelas. Se houver centavos restantes, eles são distribuídos entre as primeiras parcelas.

#### Pagar parcela

1. Selecione uma parcela.
2. Clique em **Pagar parcela selecionada**.

Ao pagar, o app cria uma transação de despesa na data atual.

#### Editar parcela

1. Selecione uma parcela.
2. Clique em **Editar parcela**.
3. Altere vencimento ou valor.
4. Clique em **Salvar**.

Parcelas já pagas não podem ser editadas.

#### Apagar parcelamento

1. Selecione qualquer parcela do parcelamento.
2. Clique em **Apagar parcelamento**.
3. Confirme.

Parcelamentos com parcelas pagas não podem ser apagados pela tela.

## 13. Tela Despesas recorrentes

A tela **Despesas recorrentes** possui duas abas:

- Cadastros;
- Contas do mês.

### Aba Cadastros

Nesta aba você cadastra despesas que se repetem.

#### Criar despesa recorrente

1. Clique em **Nova despesa recorrente**.
2. Informe a descrição.
3. Escolha o tipo de valor:
   - valor fixo;
   - valor variável a cada mês.
4. Se for valor fixo, informe o valor.
5. Informe o dia de vencimento.
6. Informe o lembrete em dias antes.
7. Escolha a conta de pagamento.
8. Escolha uma categoria, se quiser.
9. Mantenha **Despesa ativa** marcada.
10. Clique em **Salvar**.

#### Editar despesa recorrente

1. Selecione uma despesa recorrente.
2. Clique em **Editar selecionada**.
3. Altere os campos necessários.
4. Clique em **Salvar**.

#### Apagar despesa recorrente

1. Selecione uma despesa recorrente.
2. Clique em **Apagar selecionada**.
3. Confirme.

Se houver ocorrências mensais já pagas, o app impede a exclusão.

### Aba Contas do mês

Nesta aba aparecem as ocorrências do mês de referência.

O app gera automaticamente as competências mensais das despesas ativas.

#### Selecionar mês

1. Altere o campo **Mês de referência**.
2. A lista será atualizada para o mês escolhido.

#### Informar valor variável

1. Selecione uma despesa variável.
2. Clique em **Informar valor**.
3. Digite o valor do mês.
4. Confirme.

Despesas fixas não precisam dessa etapa.

#### Marcar como paga

1. Selecione uma conta do mês.
2. Clique em **Marcar como paga**.

O app cria uma transação de despesa para representar o pagamento.

#### Marcar como não paga

1. Selecione uma conta paga.
2. Clique em **Marcar como não paga**.
3. Confirme.

O app remove a transação gerada pelo pagamento e reabre a ocorrência.

### Lembretes

Quando há contas próximas do vencimento ou atrasadas, a tela exibe um aviso com os lembretes de pagamento.

## 14. Tela Gráficos

A tela **Gráficos** mostra as despesas do mês agrupadas por categoria.

Tipos disponíveis:

- Pizza;
- Barras;
- Linha.

Para trocar:

1. Abra **Gráficos**.
2. Selecione o tipo no campo **Tipo do gráfico**.

O gráfico usa os dados do mês atual.

## 15. Tela Relatórios e cópias

A tela **Relatórios e segurança** reúne exportação e backup.

### Exportar para Excel

1. Clique em **Exportar para Excel**.
2. Escolha onde salvar o arquivo `.xlsx`.
3. Confirme.

O relatório exporta transações do período atual do mês.

### Exportar para PDF

1. Clique em **Exportar para PDF**.
2. Escolha onde salvar o arquivo `.pdf`.
3. Confirme.

O PDF inclui resumo financeiro e despesas por categoria.

### Criar cópia de segurança

1. Clique em **Criar cópia de segurança**.
2. Aguarde a mensagem de confirmação.

O backup é salvo no diretório de backups configurado. Por padrão:

```text
~/.local/share/financeiro-kairo/backups/
```

O arquivo recebe nome com data e hora:

```text
financeiro-kairo-YYYYMMDD-HHMMSS.sqlite3
```

### Restaurar cópia de segurança

1. Clique em **Restaurar cópia de segurança**.
2. Selecione um arquivo `.sqlite3` ou `.db`.
3. Confirme a restauração.

Antes de restaurar, o app cria uma cópia preventiva da base atual. Após restaurar, reinicie o aplicativo.

## 16. Tela Banco de dados

A tela **Banco de dados** permite visualizar a estrutura e os dados brutos do SQLite em modo somente leitura.

Ela é útil para:

- conferir tabelas;
- verificar registros;
- entender o modelo de dados;
- copiar a estrutura SQL;
- salvar uma cópia do arquivo SQLite.

### Lista de tabelas

À esquerda aparece a lista de tabelas.

Cada item mostra:

- nome da tabela;
- quantidade de registros.

Ao selecionar uma tabela, a tela mostra:

- descrição da tabela;
- colunas;
- linhas carregadas.

### Mostrar tabelas internas

Marque **Mostrar tabelas internas do SQLite** para incluir tabelas como:

- `sqlite_sequence`;
- outras tabelas internas, se existirem.

### Limite de linhas

O campo **Limite de linhas** controla quantos registros serão carregados na grade.

Use limites menores para tabelas grandes.

### Atualizar

Clique em **Atualizar** para recarregar a lista de tabelas e os dados da tabela selecionada.

### Copiar estrutura SQL

Clique em **Copiar estrutura SQL** para copiar para a área de transferência um SQL contendo apenas:

- nomes das tabelas;
- nomes dos campos;
- tipos dos campos.

O conteúdo copiado não inclui dados.

Exemplo de saída:

```sql
CREATE TABLE "accounts" (
    "id" INTEGER,
    "name" VARCHAR(120),
    "account_type" VARCHAR(30)
);
```

Esse recurso é útil para colar a estrutura do banco em documentação, IA, ferramentas de modelagem ou revisão técnica.

### Baixar arquivo SQLite

Clique em **Baixar arquivo SQLite** para salvar uma cópia do banco em outro local.

O app usa o mecanismo de backup do SQLite para gerar uma cópia consistente.

## 17. Tela Console SQL

A tela **Console SQL** permite executar comandos SQL manualmente.

Por padrão, o console aceita somente comandos de leitura:

- `SELECT`;
- `WITH`;
- `PRAGMA`;
- `EXPLAIN`.

### Executar consulta

1. Digite a consulta no editor.
2. Ajuste o limite de linhas, se necessário.
3. Clique em **Executar SQL**.

O resultado aparece na grade.

### Histórico

As consultas executadas ficam no histórico da sessão.

Para reutilizar:

1. Dê duplo clique em uma consulta do histórico.
2. Ela volta para o editor.

### Comandos que alteram dados

Existe a opção **Permitir comandos que alteram dados**.

Use somente se souber exatamente o que está fazendo. Ao marcar essa opção, o app pedirá confirmação antes de executar.

Comandos de escrita podem alterar ou apagar dados permanentemente.

Antes de usar escrita manual:

1. faça backup;
2. valide o backup;
3. execute o comando;
4. confira o resultado;
5. faça novo backup se estiver tudo correto.

## 18. Comandos administrativos

Os comandos administrativos usam o executável `financeiro-kairo`.

### Aplicar migrações

```bash
financeiro-kairo migrate
```

Use após atualizar o código ou antes da primeira execução.

### Criar schema diretamente

```bash
financeiro-kairo init-db
```

Útil para ambientes descartáveis.

### Criar backup

```bash
financeiro-kairo backup
```

### Validar backup

```bash
financeiro-kairo validate-backup /caminho/backup.sqlite3
```

### Restaurar backup

```bash
financeiro-kairo restore /caminho/backup.sqlite3
```

### Rotacionar backups

```bash
financeiro-kairo rotate-backups --keep 30
```

Mantém os 30 backups mais recentes e remove os demais.

## 19. Rotina recomendada de uso

### Primeira configuração

1. Rode `financeiro-kairo migrate`.
2. Abra `financeiro-kairo-desktop`.
3. Cadastre contas.
4. Cadastre categorias principais.
5. Cadastre despesas recorrentes.
6. Cadastre metas e orçamentos.
7. Faça um backup inicial.

### Uso diário

1. Registre receitas e despesas.
2. Confira a visão geral.
3. Atualize despesas recorrentes variáveis.
4. Marque contas recorrentes pagas.
5. Confira a fatura do cartão.

### Uso semanal

1. Revise categorias.
2. Confira gráficos.
3. Confira orçamentos e metas.
4. Faça backup.

### Uso mensal

1. Exporte relatórios.
2. Revise despesas do mês.
3. Compare categorias.
4. Confira parcelamentos.
5. Valide e guarde um backup.

## 20. Boas práticas

### Categorias

Crie categorias simples e claras.

Exemplos:

- Alimentação;
- Transporte;
- Moradia;
- Saúde;
- Educação;
- Lazer;
- Assinaturas;
- Investimentos.

Evite criar categorias parecidas demais, como `Mercado`, `Supermercado`, `Compras mercado`, se todas significam a mesma coisa.

### Contas

Use nomes fáceis de reconhecer:

- Conta principal;
- Carteira;
- Cartão Nubank;
- Poupança reserva;
- Investimento corretora.

Para cartões, use sempre o tipo **Cartão de crédito**. Isso permite que a fatura apareça corretamente na visão geral.

### Backups

Faça backups antes de:

- restaurar dados;
- usar Console SQL com escrita;
- apagar muitos registros;
- atualizar o app;
- editar manualmente o banco.

Guarde cópias fora do computador principal.

### Exclusões

Prefira arquivar ou inativar quando houver histórico.

Apagar é útil para:

- lançamentos criados por engano;
- dados de teste;
- cadastros duplicados sem uso.

## 21. Solução de problemas

### O app não abre

Confirme que o ambiente virtual está ativo:

```bash
source .venv/bin/activate
```

Depois rode:

```bash
financeiro-kairo migrate
financeiro-kairo-desktop
```

### Erro em migrações

Rode:

```bash
financeiro-kairo migrate
```

Se o erro persistir, faça backup do arquivo SQLite antes de qualquer correção manual.

### Não consigo apagar uma conta ou categoria

Isso normalmente acontece quando há registros vinculados.

Soluções:

- inativar a conta;
- arquivar a categoria;
- remover ou alterar os registros vinculados antes de apagar.

### A fatura do cartão não mostra uma despesa

Confira:

1. a conta da despesa está cadastrada como **Cartão de crédito**;
2. a transação é do tipo **Despesa**;
3. a data está no mês atual;
4. a transação foi salva corretamente.

### Despesa recorrente variável não permite pagamento

Antes de pagar, informe o valor do mês:

1. abra **Despesas recorrentes**;
2. vá para **Contas do mês**;
3. selecione a despesa;
4. clique em **Informar valor**;
5. depois clique em **Marcar como paga**.

### Importação JSON falha

Confira:

- se o arquivo é JSON válido;
- se está em UTF-8;
- se os campos seguem o formato aceito;
- se os totais batem com a soma dos itens;
- se o arquivo não foi importado antes.

### Backup inválido

Não use o arquivo.

Crie um novo backup:

```bash
financeiro-kairo backup
```

Valide:

```bash
financeiro-kairo validate-backup /caminho/backup.sqlite3
```

## 22. Limitações atuais

O app já cobre o fluxo central de gestão financeira local, mas algumas áreas ainda têm limitações:

- a fatura do cartão usa o mês atual, sem fechamento e vencimento personalizados;
- compras importadas têm edição de cabeçalho, mas não edição item a item pela interface;
- relatórios usam o mês atual na interface principal;
- o Console SQL exige cuidado, pois comandos de escrita podem alterar dados diretamente;
- não há sincronização em nuvem;
- não há criptografia do banco local.

## 23. Checklist rápido

Para começar bem:

- [ ] Rodar migrações.
- [ ] Criar contas.
- [ ] Criar categorias.
- [ ] Registrar primeiras transações.
- [ ] Criar despesas recorrentes.
- [ ] Criar orçamento do mês.
- [ ] Criar metas.
- [ ] Fazer backup.
- [ ] Testar validação do backup.

## 24. Referências internas

- [README](../README.md)
- [Índice da documentação](00-indice.md)
- [Execução e desenvolvimento](15-execucao-e-desenvolvimento.md)
- [Segurança e backup](09-seguranca-e-backup.md)
- [Importação JSON](05-importacao-json.md)
