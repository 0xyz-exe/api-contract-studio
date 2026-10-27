# Breaking Change Detection Rules

API Contract Studio classifies all contract differences into four compatibility categories:

- **BREAKING**: Breaks backwards compatibility for existing API consumers. Fails CI by default.
- **POTENTIALLY_BREAKING**: Ambiguous or consumer-dependent modifications requiring human review.
- **NON_BREAKING**: Additive modifications that preserve backwards compatibility.
- **INFORMATIONAL**: Documentation, examples, or description updates.

## Catalog of Implemented Rules

| Rule ID | Category | Default Classification | Severity | Description |
| :--- | :--- | :--- | :--- | :--- |
| `ACS-PATH-REMOVED` | Endpoint | `BREAKING` | `CRITICAL` | An existing path was deleted from the API. |
| `ACS-METHOD-REMOVED` | Endpoint | `BREAKING` | `CRITICAL` | An HTTP method on an existing path was removed. |
| `ACS-PATH-ADDED` | Endpoint | `NON_BREAKING` | `INFO` | A new path endpoint was added. |
| `ACS-METHOD-ADDED` | Endpoint | `NON_BREAKING` | `INFO` | A new HTTP method was added to an existing path. |
| `ACS-REQ-PARAM-ADDED-REQUIRED` | Request | `BREAKING` | `HIGH` | A new required query, path, or header parameter was added. |
| `ACS-REQ-PARAM-ADDED-OPTIONAL` | Request | `NON_BREAKING` | `LOW` | A new optional parameter was added. |
| `ACS-REQ-PARAM-REMOVED` | Request | `BREAKING` | `HIGH` | An existing required parameter was removed. |
| `ACS-REQ-PARAM-LOCATION-CHANGED` | Request | `BREAKING` | `HIGH` | Parameter location changed (e.g. from query to header). |
| `ACS-REQ-BODY-REQUIRED-ADDED` | Request | `BREAKING` | `HIGH` | A new required request body was added to an operation. |
| `ACS-REQ-BODY-REQUIRED-CHANGED` | Request | `BREAKING` | `HIGH` | An optional request body became required. |
| `ACS-REQ-MEDIA-TYPE-REMOVED` | Request | `BREAKING` | `HIGH` | An accepted request content-type was removed. |
| `ACS-RESP-STATUS-REMOVED` | Response | `BREAKING` | `HIGH` | A documented HTTP status code response was removed. |
| `ACS-RESP-STATUS-ADDED` | Response | `POTENTIALLY_BREAKING` | `MEDIUM` | A new response status code was added. |
| `ACS-RESP-PROP-REMOVED` | Schema | `BREAKING` | `HIGH` | A response property was removed from a schema payload. |
| `ACS-RESP-PROP-ADDED` | Schema | `NON_BREAKING` | `LOW` | A response property was added to an existing schema payload. |
| `ACS-SCHEMA-TYPE-CHANGED` | Schema | `BREAKING` | `HIGH` | Incompatible type change (e.g. integer to string). |
| `ACS-SCHEMA-ENUM-REMOVED` | Schema | `BREAKING` | `HIGH` | Acceptable enum value variants were removed. |
| `ACS-SCHEMA-ENUM-EXPANDED` | Schema | `POTENTIALLY_BREAKING` | `MEDIUM` | New enum values added (may break strict consumer parsers). |
| `ACS-SEC-SCHEME-ADDED` | Security | `BREAKING` | `HIGH` | New global security scheme requirement was added. |
| `ACS-SEC-SCHEME-REMOVED` | Security | `BREAKING` | `HIGH` | Supported security scheme was deleted. |
