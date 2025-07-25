# Telnyx Webhook Fallback Handler

Lambda function for handling failed Telnyx webhook deliveries and retry logic.

## Dependencies

- **boto3**: AWS SDK for DynamoDB and SNS integration
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
