from OpenSSL import crypto
import os

def generate_self_signed_cert():
    # Create certificates directory if it doesn't exist
    if not os.path.exists('certificates'):
        os.makedirs('certificates')

    # Generate key
    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)

    # Generate certificate
    cert = crypto.X509()
    cert.get_subject().CN = 'localhost'
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(365*24*60*60)  # Valid for one year
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(key)
    cert.sign(key, 'sha256')

    # Save private key
    with open('certificates/server.key', 'wb') as f:
        f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, key))

    # Save certificate
    with open('certificates/server.crt', 'wb') as f:
        f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert))

    print("Certificates generated successfully!")

if __name__ == '__main__':
    generate_self_signed_cert() 