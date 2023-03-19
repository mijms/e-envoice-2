import qrcode
from PIL import Image

# e-invoice data
seller_name = "ABC Company"
seller_vat = "1234567890"
seller_tax = "001"
invoice_number = "INV-20220001"
invoice_date = "2022-01-01"
invoice_time = "12:30:00"
invoice_amount = "1000.00"
currency_code = "SAR"
buyer_name = "XYZ Corporation"
buyer_vat = "0987654321"

# e-invoice QR code data
qr_data = f"||1|1|{seller_name}|{seller_vat}|{seller_tax}|{invoice_number}|{invoice_date}|{invoice_time}|{invoice_amount}|{currency_code}|{buyer_name}|{buyer_vat}||"

# generate QR code
qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
qr.add_data(qr_data)
qr.make(fit=True)

img = qr.make_image(fill_color="black", back_color="white")

# save QR code image
img.save("e-invoice-qr.png")
