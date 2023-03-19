import createinvoice

invoice_data = {
    "seller_name": "ABC Company",
    "seller_vat":"1234567890",
    "seller_tax":"001",
    "invoice_number":"INV-20220001",
    "invoice_date":"2022-01-01",
    "invoice_time":"12:30:00",
    "invoice_amount":"1000.00",
    "currency_code":"SAR",
    "buyer_name":"XYZ Corporation",
    "buyer_vat":"0987654321",
    "line_items": [
        {"product": "product1", "quantity": 1, "price": 20, "total": 20}
    ]
}

sei = createinvoice.SaudiEInvoice(config_file_path="configuration.json")
encoded_invoice_data = sei.create_invoice(invoice_data)
