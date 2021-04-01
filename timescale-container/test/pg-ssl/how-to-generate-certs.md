# How to generate SSL certificates

Adapted from Postgres 10 official documentation:

- [18.9.3. Creating Certificates](https://www.postgresql.org/docs/10/ssl-tcp.html#SSL-CERTIFICATE-CREATION)

**Warning**: The below procedure is only suitable for testing locally,
don't even think of doing the same for prod!

## Create self-signed certificate

Create a simple self-signed certificate for localhost valid for 10 years:

```bash
$ openssl req -new -x509 -days 3650 -nodes -text -out server.crt \
    -keyout server.key -subj "/CN=localhost"
```

Then do:

```bash
$ chmod og-rwx server.key
```

because the server will reject the file if its permissions are more liberal
than this.

## Create server certificate

To create a server certificate whose identity can be validated by clients,
first create a certificate signing request (CSR) and a public/private key
file:

```bash
$ openssl req -new -nodes -text -out root.csr \
    -keyout root.key -subj "/CN=root.localhost"
$ chmod og-rwx root.key
```

Then, sign the request with the key to create a root certificate authority
(using the default OpenSSL configuration file location on Linux and MacOS):

```bash
$ openssl x509 -req -in root.csr -text -days 3650 \
    -extfile /etc/ssl/openssl.cnf \
    -signkey root.key -out root.crt
```

Finally, create a server certificate signed by the new root certificate
authority:

```bash
$ openssl req -new -nodes -text -out server.csr \
    -keyout server.key -subj "/CN=localhost"
$ chmod og-rwx server.key
$ openssl x509 -req -in server.csr -text -days 3650 \
    -CA root.crt -CAkey root.key -CAcreateserial \
    -out server.crt
```
