import subprocess
import os

# Get current user's home directory
home_dir = os.path.expanduser("~")

# Append necessary path to OpenSSL directory
openssl_dir = os.path.join(home_dir, "scoop", "apps", "openssl", "3.1.0", "bin")


def generatekeys():
    # Generate private key
    subprocess.run([os.path.join(openssl_dir, 'openssl.exe'), 'ecparam',
                    '-name', 'secp256k1', '-genkey', '-noout', '-out', 'PrivateKey.pem'])

    # Generate public key from private key
    subprocess.run([os.path.join(openssl_dir, 'openssl.exe'), 'ec',
                    '-in', 'PrivateKey.pem', '-pubout', '-out', 'publickey.pem'])

    # Generate CSR
    subprocess.run([os.path.join(openssl_dir, 'openssl.exe'), 'req', '-new', '-sha256', '-key', 'PrivateKey.pem', '-extensions', 'v3_req',
                    '-config', 'Configuration.cnf', '-out', 'taxpayer.csr'])
