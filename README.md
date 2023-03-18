# SaudiEInvoice-phase2

SaudiEInvoice is a Python library that helps you create and submit invoices to the Saudi Arabian General Authority of Zakat and Tax (GAZT) using the e-invoicing system.

## Getting Started

### Prerequisites

**Before using SaudiEInvoice, you need to have the following:**

Python 3.6 or higher
OpenSSL library
A GAZT account
A valid private key file (.pfx format) and its password
An e-invoicing API URL provided by GAZT

### Installation

To install SaudiEInvoice, you can simply use pip:

```
pip install saudieinvoice
```

### Usage

To use SaudiEInvoice, you need to create an instance of the SaudiEInvoice class and provide it with the path to a configuration file that contains your GAZT account credentials, private key file path, and the e-invoicing API URL.

```
from saudieinvoice import SaudiEInvoice
sei = SaudiEInvoice(config_file_path="config.json")
```

#### Creating an Invoice

To create an invoice, you can pass an invoice data dictionary to the create_invoice() method. The dictionary should contain the invoice number, invoice date, vendor name, customer name, and a list of line items.

```
invoice_data = {
    "invoice_number": 123,
    "invoice_date": "02/10/2023",
    "vendor": "example co.",
    "customer": "example customer",
    "line_items": [
        {"product": "product1", "quantity": 1, "price": 20, "total": 20}
    ]
}
```

```
encoded_invoice_data = sei.create_invoice(invoice_data)
```

#### Submitting an Invoice

To submit an invoice, you can pass the encoded invoice data to the send_invoice() method.

```
success = sei.send_invoice(encoded_invoice_data)
```

```
if success:
    print("Invoice submitted successfully!")
else:
    print("Failed to submit invoice.")
```

#### Saving the XML Invoice

To save the generated XML invoice to a file, you can use the built-in ElementTree library in Python.

```
import xml.etree.ElementTree as ETroot = ET.fromstring(encoded_invoice_data)
xml_invoice = ET.tostring(root, encoding="utf-8")with open("invoice.xml", "wb") as f:
    f.write(xml_invoice)
```

### Contributing

If you'd like to contribute to SaudiEInvoice, please fork the repository and make your changes. Once you're done, submit a pull request and we'll review your changes.
