import json
import base64
import requests
import xml.etree.ElementTree as ET
from OpenSSL import crypto
import hashlib


class SaudiEInvoice:
    def __init__(self, config_file_path):
        self.config_file_path = config_file_path

    def get_keys(self):
        with open(self.config_file_path) as f:
            config = json.load(f)

        username = config['username']
        password = config['password']
        private_key_path = config['private_key_path']
        certificate_path = config['certificate_path']
        url = config['url']

        return username, password, private_key_path, certificate_path, url

    def create_invoice(self, invoice_data):
        private_key_path, certificate_path = self.get_keys()[2:4]
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
        seller_name.text = invoice_data["vendor"]

        buyer = ET.SubElement(header, "Buyer")
        buyer_name = ET.SubElement(buyer, "Name")
        buyer_name.text = invoice_data["customer"]

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

        # Calculate the invoice hash
        invoice_hash = hashlib.sha256(ET.tostring(root, encoding='utf-8')).hexdigest()

        # Sign the invoice hash
        signature = crypto.sign(pkey, invoice_hash, "sha256")

        # Load the certificate
        with open(certificate_path, "rb") as cert_file:
            cert_data = cert_file.read()
            cert = crypto.load_certificate(crypto.FILETYPE_ASN1, cert_data)

        # Get the certificate hash
        cert_hash = hashlib.sha256(cert_data).hexdigest()

        # Create the SignedInfo element
        signed_info_elem = ET.Element("ds:SignedInfo", xmlns="http://www.w3.org/2000/09/xmldsig#")

        # Add the CanonicalizationMethod element
        canonicalization_method_elem = ET.SubElement(signed_info_elem, "ds:CanonicalizationMethod", Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315")

        # Add the SignatureMethod element
        signature_method_elem = ET.SubElement(signed_info_elem, "ds:SignatureMethod", Algorithm="http://www.w3.org/2001/04/xmldsig-more#rsa-sha256")

        # Add the Reference element
        reference_elem = ET.SubElement(signed_info_elem, "ds:Reference")
        reference_elem.set("URI", "#Invoice")

        # Add the Transforms element
        transforms_elem = ET.SubElement(reference_elem, "ds:Transforms")
        transform_elem = ET.SubElement(transforms_elem, "ds:Transform", Algorithm="http://www.w3.org/2000/09/xmldsig#enveloped-signature")
        transform_elem2 = ET.SubElement(transforms_elem, "ds:Transform", Algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315")

        # Add the DigestMethod element
        digest_method_elem = ET.SubElement(reference_elem, "ds:DigestMethod", Algorithm="http://www.w3.org/2001/04/xmlenc#sha256")

        # Add the DigestValue element
        digest_value_elem = ET.SubElement(reference_elem, "ds:DigestValue")
        canon_data = ET.tostring(reference_elem, method='c14n', exclusive=False, with_comments=False).decode('utf-8')
        hash_obj = crypto.SHA256()
        hash_obj.update(canon_data.encode('utf-8'))
        digest_value_elem.text = base64.b64encode(hash_obj.finalize()).decode('utf-8')

        # Add the Signature element
        signature_elem = ET.SubElement(root, "ds:Signature", namespaces={
            "ds": "http://www.w3.org/2000/09/xmldsig#"
        })

        # Add the SignedInfo element to the Signature element
        signature_elem.append(signed_info_elem)

        # Add the SignatureValue element
        signature_value_elem = ET.SubElement(signature_elem, "ds:SignatureValue")
        canonicalized_signed_data = ET.tostring(signed_info_elem, method='c14n', exclusive=False, with_comments=False).decode('utf-8')
        signature_value = crypto.sign(pkey, canonicalized_signed_data.encode('utf-8'), "sha256")
        signature_value_elem.text = base64.b64encode(signature_value).decode('utf-8')

        # Add the KeyInfo element
        key_info_elem = ET.SubElement(signature_elem, "ds:KeyInfo")
        x509_data_elem = ET.SubElement(key_info_elem, "ds:X509Data")
        x509_certificate_elem = ET.SubElement(x509_data_elem, "ds:X509Certificate")
        x509_certificate = crypto.load_certificate(crypto.FILETYPE_PEM, cert_str)
        x509_certificate_str = crypto.dump_certificate(crypto.FILETYPE_PEM, x509_certificate).decode('utf-8').replace("-----BEGIN CERTIFICATE-----\n", "").replace("-----END CERTIFICATE-----", "").replace("\n", "")
        x509_certificate_elem.text = x509_certificate_str

        # Add the SignedProperties element
        signed_properties_elem = ET.SubElement(signature_elem, "ds:SignedProperties", Id="SignedProperties")
        signed_properties_elem.set("xmlns:xades141", "http://uri.etsi.org/01903/v1.
                # Add QR code to invoice
        qr_code = self.generate_qr_code(encoded_invoice_data)
        qr_code_elem = ET.SubElement(root, "QRCode")
        qr_code_elem.text = qr_code

        # Add signature to invoice
        signed_properties = self.create_signed_properties(pkey)
        signature_elem = ET.SubElement(root, "Signature")
        signed_properties_elem = ET.SubElement(signature_elem, "SignedProperties")
        signed_properties_elem.text = signed_properties
        signature_value_elem = ET.SubElement(signature_elem, "SignatureValue")
        signature_value = crypto.sign(pkey, signed_properties.encode(), "sha256")
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

    def generate_qr_code(self, encoded_invoice_data):
        # Generate QR code for encoded invoice data
        # Add the QR code to the invoice
        qr_code = "QR code data"
        # Modify qr_code variable to generate the actual QR code
        return qr_code

    def create_signed_properties(self, pkey):
        # Create signed properties for the invoice signature
        # This method returns a string that should be added to the SignedProperties tag
        signed_properties = "Signed properties data"
        # Modify signed_properties variable to create the actual signed properties
        return signed_properties
