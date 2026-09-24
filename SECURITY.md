# Security policy

## Which code this policy covers

SynthRange is an open research idea and reference implementation with no versioned distribution. This policy covers the latest `main` branch only; older commits are not maintained, and no version is designated as supported.

## Reporting a vulnerability

Do not open a public issue for vulnerabilities in SynthRange, its deployment artifacts, or its default configurations.

Use a [private GitHub security advisory](https://github.com/akinteldev/synthrange/security/advisories/new). Include:

- affected component and revision;
- impact and realistic attack path;
- reproduction steps or proof of concept;
- suggested remediation, if known;
- whether disclosure is time-sensitive.

Reports are handled on a best-effort basis by a maintainer-led project with no on-call rotation. The intent is to acknowledge the report, assess severity, remediate on `main` where warranted, and credit reporters who want attribution. No acknowledgement or remediation timeline is promised.

## Scope

This policy covers vulnerabilities in SynthRange itself. Reports about intentionally vulnerable targets such as OWASP Juice Shop belong to their upstream projects unless SynthRange introduces the weakness through packaging or configuration.

Do not include real credentials, private keys, personal data, malware, or evidence collected from systems you do not own or have authorization to assess.
