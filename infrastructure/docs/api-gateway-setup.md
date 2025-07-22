# API Gateway Setup for Telnyx SMS Webhooks

## 🎯 Overview

The API Gateway integration provides secure webhook endpoints for Telnyx SMS integration with:
- **HMAC-SHA256 signature validation** via Lambda Authorizer
- **IP restriction** to Telnyx CIDR blocks
- **Dual event handling** (SNS + API Gateway) in the same Lambda function

## 🏗️ Architecture

```
Telnyx → API Gateway → Lambda Authorizer → SMS Handler Lambda → DynamoDB/SNS
                    ↓
                CloudWatch Logs
```

## 📋 Resources Created

### API Gateway Resources
- **REST API**: `smsbot-dev-telnyx-webhook-api`
- **Authorizer**: `smsbot-dev-security-telnyx-auth`
- **Endpoints**:
  - `POST /webhook/sms` - SMS webhook (authenticated)
  - `GET /health` - Health check (public)

### Lambda Functions
- **Authorizer**: `smsbot-dev-security-telnyx-authorizer`
- **SMS Handler**: Updated to handle both SNS and API Gateway events

### Security Features
- **IP Restrictions**: Only Telnyx IPs can access webhook endpoints
- **HMAC Validation**: Cryptographic signature verification
- **Timestamp Validation**: Prevents replay attacks (5-minute window)

## 🚀 Deployment Steps

### 1. Deploy Updated Infrastructure
```bash
cd infrastructure
source ./scripts/setup-aws-env.sh boss
./deploy-with-boss.sh dev your-company
```

### 2. Get API Gateway URL
After deployment, note the webhook endpoint from outputs:
```bash
# Check deployment outputs
cat outputs-dev-boss.json | grep WebhookEndpoint
```

### 3. Configure Telnyx Webhook Secret
The authorizer needs your Telnyx webhook secret. Update the Lambda environment variable:

```bash
# Get your webhook secret from Telnyx dashboard
# Then update the Lambda function
aws lambda update-function-configuration \
  --function-name smsbot-dev-security-telnyx-authorizer \
  --environment Variables='{
    "TELNYX_WEBHOOK_SECRET": "your-actual-webhook-secret-here",
    "ENVIRONMENT": "dev"
  }' \
  --profile boss
```

### 4. Configure Telnyx Webhook URL
In your Telnyx dashboard:
1. Go to Messaging → Messaging Profiles
2. Select your messaging profile
3. Set webhook URL to: `https://your-api-id.execute-api.us-east-1.amazonaws.com/dev/webhook/sms`
4. Enable webhook signing
5. Set HTTP method to POST

## 🔧 Configuration Details

### Telnyx IP CIDR Blocks
The API Gateway is restricted to these IP ranges:
```
185.86.151.0/24    # Telnyx primary
185.86.150.0/24    # Telnyx secondary  
147.75.0.0/16      # Telnyx infrastructure
139.178.0.0/16     # Telnyx infrastructure
136.144.0.0/16     # Telnyx infrastructure
```

**Development**: Additional IPs allowed for testing
**Production**: Only Telnyx IPs allowed

### Webhook Signature Validation
The authorizer validates:
- **Header**: `telnyx-signature-ed25519`
- **Timestamp**: `telnyx-timestamp`
- **Algorithm**: HMAC-SHA256
- **Payload**: `timestamp + request_body`

### Environment-Specific Settings

#### Development
- **Throttling**: 10 req/sec, 20 burst
- **IP Restrictions**: Permissive (includes 0.0.0.0/0)
- **Logging**: Detailed

#### Production
- **Throttling**: 100 req/sec, 200 burst
- **IP Restrictions**: Strict (Telnyx only)
- **Logging**: Standard

## 🧪 Testing

### 1. Health Check
```bash
# Test health endpoint (no auth required)
curl https://your-api-id.execute-api.us-east-1.amazonaws.com/dev/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "environment": "dev"
}
```

### 2. Webhook Endpoint (requires valid signature)
```bash
# This will fail without proper Telnyx signature
curl -X POST https://your-api-id.execute-api.us-east-1.amazonaws.com/dev/webhook/sms \
  -H "Content-Type: application/json" \
  -d '{"test": "message"}'
```

Expected response: `403 Forbidden` (due to missing/invalid signature)

### 3. Monitor Logs
```bash
# Check authorizer logs
aws logs tail /aws/lambda/smsbot-dev-security-telnyx-authorizer --follow --profile boss

# Check SMS handler logs  
aws logs tail /aws/lambda/smsbot-dev-messaging-sms-handler --follow --profile boss
```

## 📊 Monitoring

### CloudWatch Metrics
- **API Gateway**: Request count, latency, errors
- **Lambda Authorizer**: Invocations, duration, errors
- **SMS Handler**: Invocations, duration, errors

### Key Metrics to Watch
- `4XX` errors (authentication failures)
- `5XX` errors (server errors)
- Authorizer duration (should be < 1 second)
- SMS handler duration

### Alarms (Production)
- High error rate (> 5%)
- High latency (> 5 seconds)
- Authorizer failures (> 10%)

## 🔒 Security Best Practices

### Webhook Secret Management
- **Development**: Environment variable (temporary)
- **Production**: Use AWS Secrets Manager
- **Rotation**: Rotate secrets regularly

### IP Restrictions
- **Verify Telnyx IPs**: Check Telnyx documentation for current ranges
- **Monitor Access**: Review CloudWatch logs for unauthorized attempts
- **Update Regularly**: Keep CIDR blocks current

### Signature Validation
- **Always Validate**: Never skip signature verification
- **Timestamp Check**: Prevent replay attacks
- **Error Logging**: Log all validation failures

## 🆘 Troubleshooting

### Common Issues

**1. 403 Forbidden Errors**
- Check Telnyx webhook secret is correct
- Verify signature validation logic
- Confirm timestamp is within 5-minute window

**2. IP Restriction Issues**
- Verify Telnyx IP ranges are current
- Check if your testing IP is allowed (dev only)
- Review API Gateway resource policy

**3. Lambda Authorizer Timeouts**
- Check authorizer function logs
- Verify environment variables are set
- Ensure webhook secret is configured

**4. SMS Handler Not Triggered**
- Verify API Gateway integration is correct
- Check Lambda permissions
- Review request/response mapping

### Debug Commands
```bash
# Check API Gateway configuration
aws apigateway get-rest-api --rest-api-id YOUR-API-ID --profile boss

# Check authorizer configuration
aws apigateway get-authorizer --rest-api-id YOUR-API-ID --authorizer-id YOUR-AUTH-ID --profile boss

# Test authorizer directly
aws lambda invoke --function-name smsbot-dev-security-telnyx-authorizer \
  --payload '{"headers":{"telnyx-signature-ed25519":"test","telnyx-timestamp":"'$(date +%s)'"}}' \
  response.json --profile boss
```

## 📚 Next Steps

1. **Configure Telnyx**: Set up webhook URL and signing
2. **Test Integration**: Send test SMS through Telnyx
3. **Monitor Performance**: Watch CloudWatch metrics
4. **Security Review**: Audit IP restrictions and secrets
5. **Production Deployment**: Deploy to staging/prod environments

## 🔗 Useful Links

- [Telnyx Webhook Documentation](https://developers.telnyx.com/docs/v2/messaging/webhooks)
- [API Gateway Custom Authorizers](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-lambda-authorizer-lambda-function-create.html)
- [HMAC Signature Validation](https://developers.telnyx.com/docs/v2/messaging/webhooks#webhook-signing)
