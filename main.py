import json
import base64
import requests
import xml.etree.ElementTree as ET
from OpenSSL import crypto
from genkeys import *


generatekeys()
invoice_data = {
    "seller_name": "ABC Company",
    "seller_vat": "1234567890",
    "invoice_number": "INV-20220001",
    "invoice_date": "2022-01-01",
    "invoice_time": "12:30:00",
    "invoice_amount": "1000.00",
    "currency_code": "SAR",
    "buyer_name": "XYZ Corporation",
    "buyer_vat": "0987654321",
    "line_items": [
        {"product": "product1", "quantity": 1, "price": 20, "total": 20}
    ]
}


class SaudiEInvoice:
    def __init__(self, config_file_path):
        self.config_file_path = config_file_path

    def get_keys(self):
        with open(self.config_file_path) as f:
            config = json.load(f)

        username = config['username']
        password = config['password']
        private_key_path = config['private_key_path']
        url = config['url']

        return username, password, private_key_path, url

    def create_invoice(self, invoice_data):
        private_key_path = self.get_keys()[2]
        with open(private_key_path, "rb") as key_file:
            private_key = key_file.read()

        pkey = crypto.load_privatekey(crypto.FILETYPE_PEM, private_key)

        root = ET.Element("Invoice")
        header = ET.SubElement(root, "InvoiceHeader")

        # Add invoice header data
        invoice_number = ET.SubElement(header, "InvoiceNumber")
        invoice_number.text = str(invoice_data["invoice_number"])

        invoice_date = ET.SubElement(header, "InvoiceDate")
        invoice_date.text = invoice_data["invoice_date"]

        seller = ET.SubElement(header, "Seller")
        seller_name = ET.SubElement(seller, "Name")
        seller_name.text = invoice_data["seller_name"]

        buyer = ET.SubElement(header, "Buyer")
        buyer_name = ET.SubElement(buyer, "Name")
        buyer_name.text = invoice_data["buyer_name"]

        # Add invoice items
        line_items = invoice_data["line_items"]
        invoice_total = 0
        for i, item in enumerate(line_items):
            item_elem = ET.SubElement(root, "InvoiceLine")
            item_description = ET.SubElement(item_elem, "ItemDescription")
            item_description.text = item["product"]
            item_quantity = ET.SubElement(item_elem, "ItemQuantity")
            item_quantity.text = str(item["quantity"])
            item_price = ET.SubElement(item_elem, "ItemPrice")
            item_price.text = str(item["price"])
            item_total = ET.SubElement(item_elem, "ItemTotal")
            item_total.text = str(item["total"])
            invoice_total += item["total"]
        # Add invoice summary data
        invoice_summary = ET.SubElement(root, "InvoiceSummary")
        taxable_amount = ET.SubElement(invoice_summary, "TaxableAmount")
        taxable_amount.text = str(invoice_total)
        tax_amount = ET.SubElement(invoice_summary, "TaxAmount")
        tax_amount.text = str(invoice_total * 0.15)  # assuming a 15% VAT rate
        invoice_total_elem = ET.SubElement(invoice_summary, "InvoiceTotal")
        invoice_total_elem.text = str(invoice_total + (invoice_total * 0.15))

        # Sign the invoice
        signed_data = ET.tostring(root, encoding='utf-8')
        signature = crypto.sign(pkey, signed_data, "sha256")
        signed_invoice_data = signed_data + signature

        # Write the signed invoice to a file
        with open("invoice.xml", "wb") as output_file:
            output_file.write(signed_data)

        # Encode the signed invoice data in base64
        encoded_invoice_data = base64.b64encode(
            signed_invoice_data).decode('utf-8')

        return encoded_invoice_data

    def send_invoice(self, encoded_invoice_data):
        username, password, _, url = self.get_keys()

        headers = {
            'Content-Type': 'text/xml;charset=UTF-8',
            'Authorization': f'Basic {base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("utf-8")}'
        }
        body = f"""<?xml version="1.0" encoding="UTF-8"?>
                   <SubmitInvoiceRequest>
                       <Invoice>{encoded_invoice_data}</Invoice>
                   </SubmitInvoiceRequest>"""

        response = requests.post(url, headers=headers, data=body)

        # Decode the response
        response_data = base64.b64decode(response.content).decode('utf-8')
        response_root = ET.fromstring(response_data)
        # Check if the submission was successful
        if response_root.find('Status').text == 'Success':
            return True
        else:
            return False


sei = SaudiEInvoice(config_file_path="configuration.json")
encoded_invoice_data = sei.create_invoice(invoice_data)
