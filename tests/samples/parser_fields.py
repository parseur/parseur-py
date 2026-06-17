"""Reusable parser-field definitions and a realistic invoice document.

``ALL_FORMAT_FIELDS`` declares one scalar field for every non-table
:class:`parseur.FieldFormat`, plus a single ``LineItems`` ``TABLE`` field whose
six columns are scalars (not nested tables). ``INVOICE_TEXT`` is a realistic,
fully-laid-out invoice that contains a value for each field and a 12-row line
table, so an AI mailbox configured with these fields parses it into a complete
result. The same data drives the ``sample.txt`` / ``sample.pdf`` documents
(see ``tests/samples/generate_invoice.py``).
"""

# -- Header / scalar values -------------------------------------------------

SELLER_NAME = "Northwind Supplies Ltd."
SELLER_ADDRESS_LINES = [
    "Northwind Supplies Ltd.",
    "18 Harbour Road, Unit 4",
    "Bristol BS1 5TY, United Kingdom",
    "VAT GB 218 4471 09",
]

INVOICE_NUMBER = "INV-2026-0042"
PO_NUMBER = "PO-99817"
INVOICE_DATE = "2026-06-16"
DUE_DATE = "2026-07-16"
ISSUE_TIME = "09:45"
GENERATED_AT = "2026-06-16 09:45"
ACCOUNT_MANAGER = "Jane Doe"
BILLING_ADDRESS = "Contoso Ltd, 742 Evergreen Terrace, Springfield, IL 62704, USA"
PORTAL_LINK = "https://billing.northwind.example.com/inv/INV-2026-0042"
PAYMENT_TERMS = "Net 30"

# -- Line items: 12 rows x 6 columns ----------------------------------------

TAX_RATE = 8  # percent, applied to the whole invoice

_RAW_ITEMS = [
    ("WDG-1001", "Standard Widget", 10, 12.50),
    ("WDG-1002", "Premium Widget", 5, 24.00),
    ("GDT-2001", "Gadget Mini", 20, 6.75),
    ("GDT-2002", "Gadget Pro", 3, 49.90),
    ("CBL-3001", "USB-C Cable 2m", 15, 4.20),
    ("CBL-3002", "HDMI Cable 3m", 8, 7.80),
    ("ADP-4001", "Power Adapter 65W", 6, 29.99),
    ("ADP-4002", "Travel Adapter", 12, 9.50),
    ("BAT-5001", "AA Battery Pack", 30, 3.10),
    ("BAT-5002", "Li-ion Battery", 4, 18.40),
    ("CSE-6001", "Carrying Case", 7, 15.25),
    ("CSE-6002", "Protective Sleeve", 9, 5.60),
]

LINE_ITEMS = [
    {
        "ItemCode": code,
        "Description": description,
        "Quantity": qty,
        "UnitPrice": round(unit, 2),
        "TaxRate": TAX_RATE,
        "Amount": round(qty * unit, 2),
    }
    for code, description, qty, unit in _RAW_ITEMS
]

SUBTOTAL = round(sum(item["Amount"] for item in LINE_ITEMS), 2)
TAX_TOTAL = round(SUBTOTAL * TAX_RATE / 100, 2)
TOTAL_DUE = round(SUBTOTAL + TAX_TOTAL, 2)

# Table column order, names and formats (columns are scalars, not nested).
TABLE_COLUMNS = [
    ("ItemCode", "TEXT"),
    ("Description", "TEXT"),
    ("Quantity", "NUMBER"),
    ("UnitPrice", "NUMBER"),
    ("TaxRate", "NUMBER"),
    ("Amount", "NUMBER"),
]


# -- Plain-text rendering of the invoice ------------------------------------


def _build_invoice_text():
    head = f"{'SKU':<10} {'Description':<24}{'Qty':>5} {'Unit Price':>12} {'Tax':>6} {'Amount':>12}"
    rows = [
        f"{i['ItemCode']:<10} {i['Description']:<24}{i['Quantity']:>5} "
        f"{i['UnitPrice']:>12.2f} {str(i['TaxRate']) + '%':>6} {i['Amount']:>12.2f}"
        for i in LINE_ITEMS
    ]
    lines = [
        "[LOGO] " + SELLER_NAME,
        *SELLER_ADDRESS_LINES[1:],
        "",
        "INVOICE",
        f"Invoice Number: {INVOICE_NUMBER}",
        f"PO Number: {PO_NUMBER}",
        f"Invoice Date: {INVOICE_DATE}",
        f"Due Date: {DUE_DATE}",
        f"Issue Time: {ISSUE_TIME}",
        f"Generated At: {GENERATED_AT}",
        f"Account Manager: {ACCOUNT_MANAGER}",
        f"Payment Terms: {PAYMENT_TERMS}",
        "",
        f"Bill To: {BILLING_ADDRESS}",
        f"Customer Portal: {PORTAL_LINK}",
        "",
        "Line Items:",
        head,
        *rows,
        "",
        f"Subtotal: {SUBTOTAL:.2f}",
        f"Tax ({TAX_RATE}%): {TAX_TOTAL:.2f}",
        f"Total Due: {TOTAL_DUE:.2f}",
    ]
    return "\n".join(lines) + "\n"


INVOICE_TEXT = _build_invoice_text()


# -- Parser field definitions -----------------------------------------------

ALL_FORMAT_FIELDS = [
    {"name": "InvoiceNumber", "format": "ONELINE", "query": "the invoice number"},
    {"name": "PONumber", "format": "TEXT", "query": "the purchase order number"},
    {"name": "InvoiceDate", "format": "DATE", "query": "the invoice date"},
    {"name": "DueDate", "format": "DATE", "query": "the payment due date"},
    {"name": "IssueTime", "format": "TIME", "query": "the issue time"},
    {"name": "GeneratedAt", "format": "DATETIME", "query": "the generation timestamp"},
    {"name": "AccountManager", "format": "NAME", "query": "the account manager name"},
    {"name": "BillingAddress", "format": "ADDRESS", "query": "the bill-to address"},
    {"name": "CustomerPortal", "format": "LINK", "query": "the customer portal url"},
    {"name": "TotalDue", "format": "NUMBER", "query": "the total amount due"},
    {
        "name": "LineItems",
        "format": "TABLE",
        "query": "the invoice line items",
        "parser_object_set": [
            {"name": name, "format": fmt} for name, fmt in TABLE_COLUMNS
        ],
    },
]
