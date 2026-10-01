# Rate Limit Configuration Guide

## How to Adjust Rate Limits

1. **Locate the .env file** in `backend/backend/.env`

2. **Edit the rate limit values:**

```bash
   RATE_LIMIT_AUTH=10/hour          # Increase if users complain about login issues
   RATE_LIMIT_UPLOAD=5/hour         # Increase if users need to upload more documents
   RATE_LIMIT_QUERY=20/hour         # CAREFUL: Each query costs money!
   RATE_LIMIT_GENERAL=100/hour      # General requests
```

3. **Restart the server** for changes to take effect

4. **Monitor costs** after increasing limits (especially RATE_LIMIT_QUERY)

## When to Adjust Limits

**Increase RATE_LIMIT_AUTH if:**

- Users complain they can't log in (10 attempts not enough)
- Multiple people share a network/IP address

**Increase RATE_LIMIT_UPLOAD if:**

- Users need to process many documents quickly
- You have budget for Vision API costs

**Increase RATE_LIMIT_QUERY if:**

- Users need to ask many questions
- You can afford higher LLM API costs
- Consider: 100 queries/day × $0.005 = $15/month per user

**Decrease limits if:**

- API costs are too high
- You detect abuse
- Need to control resource usage

## Disable Rate Limiting (Testing Only)

```bash
RATE_LIMIT_ENABLED=false
```

**WARNING:** Never disable in production!

## Exempt Specific IPs

For admin machines or monitoring services:

```bash
RATE_LIMIT_EXEMPT_IPS=["192.168.1.100","10.0.0.5"]
```
