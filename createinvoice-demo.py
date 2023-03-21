import json
import base64
import requests
import xml.etree.ElementTree as ET
from OpenSSL import crypto
import hashlib
from PIL import Image
import qrcode
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
        ET.SubElement(header, "InvoiceNumber").text = str(
            invoice_data["invoice_number"])
        ET.SubElement(
            header, "InvoiceDate").text = invoice_data["invoice_date"]
        seller = ET.SubElement(header, "Seller")
        ET.SubElement(seller, "Name").text = invoice_data["seller_name"]
        buyer = ET.SubElement(header, "Buyer")
        ET.SubElement(buyer, "Name").text = invoice_data["buyer_name"]

        # Add invoice items
        invoice_total = 0
        for item in invoice_data["line_items"]:
            item_elem = ET.SubElement(root, "InvoiceLine")
            ET.SubElement(item_elem, "ItemDescription").text = item["product"]
            ET.SubElement(item_elem, "ItemQuantity").text = str(
                item["quantity"])
            ET.SubElement(item_elem, "ItemPrice").text = str(item["price"])
            item_total = ET.SubElement(item_elem, "ItemTotal")
            item_total.text = str(item["total"])
            invoice_total += item["total"]

        # Add invoice summary data
        invoice_summary = ET.SubElement(root, "InvoiceSummary")
        ET.SubElement(invoice_summary, "TaxableAmount").text = str(
            invoice_total)
        ET.SubElement(invoice_summary, "TaxAmount").text = str(
            invoice_total * 0.15)  # assuming a 15% VAT rate
        ET.SubElement(invoice_summary, "InvoiceTotal").text = str(
            invoice_total + (invoice_total * 0.15))

        # Calculate the invoice hash
        invoice_hash = hashlib.sha256(
            ET.tostring(root, encoding='utf-8')).hexdigest()

        # Sign the invoice hash
        signature = crypto.sign(pkey, invoice_hash, "sha256")

        # Load the certificate
        with open('taxpayer.csr', "rb") as cert_file:
            cert = crypto.load_certificate(
                crypto.FILETYPE_ASN1, cert_file.read())

        # Get the certificate hash
        cert_hash = hashlib.sha256(cert_file.read()).hexdigest()

        # Add QR code to invoice
        qr_data = f"||1|1|{invoice_data['seller_name']}|{invoice_data['seller_vat']}|{invoice_data['invoice_number']}|{invoice_data['invoice_date']}|{invoice_data['invoice_time']}|{invoice_data['invoice_amount']}|{invoice_data['currency_code']}|{invoice_data['buyer_name']}|{invoice_data['buyer_vat']}"
        qr_code = base64.b64encode(qr_data.encode()).decode()
        ET.SubElement(root, "QRCode").text = qr_code

        # Add signature to invoice
        signed_properties = self.create_signed_properties(pkey)
        signature_elem = ET.SubElement(root, "Signature")
        signed_properties_elem = ET.SubElement(
            signature_elem, "SignedProperties")
        signed_properties_elem.text = signed_properties
        signature_value_elem = ET.SubElement(signature_elem, "SignatureValue")
        signature_value = crypto.sign(
            pkey, signed_properties.encode(), "sha256")
        signature_value_elem.text = base64.b64encode(signature_value).decode()

        # Sign the final invoice
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

    def generate_qr_code(self, invoice_data):
        invoice_number = str(invoice_data["invoice_number"])
        invoice_date = invoice_data["invoice_date"]
        invoice_time = invoice_data["invoice_time"]
        invoice_amount = invoice_data["invoice_amount"]
        currency_code = invoice_data["currency_code"]
        seller_name = invoice_data["seller_name"]
        seller_vat = invoice_data["seller_vat"]
        buyer_name = invoice_data["buyer_name"]
        buyer_vat = invoice_data["buyer_vat"]

        # e-invoice QR code data
        qr_data = f"||1|1|{seller_name}|{seller_vat}|{invoice_number}|{invoice_date}|{invoice_time}|{invoice_amount}|{currency_code}|{buyer_name}|{buyer_vat}||"

        # generate QR code
        qr = qrcode.QRCode(
            version=None, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
        qr.add_data(qr_data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # save QR code image
        img.save("e-invoice-qr.png")

        return qr

    def create_signed_properties(self, pkey):
        # Create signed properties for the invoice signature
        # This method returns a string that should be added to the SignedProperties tag
        signed_properties = "Signed properties data"
        # Modify signed_properties variable to create the actual signed properties
        return signed_properties


sei = SaudiEInvoice(config_file_path="configuration.json")
encoded_invoice_data = sei.create_invoice(invoice_data)
