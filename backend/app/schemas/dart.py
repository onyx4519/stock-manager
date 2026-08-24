from datetime import date

from pydantic import BaseModel, Field


class DartCompany(BaseModel):
    corp_code: str = Field(pattern=r"^\d{8}$")
    corp_name: str
    corp_eng_name: str | None = None
    stock_code: str | None = Field(default=None, pattern=r"^\d{6}$")
    modify_date: str | None = Field(default=None, pattern=r"^\d{8}$")


class DartDisclosure(BaseModel):
    corporation_class: str
    corporation_name: str
    corporation_code: str = Field(pattern=r"^\d{8}$")
    stock_code: str | None = Field(default=None, pattern=r"^\d{6}$")
    report_name: str
    receipt_number: str = Field(pattern=r"^\d{14}$")
    filer_name: str
    receipt_date: date
    remarks: str | None = None
    viewer_url: str


class DartDisclosureList(BaseModel):
    company: DartCompany
    total_count: int = Field(ge=0)
    items: list[DartDisclosure]


class DartFinancialAccount(BaseModel):
    receipt_number: str = Field(pattern=r"^\d{14}$")
    business_year: str = Field(pattern=r"^\d{4}$")
    report_code: str = Field(pattern=r"^\d{5}$")
    account_name: str
    financial_statement_division: str
    financial_statement_name: str
    statement_division: str
    statement_name: str
    current_term_name: str | None = None
    current_term_date: str | None = None
    current_term_amount: int | None = None
    current_term_cumulative_amount: int | None = None
    previous_term_name: str | None = None
    previous_term_date: str | None = None
    previous_term_amount: int | None = None
    currency: str | None = None


class DartFinancialStatement(BaseModel):
    company: DartCompany
    business_year: str = Field(pattern=r"^\d{4}$")
    report_code: str = Field(pattern=r"^\d{5}$")
    financial_statement_division: str | None = None
    accounts: list[DartFinancialAccount]
