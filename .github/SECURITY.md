# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Which versions are eligible for receiving such patches depends on the CVSS v3.0 Rating:

| Version | Supported          |
| ------- | ------------------ |
| 2.1.x   | :white_check_mark: |
| 2.0.x   | :white_check_mark: |
| < 2.0   | :x:                |

## Reporting a Vulnerability

Please report security vulnerabilities by emailing security@hendrix-project.org.

**Please do not report security vulnerabilities through public GitHub issues.**

When reporting a vulnerability, please include:

1. Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
2. Full paths of source file(s) related to the manifestation of the issue
3. The location of the affected source code (tag/branch/commit or direct URL)
4. Any special configuration required to reproduce the issue
5. Step-by-step instructions to reproduce the issue
6. Proof-of-concept or exploit code (if possible)
7. Impact of the issue, including how an attacker might exploit it

## Response Timeline

- **Initial Response**: Within 48 hours
- **Assessment**: Within 1 week
- **Patch Release**: Depends on severity
  - Critical: Within 48 hours
  - High: Within 1 week
  - Medium: Within 2 weeks
  - Low: Next regular release

## Disclosure Policy

- Security issues will be disclosed after a fix is available
- We will credit reporters who wish to be identified
- We request a 90-day disclosure embargo for critical vulnerabilities

## Security Best Practices for Users

1. **Keep Dependencies Updated**: Regularly update all dependencies
2. **API Keys**: Never commit API keys to the repository
3. **Model Files**: Only download models from trusted sources
4. **Input Validation**: Validate video files before processing
5. **Resource Limits**: Set appropriate memory and time limits

## Known Security Considerations

- Video processing can consume significant resources; implement timeouts
- Large model files should be verified with checksums
- User-uploaded content should be sandboxed
- API endpoints should implement rate limiting

Thank you for helping keep Hendrix and its users safe!