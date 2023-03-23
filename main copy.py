import json
import base64
import xml.etree.ElementTree as ET
from OpenSSL import crypto
import hashlib
from PIL import Image
import qrcode
from genkeys import generatekeys
from getcsid import get_csid

generatekeys()
get_csid()

invoice_data = {
    "seller_name": "ABC Company",
    "seller_vat": "310864207200003",
    "seller_street": "street",
    "seller_building": "1",
    "postal_zone": "11417",
    "seller_city_name": "city",
    "invoice_number": "INV-20220001",
    "invoice_date": "2022-01-01",
    "invoice_time": "12:30:00",
    "invoice_amount": "1000.00",
    "currency_code": "SAR",
    "buyer_name": "XYZ Corporation",
    "buyer_vat": "310864207200003",
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
        return config['username'], config['password'], config['private_key_path'], config['url']

    def create_invoice(self, invoice_data):
        private_key_path = self.get_keys()[2]
        with open(private_key_path, "rb") as key_file:
            private_key = key_file.read()

        pkey = crypto.load_privatekey(crypto.FILETYPE_PEM, private_key)

        path = 'Simplified_Invoice.xml'  # Replace with actual path to invoice template file
        tree = ET.parse(path)
        root = tree.getroot()

        # Add QR code to invoice
        qr_data = f"||1|1|{invoice_data['seller_name']}|{invoice_data['seller_vat']}|{invoice_data['invoice_number']}|{invoice_data['invoice_date']}|{invoice_data['invoice_time']}|{invoice_data['invoice_amount']}|{invoice_data['currency_code']}|{invoice_data['buyer_name']}|{invoice_data['buyer_vat']}"
        qr_code = base64.b64encode(qr_data.encode()).decode()

        # Find the relevant elements to replace

        seller_name = root.find('cbc:RegistrationName')
        seller_vat = root.find('CompanyID')
        seller_street = root.find('StreetName')
        seller_building = root.find('PlotIdentification')
        postal_zone = root.find('PostalZone')
        seller_city_name = root.find('CityName')
        invoice_number = root.find('InvoiceNumber')
        invoice_date = root.find('IssueDate')
        invoice_time = root.find('IssueTime')
        invoice_amount = root.find('InvoiceNumber')
        currency_code = root.find('InvoiceNumber')
        buyer_name = root.find('InvoiceNumber')
        buyer_vat = root.find('InvoiceNumber')
        # line_items = root.find('LineItems')
        X509Certificate = root.find('X509Certificate')
        SigningTime = root.find('SigningTime')
        signing_cert = root.find('DigestValue')
        X509SerialNumber = root.find('X509SerialNumber')
        ID = root.find('ID')
        UUID = root.find('UUID')
        QR = root.find('QR')
        # Replace the data with your own values

        seller_name.text = invoice_data["invoice_number"]
        seller_vat.text = invoice_data["invoice_number"]
        seller_street.text = invoice_data["invoice_number"]
        seller_building.text = invoice_data["invoice_number"]
        postal_zone.text = invoice_data["invoice_number"]
        seller_city_name.text = invoice_data["invoice_number"]
        invoice_number.text = invoice_data["invoice_number"]
        invoice_date.text = invoice_data["invoice_number"]
        invoice_time.text = invoice_data["invoice_number"]
        invoice_amount.text = invoice_data["invoice_number"]
        currency_code.text = invoice_data["invoice_number"]
        buyer_name.text = invoice_data["invoice_number"]
        buyer_vat.text = invoice_data["invoice_number"]
        # line_items.text = invoice_data.seller_name

        # Calculate the invoice hash and sign it
        invoice_hash = hashlib.sha256(
            ET.tostring(root, encoding='utf-8')).hexdigest()
        signature = crypto.sign(pkey, invoice_hash, "sha256")

        # Load the certificate, get its hash, and sign the final invoice with ZATCA signature
        with open('certificate.txt', "rb") as cert_file:
            cert = cert_file.read()
            cert_hash = hashlib.sha256(cert_file.read()).hexdigest()
        zatca_signature = crypto.sign(
            pkey, ET.tostring(root, encoding='utf-8'), "sha256")
        zatca_signed_data = ET.tostring(root, encoding='utf-8')
        signed_zatca_invoice_data = zatca_signed_data + zatca_signature
        # Write the signed invoice to a file
        tree.write('invoice.xml')

        # Encode the signed ZATCA invoice data in base64
        encoded_zatca_invoice_data = base64.b64encode(
            signed_zatca_invoice_data).decode('utf-8')
        return encoded_zatca_invoice_data

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
