Below are instructions on how to generate crt and key from your bbc p12 certificate.
Convert .p12 to .crt
openssl pkcs12 -in bbc_cert.p12 -out bbc_cert.crt.pem -clcerts -nokeys

Convert .p12 to .key
openssl pkcs12 -in bbc_cert.p12 -out bbc_cert.key.pem -nocerts -nodes
