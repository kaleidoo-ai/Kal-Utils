#!/bin/bash

# Create directories if they don't exist
mkdir -p certs

# Generate CA private key and certificate
openssl genpkey -algorithm RSA -out certs/ca-key.pem
openssl req -x509 -new -nodes -key certs/ca-key.pem -sha256 -days 365 -out certs/cert.pem \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=CA"

# Generate certificates for app1
openssl genpkey -algorithm RSA -out certs/app1-key.pem
openssl req -new -key certs/app1-key.pem -out certs/app1.csr \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=app1"
openssl x509 -req -in certs/app1.csr -CA certs/cert.pem -CAkey certs/ca-key.pem \
    -CAcreateserial -out certs/app1-cert.pem -days 365 -sha256

# Generate certificates for nginx
openssl genpkey -algorithm RSA -out certs/nginx-key.pem
openssl req -new -key certs/nginx-key.pem -out certs/nginx.csr \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=nginx"
openssl x509 -req -in certs/nginx.csr -CA certs/cert.pem -CAkey certs/ca-key.pem \
    -CAcreateserial -out certs/nginx-cert.pem -days 365 -sha256

# Generate certificates for prometheus
openssl genpkey -algorithm RSA -out certs/prometheus-key.pem
openssl req -new -key certs/prometheus-key.pem -out certs/prometheus.csr \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=prometheus"
openssl x509 -req -in certs/prometheus.csr -CA certs/cert.pem -CAkey certs/ca-key.pem \
    -CAcreateserial -out certs/prometheus-cert.pem -days 365 -sha256

# Set appropriate permissions
chmod 644 certs/*.pem
chmod 600 certs/*-key.pem

# Clean up CSR files
rm certs/*.csr
