import requests
import base64


def get_csid():
    try:
        with open("taxpayer.csr", "r") as f:
            csr_contents = f.read()
    except Exception as e:
        print(str(e))

    csr = base64.b64encode(csr_contents.encode("utf-8")).decode("utf-8")

    headers = {
        'accept': 'application/json',
        'OTP': '123345',
        'Accept-Version': 'V2',
        'Content-Type': 'application/json',
    }

    json_data = {
        'csr': '000',
    }
    json_data['csr'] = csr

    response = requests.post(
        'https://gw-fatoora.zatca.gov.sa/e-invoicing/developer-portal/compliance',
        headers=headers,
        json=json_data,
    )

    if response.status_code == 200:
        csid = response.json()
        print(csid)
        binarySecurityToken = response.json()['binarySecurityToken']
        decoded_token = base64.b64decode(binarySecurityToken).decode('utf-8')
        secret = response.json()['secret']

        with open('certificate.txt', 'w') as f:
            f.write(decoded_token)
        print('certificate.txt'+' saved')

        with open('binarySecurityToken.txt', 'w') as f:
            f.write(binarySecurityToken)
        print('binarySecurityToken.txt'+' saved')

        with open('secret.txt', 'w') as f:
            f.write(secret)
        print('secret.txt'+' saved')
    else:
        print(
            f"Error: received {response.status_code} status code with message {response.json()['dispositionMessage']}")
