# Telnyx Webhook Authorizer

Lambda function for validating Telnyx webhook signatures using the official SDK pattern.

## Dependencies

- **PyNaCl**: Official Telnyx SDK dependency for EdDSA signature validation
- **boto3**: AWS SDK for Secrets Manager integration
- **botocore**: AWS core library

## Development

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Format code
uv run black .

# Lint code
uv run ruff check .
```

## Deployment

This function is packaged and deployed via AWS CDK with proper dependency management.
