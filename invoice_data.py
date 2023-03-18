import createinvoice

invoice_data = {
    "invoice_number": 123,
    "invoice_date": "02/10/2023",
    "vendor": "example co.",
    "customer": "example customer",
    "line_items": [
        {"product": "product1", "quantity": 1, "price": 20, "total": 20}
    ]
}

sei = createinvoice.SaudiEInvoice(config_file_path="configuration.json")
encoded_invoice_data = sei.create_invoice(invoice_data)
