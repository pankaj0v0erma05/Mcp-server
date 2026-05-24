from datetime import date
from typing import Annotated

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

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

app = FastAPI(
    title="Expense Tracker API",
    description=(
        "Personal expense tracker API. Use this API only with real values "
        "provided by the user or values already stored in the database. "
        "Do not invent expenses, dates, categories, or IDs."
    ),
    version="1.0.0"
)


class ExpenseCreate(BaseModel):
    title: Annotated[
        str,
        Field(
            min_length=1,
            max_length=100,
            description="Expense ka short name. Example: 'Lunch', 'Uber ride'.",
        ),
    ]
    amount: Annotated[
        float,
        Field(
            gt=0,
            description="Expense amount. Positive number only. Currency user context se decide hogi.",
        ),
    ]
    category: Annotated[
        str,
        Field(
            min_length=1,
            max_length=50,
            description="Main category. Example: Food, Travel, Bills, Shopping.",
        ),
    ]
    subcategory: Annotated[
        str | None,
        Field(
            max_length=50,
            description="Optional detailed category. Example: Dinner, Taxi, Electricity.",
        ),
    ] = None
    date: Annotated[
        date,
        Field(description="Expense date in YYYY-MM-DD format. Do not guess if user did not provide it."),
    ]


@app.on_event("startup")
def startup() -> None:
    create_tables()


@app.get(
    "/",
    summary="API health check",
    description="Check karta hai ki Expense Tracker API running hai.",
)
def root():
    return {"message": "Expense Tracker API chal raha hai!"}


@app.post(
    "/expenses",
    status_code=status.HTTP_201_CREATED,
    summary="Add a new expense",
    description=(
        "Naya expense save karta hai. LLM client ko title, amount, category, "
        "and date user se leni chahiye. Missing required fields ko guess nahi karna."
    ),
)
def create_expense(expense: ExpenseCreate):
    return add_expense(
        title=expense.title.strip(),
        amount=expense.amount,
        category=expense.category.strip(),
        subcategory=expense.subcategory.strip() if expense.subcategory else None,
        date=expense.date.isoformat(),
    )


@app.get(
    "/expenses",
    summary="List all expenses",
    description=(
        "Database me saved expenses return karta hai. Optional category, from_date, "
        "and to_date filters use kar sakte ho. Dates YYYY-MM-DD format me honi chahiye."
    ),
)
def list_expenses(
    category: str | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
):
    if not category and not from_date and not to_date:
        return get_expenses()

    return search_expenses(
        category=category.strip() if category else None,
        from_date=from_date.isoformat() if from_date else None,
        to_date=to_date.isoformat() if to_date else None,
    )


@app.get(
    "/expenses/{expense_id}",
    summary="Get one expense by ID",
    description="Specific expense ID ka saved record return karta hai. Agar ID nahi mile to 404.",
)
def read_expense(expense_id: int):
    expense = get_expense(expense_id)

    if expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense nahi mila",
        )

    return expense


@app.put(
    "/expenses/{expense_id}",
    summary="Update one expense by ID",
    description=(
        "Existing expense ko replace/update karta hai. LLM client ko update karne "
        "se pehle exact expense ID confirm karni chahiye."
    ),
)
def edit_expense(expense_id: int, expense: ExpenseCreate):
    updated_expense = update_expense(
        expense_id=expense_id,
        title=expense.title.strip(),
        amount=expense.amount,
        category=expense.category.strip(),
        subcategory=expense.subcategory.strip() if expense.subcategory else None,
        date=expense.date.isoformat(),
    )

    if updated_expense is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense nahi mila",
        )

    return updated_expense


@app.delete(
    "/expenses/{expense_id}",
    summary="Delete one expense by ID",
    description="Specific expense delete karta hai. Delete se pehle user confirmation lena recommended hai.",
)
def remove_expense(expense_id: int):
    deleted = delete_expense(expense_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Expense nahi mila",
        )

    return {"message": "Expense delete ho gaya"}


@app.get(
    "/summary/categories",
    summary="Category-wise expense summary",
    description="Har category ka expense count aur total amount database records se calculate karta hai.",
)
def category_summary():
    return get_summary_by_category()


@app.get(
    "/summary/monthly",
    summary="Month-wise expense summary",
    description="Har YYYY-MM month ka expense count aur total amount database records se calculate karta hai.",
)
def monthly_summary():
    return get_summary_by_month()
