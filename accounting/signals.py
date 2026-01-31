# accounting/utils/coa_seed.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from django.db import transaction
from django.core.exceptions import ValidationError

# ✅ Adjust this import to your actual app label where ChartofAccounts lives
from accounting.models import ChartofAccounts


@dataclass(frozen=True)
class COARow:
    code: str
    name: str
    type: str  # asset/liability/equity/income/expense
    parent: Optional[str] = None
    description: Optional[str] = None


# Practical SME-friendly default COA (tree)
DEFAULT_COA: List[COARow] = [
    # ASSETS (1000-1999)
    COARow("1000", "Assets", "asset"),
    COARow("1100", "Current Assets", "asset", parent="1000"),
    COARow("1110", "Cash on Hand", "asset", parent="1100"),
    COARow("1120", "Bank Accounts", "asset", parent="1100"),
    COARow("1130", "Accounts Receivable", "asset", parent="1100"),
    COARow("1140", "Inventory", "asset", parent="1100"),
    COARow("1150", "Advances & Prepayments", "asset", parent="1100"),
    COARow("1200", "Non-Current Assets", "asset", parent="1000"),
    COARow("1210", "Property, Plant & Equipment", "asset", parent="1200"),
    COARow("1220", "Accumulated Depreciation", "asset", parent="1200", description="Contra-asset"),

    # LIABILITIES (2000-2999)
    COARow("2000", "Liabilities", "liability"),
    COARow("2100", "Current Liabilities", "liability", parent="2000"),
    COARow("2110", "Accounts Payable", "liability", parent="2100"),
    COARow("2120", "Taxes Payable", "liability", parent="2100"),
    COARow("2130", "Salaries Payable", "liability", parent="2100"),
    COARow("2200", "Non-Current Liabilities", "liability", parent="2000"),
    COARow("2210", "Loans Payable", "liability", parent="2200"),

    # EQUITY (3000-3999)
    COARow("3000", "Equity", "equity"),
    COARow("3100", "Owner's Capital", "equity", parent="3000"),
    COARow("3200", "Retained Earnings", "equity", parent="3000"),
    COARow("3300", "Current Year Profit/Loss", "equity", parent="3000"),

    # INCOME (4000-4999)
    COARow("4000", "Income", "income"),
    COARow("4100", "Sales / Service Revenue", "income", parent="4000"),
    COARow("4200", "Other Income", "income", parent="4000"),

    # DIRECT COSTS / COGS (commonly kept under expense in many SMEs)
    COARow("5000", "Cost of Sales", "expense", description="Often treated as Expense in SME ledgers"),
    COARow("5100", "Purchases / Direct Costs", "expense", parent="5000"),
    COARow("5200", "Freight / Direct Expenses", "expense", parent="5000"),

    # EXPENSES (6000-6999)
    COARow("6000", "Operating Expenses", "expense"),
    COARow("6100", "Rent Expense", "expense", parent="6000"),
    COARow("6200", "Utilities Expense", "expense", parent="6000"),
    COARow("6300", "Salaries & Wages", "expense", parent="6000"),
    COARow("6400", "Marketing Expense", "expense", parent="6000"),
    COARow("6500", "Office Expense", "expense", parent="6000"),
    COARow("6600", "Depreciation Expense", "expense", parent="6000"),
]


def seed_coa_for_master(master, *, user=None, force: bool = False) -> Dict[str, Any]:
    """
    Seeds DEFAULT_COA into master.branch.

    master: any object that has master.branch set (required)
    user: value for user_add (optional)
    force:
      - False: if ANY COA exists for branch -> skip entirely
      - True: create missing ones (does NOT delete/update existing)
    """
    if not hasattr(master, "branch") or master.branch is None:
        raise ValidationError("master.branch is required to seed COA")

    branch = master.branch

    existing_qs = ChartofAccounts.objects.filter(branch=branch)
    if existing_qs.exists() and not force:
        return {"created": 0, "skipped": True, "reason": "COA already exists for this branch."}

    # Map existing by code (force mode uses this to skip duplicates)
    existing_by_code = {
        c.code: c
        for c in existing_qs.only("id", "code", "parent_account_id", "type")
    }

    code_to_obj = dict(existing_by_code)
    created_count = 0

    # We'll insert parents first, children later (order-agnostic loop)
    pending = list(DEFAULT_COA)

    with transaction.atomic():
        # Optional: lock existing COA rows for this branch to avoid race conditions
        ChartofAccounts.objects.select_for_update().filter(branch=branch)

        safety = 0
        while pending:
            safety += 1
            if safety > 80:
                raise ValidationError("COA seeding failed (circular parent references or missing parents).")

            next_pending: List[COARow] = []
            progressed = False

            for row in pending:
                # already exists? skip
                if row.code in code_to_obj:
                    continue

                parent_obj = None
                if row.parent:
                    parent_obj = code_to_obj.get(row.parent)
                    if not parent_obj:
                        next_pending.append(row)
                        continue

                obj = ChartofAccounts.objects.create(
                    branch=branch,
                    user_add=user,
                    active=True,
                    is_system_generated=True,
                    code=row.code,
                    name=row.name,
                    type=row.type,
                    parent_account=parent_obj,
                    description=row.description,
                )
                code_to_obj[row.code] = obj
                created_count += 1
                progressed = True

            if not progressed and next_pending:
                missing_parents = sorted(
                    {r.parent for r in next_pending if r.parent and r.parent not in code_to_obj}
                )
                raise ValidationError(f"COA seeding stuck. Missing parent codes: {missing_parents}")

            pending = next_pending

    return {"created": created_count, "skipped": False, "branch_id": getattr(branch, "id", None)}


def seed_coa_for_branch(branch, *, user=None, force: bool = False) -> Dict[str, Any]:
    """
    Convenience wrapper if you want to seed directly by branch.
    """
    class _FakeMaster:
        def __init__(self, branch):
            self.branch = branch

    return seed_coa_for_master(_FakeMaster(branch), user=user, force=force)
