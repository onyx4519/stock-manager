from pydantic import BaseModel, Field


class DartCompany(BaseModel):
    corp_code: str = Field(pattern=r"^\d{8}$")
    corp_name: str
    corp_eng_name: str | None = None
    stock_code: str | None = Field(default=None, pattern=r"^\d{6}$")
    modify_date: str | None = Field(default=None, pattern=r"^\d{8}$")
