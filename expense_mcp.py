from datetime import date
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from expense_db import (
    add_expense,
    create_tables,
    delete_expense,
    get_expense,
    get_expenses,
    get_summary_by_month,
    get_summary_by_category,
    search_expenses,
    update_expense,
)


mcp = FastMCP(
    "expense-tracker",
    instructions=(
        "This server manages the user's personal expenses stored in SQLite. "
        "Use only the data returned by these tools or explicitly provided by the user. "
        "Never invent expense records, dates, amounts, categories, IDs, or summaries. "
        "If a required value is missing, ask the user for it before calling a tool. "
        "Before deleting an expense, ask the user to confirm the exact expense ID."
    ),
)


def _parse_iso_date(value: str) -> tuple[bool, str]:
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return False, "Date format galat hai. YYYY-MM-DD format use karo."

    return True, parsed.isoformat()


def _clean_text(value: str) -> str:
    return value.strip()


create_tables()


@mcp.tool()
def add_user_expense(
    title: Annotated[
        str,
        Field(description="Expense ka short name. Example: Lunch, Uber ride, Electricity bill."),
    ],
    amount: Annotated[
        float,
        Field(description="Expense amount as a positive number. Do not guess the amount.", gt=0),
    ],
    category: Annotated[
        str,
        Field(description="Main expense category. Example: Food, Travel, Bills, Shopping."),
    ],
    date_text: Annotated[
        str,
        Field(description="Expense date in YYYY-MM-DD format. Ask the user if the date is missing."),
    ],
    subcategory: Annotated[
        str | None,
        Field(description="Optional detailed category. Example: Dinner, Taxi, Electricity."),
    ] = None,
) -> dict:
    """
    Add one expense to the database after the user provides all required fields.

    Use this only when title, amount, category, and date are known. Do not infer
    missing values from context. If the user says "today", convert it to the
    actual current date before calling this tool.

    Args:
        title: User-provided expense name.
        amount: Positive expense amount.
        category: User-provided or user-approved category.
        date_text: Expense date in YYYY-MM-DD format.
        subcategory: Optional user-provided detailed category.
    """
    is_valid_date, normalized_date = _parse_iso_date(date_text)
    if not is_valid_date:
        return {"ok": False, "error": normalized_date}

    cleaned_title = _clean_text(title)
    cleaned_category = _clean_text(category)
    cleaned_subcategory = _clean_text(subcategory) if subcategory else None

    if not cleaned_title:
        return {"ok": False, "error": "Title empty nahi ho sakta."}
    if not cleaned_category:
        return {"ok": False, "error": "Category empty nahi ho sakti."}

    expense = add_expense(
        title=cleaned_title,
        amount=amount,
        category=cleaned_category,
        subcategory=cleaned_subcategory,
        date=normalized_date,
    )

    return {"ok": True, "expense": expense}


@mcp.tool()
def list_user_expenses() -> dict:
    """
    Return all saved expenses from the database.

    Use this before answering questions about existing expenses. Do not mention
    expenses that are not returned by this tool.
    """
    return {"ok": True, "expenses": get_expenses()}


@mcp.tool()
def search_user_expenses(
    category: Annotated[
        str | None,
        Field(description="Optional exact category filter. Use only if the user requested or confirmed it."),
    ] = None,
    from_date: Annotated[
        str | None,
        Field(description="Optional start date in YYYY-MM-DD format. Do not guess missing dates."),
    ] = None,
    to_date: Annotated[
        str | None,
        Field(description="Optional end date in YYYY-MM-DD format. Do not guess missing dates."),
    ] = None,
) -> dict:
    """
    Search saved expenses by optional category and date range.

    Use this for questions like "Food expenses this month" or "expenses between
    two dates" after the date range is known. If the user says a relative date
    like "today" or "this month", convert it to exact YYYY-MM-DD dates before
    calling. Do not invent filters.

    Args:
        category: Optional exact category filter.
        from_date: Optional inclusive start date in YYYY-MM-DD format.
        to_date: Optional inclusive end date in YYYY-MM-DD format.
    """
    normalized_from_date = None
    normalized_to_date = None

    if from_date:
        is_valid_date, normalized_from_date = _parse_iso_date(from_date)
        if not is_valid_date:
            return {"ok": False, "error": normalized_from_date}
    if to_date:
        is_valid_date, normalized_to_date = _parse_iso_date(to_date)
        if not is_valid_date:
            return {"ok": False, "error": normalized_to_date}

    cleaned_category = _clean_text(category) if category else None
    expenses = search_expenses(
        category=cleaned_category,
        from_date=normalized_from_date,
        to_date=normalized_to_date,
    )

    return {"ok": True, "expenses": expenses}


