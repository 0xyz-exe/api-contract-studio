# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability within API Contract Studio, please do not file a public issue. Instead, report it directly to the maintainers at `security@api-contract-studio.dev`.

### SSRF Protection Policy

API Contract Studio restricts outbound HTTP requests during contract testing and specification URL imports:
- Loopback addresses (`127.0.0.0/8`, `::1`) are blocked by default.
- RFC 1918 private IP ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`) are blocked by default.
- Cloud metadata endpoints (`169.254.169.254`, `metadata.google.internal`) are blocked.
- DNS resolution is verified prior to connection to defend against rebinding attacks.
- Sensitive authentication headers (`Authorization`, `Cookie`, `X-API-Key`) are redacted in all generated reports.
