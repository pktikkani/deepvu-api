from typing import Any

from pydantic import BaseModel


class TableColumn(BaseModel):
    key: str
    label: str
    sortable: bool = True


class TableSchema(BaseModel):
    key: str
    label: str
    columns: list[TableColumn] = []
    layout: str | None = None


class ChartConfig(BaseModel):
    key: str
    label: str
    type: str  # "pie", "bar", "line", etc.


class FilterConfig(BaseModel):
    key: str
    label: str
    type: str = "dropdown"
    layout: str | None = None  # "inline" for side-by-side


class SubTab(BaseModel):
    key: str
    label: str
    charts: list[ChartConfig] = []
    tables: list[TableSchema] = []


class DashboardTab(BaseModel):
    key: str
    label: str
    order: int
    sub_tabs: list[SubTab] = []
    filters: list[FilterConfig] = []
    charts: list[ChartConfig] = []
    tables: list[TableSchema] = []


class DashboardConfigResponse(BaseModel):
    dashboard_type: str
    tabs: list[DashboardTab]
