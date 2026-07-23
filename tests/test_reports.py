from datetime import date

from financeiro_kairo.application.schemas import AccountCreate, TransactionCreate
from financeiro_kairo.application.services.finance import FinanceService
from financeiro_kairo.application.services.reports import ReportService
from financeiro_kairo.domain.models import AccountType, TransactionType


def test_summary_and_pagination(session, tmp_path):
    finance = FinanceService(session)
    account = finance.create_account(
        AccountCreate(name="Carteira", account_type=AccountType.CASH.value)
    )
    finance.create_transaction(
        TransactionCreate(
            transaction_type=TransactionType.INCOME.value,
            description="Pagamento",
            amount_cents=200_000,
            occurred_on=date(2026, 7, 1),
            account_id=account.id,
        )
    )
    finance.create_transaction(
        TransactionCreate(
            transaction_type=TransactionType.EXPENSE.value,
            description="Mercado",
            amount_cents=50_000,
            occurred_on=date(2026, 7, 2),
            account_id=account.id,
        )
    )

    reports = ReportService(session)
    summary = reports.summary(date(2026, 7, 1), date(2026, 7, 31))
    assert summary.income_cents == 200_000
    assert summary.expense_cents == 50_000
    assert summary.net_cents == 150_000

    rows, total = reports.transactions_page(page=1, page_size=1)
    assert total == 2
    assert len(rows) == 1

    excel = reports.export_transactions_excel(rows, tmp_path / "relatorio.xlsx")
    pdf = reports.export_summary_pdf(
        start=date(2026, 7, 1),
        end=date(2026, 7, 31),
        target=tmp_path / "relatorio.pdf",
    )
    assert excel.is_file()
    assert pdf.is_file()
