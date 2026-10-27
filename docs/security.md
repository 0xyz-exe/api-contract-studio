# Security Architecture & Safeguards

API Contract Studio adheres to defense-in-depth principles across contract parsing, testing, and multi-tenant persistence.

## 1. SSRF Mitigations

URL imports and live contract testing validate all network targets prior to socket connection:

- **Loopback Blocking**: `127.0.0.0/8`, `::1` rejected unless `--allow-local` is explicitly opted-in.
- **Private Network Blocking**: RFC 1918 subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`) blocked.
- **Cloud Metadata Services**: `169.254.169.254` and `metadata.google.internal` blocked.
- **DNS Resolution Check**: Target hostnames are resolved before connection to inspect all underlying IPv4 and IPv6 addresses against blocklists, preventing DNS rebinding.
- **Safe Protocols**: Only `http://` and `https://` schemes allowed.

## 2. Safe Parsing & Input Limits

- **YAML Safety**: All documents are parsed strictly with `yaml.safe_load` to prevent arbitrary Python object deserialization.
- **File Size Limits**: Specifications exceeding 10MB are rejected prior to parsing.
- **Recursion Limits**: Local `$ref` resolution tracks traversal sets to prevent cyclic reference loops. External `$ref` targets are restricted.

## 3. Secret Redaction

The contract testing engine automatically redacts sensitive headers in logs and reports:
- `Authorization`
- `Cookie` / `Set-Cookie`
- `X-API-Key`
- Any header matching sensitive token patterns.

## 4. Multi-Tenant Isolation

- Every API operation strictly scopes database queries by `current_user.id` or project ownership.
- Modifying resource IDs in URLs results in `404 Not Found`.
- Password hashes use native salted bcrypt.
