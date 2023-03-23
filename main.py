import json
import base64
import requests
import datetime
import xml.etree.ElementTree as ET
from OpenSSL import crypto
import hashlib
from PIL import Image
import qrcode
from genkeys import *
from getcsid import *
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

generatekeys()
get_csid()

invoice_data = {
    "seller_name": "ABC Company",
    "seller_vat": "1234567890",
    "seller_street": "street",
    "seller_building": "1",
    "postal_zone": "11417",
    "seller_city_name": "Riyadh",
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

        # Create root element for invoice
        root = ET.Element("{urn:oasis:names:specification:ubl:schema:xsd:Invoice-2}Invoice",
                          xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2")

        # Add invoice header data
        invoice_header = ET.SubElement(
            root, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}InvoiceHeader")
        invoice_id = ET.SubElement(
            invoice_header, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID")
        invoice_id.text = invoice_data["invoice_number"]
        invoice_issue_date = ET.SubElement(
            invoice_header, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}IssueDate")
        invoice_issue_date.text = datetime.datetime.now().strftime('%Y-%m-%d')
        invoice_type_code = ET.SubElement(
            invoice_header, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}InvoiceTypeCode")
        invoice_type_code.text = '400'

        # Add seller data
        seller_party = ET.SubElement(
            invoice_header, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}AccountingSupplierParty")
        seller_party_id = ET.SubElement(
            seller_party, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyIdentification")
        seller_party_id_text = ET.SubElement(
            seller_party_id, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}ID")
        seller_party_id_text.text = invoice_data["seller_vat"]
        seller_party_name = ET.SubElement(
            seller_party, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PartyName")
        seller_party_name_text = ET.SubElement(
            seller_party_name, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}Name")
        seller_party_name_text.text = invoice_data["seller_name"]
        seller_party_address = ET.SubElement(
            seller_party, "{urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2}PostalAddress")
        seller_party_street = ET.SubElement(
            seller_party_address, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}StreetName")
        seller_party_street.text = invoice_data["seller_street"]
        seller_party_building = ET.SubElement(
            seller_party_address, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}BuildingNumber")
        seller_party_building.text = invoice_data["seller_building"]
        seller_party_postal_zone = ET.SubElement(
            seller_party_address, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}postal_zone")
        seller_party_postal_zone.text = invoice_data["postal_zone"]
        seller_address_city_name = ET.SubElement(
            seller_party_address, "{urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2}CityName")
        seller_address_city_name.text = invoice_data["seller_city_name"]

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
        with open('invoicehash.txt', 'w') as f:
            f.write(invoice_hash)
        # Sign the invoice hash
        signature = crypto.sign(pkey, invoice_hash, "sha256")

        # Load the certificate
        try:
            with open('certificate.txt', "rb") as cert_file:
                cert = cert_file.read()
                # Get the certificate hash
                cert_hash = hashlib.sha256(cert_file.read()).hexdigest()
        except Exception as e:
            print(str(e))

        # Add QR code to invoice
        qr_data = f"||1|1|{invoice_data['seller_name']}|{invoice_data['seller_vat']}|{invoice_data['invoice_number']}|{invoice_data['invoice_date']}|{invoice_data['invoice_time']}|{invoice_data['invoice_amount']}|{invoice_data['currency_code']}|{invoice_data['buyer_name']}|{invoice_data['buyer_vat']}"
        qr_code = base64.b64encode(qr_data.encode()).decode()
        ET.SubElement(root, "QRCode").text = qr_code

        # Add ZATCA metadata to invoice
        zatca_data = ET.SubElement(
            root, "{urn:zatca:metadata:schema:xsd:ZATCA_metadata-1}ZATCA_metadata")
        ET.SubElement(
            zatca_data, "{urn:zatca:metadata:schema:xsd:ZATCA_metadata-1}CertificateHash").text = cert_hash
        ET.SubElement(
            zatca_data, "{urn:zatca:metadata:schema:xsd:ZATCA_metadata-1}InvoiceHash").text = invoice_hash

        # Add ZATCA signature to invoice

        signed_properties = self.create_signed_properties(pkey)

        zatca_signature_elem = ET.SubElement(
            root, "{urn:zatca:metadata:schema:xsd:ZATCA_metadata-1}ZATCA_signature")
        ET.SubElement(zatca_signature_elem,
                      "{urn:zatca:metadata:schema:xsd:ZATCA_metadata-1}SignedProperties").text = signed_properties
        zatca_signature_value_elem = ET.SubElement(
            zatca_signature_elem, "{urn:zatca:metadata:schema:xsd:ZATCA_metadata-1}SignatureValue")
        zatca_signature_value = crypto.sign(
            pkey, signed_properties.encode(), "sha256")
        zatca_signature_value_elem.text = base64.b64encode(
            zatca_signature_value).decode()

        # Sign the final invoice with ZATCA signature
        zatca_signed_data = ET.tostring(root, encoding='utf-8')
        zatca_signature = crypto.sign(pkey, zatca_signed_data, "sha256")
        signed_zatca_invoice_data = zatca_signed_data + zatca_signature

        # Write the signed invoice to a file
        with open("invoice.xml", "wb") as output_file:
            output_file.write(zatca_signed_data)

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
