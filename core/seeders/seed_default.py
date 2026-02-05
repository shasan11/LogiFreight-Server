from django.db import transaction
from django.db.utils import OperationalError, ProgrammingError


def _model_has_field(Model, field_name: str) -> bool:
    return any(f.name == field_name for f in Model._meta.get_fields())


def seed_all_defaults(schema_name: str = "default"):
    try:
        from accounting.models import Currency, ChartofAccounts, PaymentMethod
        from master.models import Branch, MasterData, ShipmentPrefixes, ApplicationSettings
        from core.models import CustomUser
    except Exception:
        return

    with transaction.atomic():
        # ---- Singleton defaults ----
        if not ShipmentPrefixes.objects.exists():
            ShipmentPrefixes.objects.create()

        if not ApplicationSettings.objects.exists():
            ApplicationSettings.objects.create()

        # ---- Branch defaults ----
        main_branch_defaults = {
            "name": "Main Branch",
            "address": "Head Office",
            "city": "Dubai",
            "state": "Dubai",
            "country": "United Arab Emirates",
            "contact_number": "+971000000000",
            "status": "operational",
            "active": True,
            "is_main_branch": True,
        }

        main_branch = (
            Branch.objects.filter(is_main_branch=True).order_by("created").first()
            or Branch.objects.order_by("created").first()
        )

        if main_branch:
            for field_name, field_value in main_branch_defaults.items():
                if field_name == "is_main_branch":
                    continue
                if not getattr(main_branch, field_name, None):
                    setattr(main_branch, field_name, field_value)
            main_branch.is_main_branch = True
            main_branch.save()
        else:
            main_branch = Branch.objects.create(**main_branch_defaults)

        Branch.objects.exclude(pk=main_branch.pk).filter(is_main_branch=True).update(is_main_branch=False)

        # Associate superusers with the main branch
        CustomUser.objects.filter(is_superuser=True).exclude(branch=main_branch).update(branch=main_branch)

        # ---- Currency defaults ----
        default_currencies = [
            {"name": "US Dollar", "symbol": "$"},
            {"name": "UAE Dirham", "symbol": "AED"},
            {"name": "Nepalese Rupee", "symbol": "NPR"},
            {"name": "Euro", "symbol": "€"},
            {"name": "British Pound", "symbol": "£"},
            {"name": "Indian Rupee", "symbol": "₹"},
        ]
        for row in default_currencies:
            Currency.objects.get_or_create(name=row["name"], defaults={"symbol": row["symbol"]})

        # ---- Payment methods (optional) ----
        try:
            default_payment_methods = [
                {"name": "Cash"},
                {"name": "Bank Transfer"},
                {"name": "Cheque"},
                {"name": "Card"},
            ]
            for row in default_payment_methods:
                PaymentMethod.objects.get_or_create(name=row["name"])
        except Exception:
            pass

        # ---- MasterData defaults ----
        master_defaults = {
            "INCO": ["EXW", "FOB", "CIF", "CFR", "DAP", "DDP"],
            "STATUS": ["Draft", "Pending", "Approved", "Void", "Cancelled"],
            "CONTAINER_TYPE": ["20GP", "40GP", "40HC", "45HC"],
            "CARGO_TYPE": ["General", "Perishable", "Fragile", "Dangerous Goods"],
            "TRAILER_TYPE": ["Flatbed", "Reefer", "Dry Van", "Lowbed"],
            "DELIVERY_TYPE": ["Door to Door", "Port to Door", "Door to Port", "Port to Port"],
            "ShipmenSubType": ["FCL", "LCL", "Breakbulk", "RORO"],  # your model has this typo, matching it
        }

        for type_master, names in master_defaults.items():
            for name in names:
                MasterData.objects.get_or_create(type_master=type_master, name=name, defaults={"active": True})

        # ---- Chart of Accounts defaults (per branch) ----
        coa_template = [
            {"code": "1000", "name": "Assets", "type": "asset", "parent": None},
            {"code": "1100", "name": "Current Assets", "type": "asset", "parent": "1000"},
            {"code": "1110", "name": "Cash", "type": "asset", "parent": "1100"},
            {"code": "1120", "name": "Bank", "type": "asset", "parent": "1100"},
            {"code": "1200", "name": "Accounts Receivable", "type": "asset", "parent": "1000"},

            {"code": "2000", "name": "Liabilities", "type": "liability", "parent": None},
            {"code": "2100", "name": "Current Liabilities", "type": "liability", "parent": "2000"},
            {"code": "2200", "name": "Accounts Payable", "type": "liability", "parent": "2000"},

            {"code": "3000", "name": "Equity", "type": "equity", "parent": None},

            {"code": "4000", "name": "Income", "type": "income", "parent": None},
            {"code": "4100", "name": "Freight Income", "type": "income", "parent": "4000"},
            {"code": "4200", "name": "Service Income", "type": "income", "parent": "4000"},

            {"code": "5000", "name": "Expenses", "type": "expense", "parent": None},
            {"code": "5100", "name": "Operating Expenses", "type": "expense", "parent": "5000"},
            {"code": "5110", "name": "Salaries", "type": "expense", "parent": "5100"},
            {"code": "5120", "name": "Rent", "type": "expense", "parent": "5100"},
            {"code": "5130", "name": "Utilities", "type": "expense", "parent": "5100"},
        ]

        for branch in Branch.objects.all():
            base_filter = {}
            if _model_has_field(ChartofAccounts, "branch"):
                base_filter["branch"] = branch

            # if branch already has COA, don't spam duplicates
            if base_filter and ChartofAccounts.objects.filter(**base_filter).exists():
                continue
            if not base_filter and ChartofAccounts.objects.exists():
                continue

            by_code = {}

            # create parents first
            for row in [r for r in coa_template if r["parent"] is None]:
                defaults = {"name": row["name"], "type": row["type"]}
                if _model_has_field(ChartofAccounts, "description"):
                    defaults["description"] = ""

                obj, _ = ChartofAccounts.objects.get_or_create(
                    code=row["code"],
                    defaults=defaults,
                    **base_filter,
                )
                by_code[row["code"]] = obj

            # create children
            for row in [r for r in coa_template if r["parent"] is not None]:
                parent_obj = by_code.get(row["parent"])
                defaults = {"name": row["name"], "type": row["type"]}
                if _model_has_field(ChartofAccounts, "parent_account"):
                    defaults["parent_account"] = parent_obj
                if _model_has_field(ChartofAccounts, "description"):
                    defaults["description"] = ""

                obj, _ = ChartofAccounts.objects.get_or_create(
                    code=row["code"],
                    defaults=defaults,
                    **base_filter,
                )
                by_code[row["code"]] = obj
