2# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| 1.x     | :x:                |

## Security Features

### 1. No Arbitrary Code Execution
- **Eliminated `exec()`**: Version 2.0 completely removes the dangerous `exec()` function
- **Command Whitelist**: Only 10 pre-defined, validated Playwright commands can be executed
- **Pydantic Validation**: All commands validated before execution

### 2. Authentication & Authorization
- **JWT Tokens**: Industry-standard JSON Web Tokens
- **Role-Based Access Control**: admin, prompt_engineer, user roles
- **Password Hashing**: bcrypt with salt
- **Token Expiration**: 24-hour expiry by default

### 3. Input Validation
- **Domain Whitelist**: Only localhost and *.openemis.org allowed
- **Selector Validation**: CSS selectors checked for injection patterns
- **File Path Validation**: Prevents path traversal attacks
- **Command Limits**: Max 50 commands per execution

### 4. Network Security
- **Selective CORS**: Only allowed origins can access API
- **Rate Limiting**: 10-20 requests per minute per IP
- **HTTPS Support**: SSL/TLS for production deployments

### 5. Data Protection
- **Session Storage**: Redis-backed sessions
- **Log Sanitization**: Sensitive data removed from logs
- **Environment Variables**: Secrets stored in .env files

## Known Security Measures

### Command Whitelist
Only these commands are allowed:
- `navigate` - URL validated against whitelist
- `click` - Selector validated for XSS patterns
- `fill` - Value length limited to 10,000 chars
- `wait_for` - Timeout limited to 30 seconds
- `wait_for_navigation` - Timeout limited to 30 seconds
- `screenshot` - Filename validated for path traversal
- `extract_text` - Selector validated
- `handle_dialog` - Action restricted to accept/dismiss
- `select_option` - Value validated
- `press_key` - Key restricted to known keyboard keys

### Rate Limiting
- **Automation Endpoint**: 10 requests/minute per IP
- **Chat Endpoint**: 20 requests/minute per IP
- **Admin Endpoints**: No rate limit (authenticated only)

### CORS Policy
Allowed origins:
- `http://localhost:3000` (development)
- `http://127.0.0.1:3000` (development)
- `https://demo.openemis.org` (production)
- `https://*.openemis.org` (production subdomains)

## Reporting a Vulnerability

### What to Report
We take security seriously. Please report:
- Authentication bypass vulnerabilities
- Code execution vulnerabilities
- SQL/NoSQL injection
- XSS (Cross-Site Scripting)
- CSRF (Cross-Site Request Forgery)
- Path traversal attacks
- Rate limit bypass
- Any security vulnerability

### What NOT to Report
- Bugs without security impact
- Feature requests
- Performance issues
- UI/UX issues

### How to Report

**Please DO NOT open public GitHub issues for security vulnerabilities.**

1. **Email**: Send details to security@example.com (replace with your email)
2. **Include**:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)
3. **Response Time**: We aim to respond within 48 hours

### What to Expect

1. **Acknowledgment**: Within 48 hours
2. **Assessment**: We'll validate and assess severity
3. **Fix Development**: Priority based on severity
4. **Disclosure**: Coordinated disclosure after fix is deployed
5. **Credit**: You'll be credited (if desired) in release notes

## Security Best Practices

### For Deployment

1. **Change Default Credentials**
   ```bash
   # In backend/utils/user_store.py
   # Change default admin password from "admin123"
   ```

2. **Generate Strong Secrets**
   ```bash
   # Generate JWT secret
   openssl rand -hex 32

   # Add to docker/.env
   JWT_SECRET=your-generated-secret
   FLASK_SECRET_KEY=another-generated-secret
   ```

3. **Use HTTPS in Production**
   ```yaml
   # docker-compose.yml
   # Add reverse proxy (nginx/traefik) with SSL
   ```

4. **Restrict CORS Origins**
   ```bash
   # In docker/.env
   CORS_ORIGINS=https://your-domain.com
   ```

5. **Enable Firewall**
   ```bash
   # Only expose necessary ports
   # Don't expose Redis (6379) publicly
   ```

6. **Regular Updates**
   ```bash
   # Keep dependencies updated
   pip install --upgrade -r requirements-backend.txt
   ```

### For Development

1. **Never Commit Secrets**
   - Use `.env` files (already in .gitignore)
   - Never hardcode API keys or passwords

2. **Review Generated Commands**
   - Always review LLM output before execution
   - Use `auto_execute: false` for testing

3. **Monitor Logs**
   - Check logs for suspicious activity
   - Logs are in `logs/` directory

4. **Test Security**
   - Run security tests before deployment
   - Test authentication & authorization

## Security Checklist

### Pre-Deployment
- [ ] Changed default admin password
- [ ] Generated strong JWT secret
- [ ] Generated strong Flask secret
- [ ] Configured production CORS origins
- [ ] Enabled HTTPS
- [ ] Reviewed and updated allowed domains
- [ ] Set up firewall rules
- [ ] Configured proper logging
- [ ] Tested authentication flows
- [ ] Tested authorization (role checks)
- [ ] Reviewed rate limiting settings
- [ ] Disabled debug mode
- [ ] Set up backup strategy

### Post-Deployment
- [ ] Monitor logs for suspicious activity
- [ ] Regular security updates
- [ ] Review access logs weekly
- [ ] Test rate limiting effectiveness
- [ ] Audit user accounts monthly
- [ ] Review learning examples for malicious patterns
- [ ] Monitor resource usage (DoS detection)

## Incident Response

If you detect a security incident:

1. **Immediate Actions**
   - Stop affected services
   - Preserve logs
   - Document the incident

2. **Investigation**
   - Identify scope and impact
   - Review logs and access patterns
   - Identify compromised accounts

3. **Remediation**
   - Apply security patches
   - Rotate compromised credentials
   - Notify affected users

4. **Prevention**
   - Update security measures
   - Implement additional controls
   - Document lessons learned

## Security Contacts

- **Security Email**: security@example.com
- **Project Maintainer**: [Your Name/Email]
- **Emergency Contact**: [Emergency Contact]

## Version History

### v2.0.0 (Current)
- ✅ Removed `exec()` vulnerability
- ✅ Added JWT authentication
- ✅ Implemented command whitelist
- ✅ Added rate limiting
- ✅ Implemented CORS restrictions
- ✅ Added input validation

### v1.0.0 (Legacy - Unsupported)
- ❌ Used `exec()` for code execution
- ❌ No authentication
- ❌ No rate limiting
- ❌ Wide-open CORS

## Compliance

This system implements:
- OWASP Top 10 security controls
- Principle of least privilege
- Defense in depth
- Secure by default configuration

---

**Last Updated**: February 2026
**Next Review**: March 2026
