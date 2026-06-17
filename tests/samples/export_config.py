EXPORT_CONFIG_RESPONSE = {
    "id": 10,
    "name": "My CSV export",
    "type": "PARSER",
    "parser_id": 138402,
    "items": ["InvoiceNumber", "PONumber", "InvoiceDate"],
    "csv_download": "/parser/TR-07rvCJs9h939RnWrO9ueM7Syjgak/download/my-csv-export.csv?cfg=10",
    "xls_download": "/parser/TR-07rvCJs9h939RnWrO9ueM7Syjgak/download/my-csv-export.xlsx?cfg=10",
}

EXPORT_CONFIG_LIST_RESPONSE = {
    "count": 1,
    "current": 1,
    "total": 1,
    "results": [EXPORT_CONFIG_RESPONSE],
}

EXPORT_FIELDS_RESPONSE = [
    {
        "type": "PARSER",
        "parser_field_name": None,
        "items": ["InvoiceNumber", "PONumber", "InvoiceDate", "TotalDue"],
    },
    {
        "type": "PARSER_FIELD",
        "parser_field_name": "LineItems",
        "parser_field_id": "PF951",
        "items": ["ItemCode", "Description", "Quantity", "Amount"],
    },
]