@mcp.tool()
def get_user_expense(
    expense_id: Annotated[
        int,
        Field(description="Exact expense ID to fetch. Use an ID returned by list_user_expenses."),
    ],
) -> dict:
    """
    Return one saved expense by exact database ID.

    Use this when the user asks about a specific expense. If no record is found,
    say that the expense was not found instead of inventing details.

    Args:
        expense_id: Existing expense ID.
    """
    expense = get_expense(expense_id)
    if expense is None:
        return {"ok": False, "error": "Expense nahi mila."}

    return {"ok": True, "expense": expense}


@mcp.tool()
def update_user_expense(
    expense_id: Annotated[
        int,
        Field(description="Exact expense ID to update. Use an ID returned by list/search/get tools."),
    ],
    title: Annotated[
        str,
        Field(description="Updated expense name. Do not guess this value."),
    ],
    amount: Annotated[
        float,
        Field(description="Updated positive expense amount. Do not guess this value.", gt=0),
    ],
    category: Annotated[
        str,
        Field(description="Updated main category. Ask user if unclear."),
    ],
    date_text: Annotated[
        str,
        Field(description="Updated date in YYYY-MM-DD format. Ask user if missing."),
    ],
    subcategory: Annotated[
        str | None,
        Field(description="Optional updated subcategory."),
    ] = None,
) -> dict:
    """
    Update one existing expense by exact database ID.

    Use this only after the user confirms which expense should change and
    provides the replacement values. This tool replaces the whole expense record,
    so do not fill missing fields from imagination. First call get_user_expense
    if you need to show the current saved values to the user.

    Args:
        expense_id: Existing expense ID.
        title: Updated title.
        amount: Updated positive amount.
        category: Updated category.
        date_text: Updated date in YYYY-MM-DD format.
        subcategory: Optional updated subcategory.
    """
    is_valid_date, normalized_date = _parse_iso_date(date_text)
    if not is_valid_date:
        return {"ok": False, "error": normalized_date}

    cleaned_title = _clean_text(title)
    cleaned_category = _clean_text(category)
    cleaned_subcategory = _clean_text(subcategory) if subcategory else None

    if not cleaned_title:
        return {"ok": False, "error": "Title empty nahi ho sakta."}
    if not cleaned_category:
        return {"ok": False, "error": "Category empty nahi ho sakti."}

    expense = update_expense(
        expense_id=expense_id,
        title=cleaned_title,
        amount=amount,
        category=cleaned_category,
        subcategory=cleaned_subcategory,
        date=normalized_date,
    )

    if expense is None:
        return {"ok": False, "error": "Expense nahi mila. Kuch update nahi hua."}

    return {"ok": True, "expense": expense}


@mcp.tool()
def delete_user_expense(
    expense_id: Annotated[
        int,
        Field(description="Exact expense ID to delete. Ask user confirmation before using this tool."),
    ],
) -> dict:
    """
    Delete one saved expense by exact database ID.

    Use this only after the user confirms the exact ID to delete. If the ID does
    not exist, report that no expense was deleted.

    Args:
        expense_id: Existing expense ID to delete.
    """
    deleted = delete_expense(expense_id)
    if not deleted:
        return {"ok": False, "error": "Expense nahi mila. Kuch delete nahi hua."}

    return {"ok": True, "message": "Expense delete ho gaya."}


@mcp.tool()
def summarize_expenses_by_category() -> dict:
    """
    Return category-wise expense totals calculated from stored database records.

    Use this for questions like total spending by category. Do not calculate from
    memory or guess missing categories; rely on this tool result.
    """
    return {"ok": True, "summary": get_summary_by_category()}


@mcp.tool()
def summarize_expenses_by_month() -> dict:
    """
    Return month-wise expense totals calculated from stored database records.

    Use this for questions like monthly spending trends or "which month was
    highest". Do not calculate from memory; rely on this tool result.
    """
    return {"ok": True, "summary": get_summary_by_month()}


if __name__ == "__main__":
    mcp.run()
