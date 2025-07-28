# 🌐 Public API Gateway Configuration Guide

## 🎯 **API Gateway Changes Made**

Your SMS Bot infrastructure now uses a **public regional API Gateway** **without custom domains, certificates, or VPC costs**. This provides secure webhook endpoints with Lambda authorization while keeping costs minimal.

## 💰 **Cost Optimization**

### ❌ **Removed Expensive Components:**
- **VPC Gateway Endpoint**: Saved ~$7.30/month
- **Custom Domain**: Saved ~$0.50/month per domain
- **SSL Certificates**: No ACM certificate costs
- **Private API Complexity**: Simplified architecture

### ✅ **What Remains (Cost-Effective):**
- **Public Regional API**: No additional infrastructure costs
- **Lambda Authorizer**: Only pay for invocations
- **CloudWatch Logs**: Standard logging costs
- **Request-based Pricing**: Pay only for actual usage

## 🏗️ **Public API Architecture**

### **API Gateway Configuration:**
```python
# Public regional API (no VPC costs)
endpoint_configuration=apigateway.EndpointConfiguration(
    types=[apigateway.EndpointType.REGIONAL]
)

# No resource policy needed - security via Lambda authorizer
# No VPC endpoint required - direct internet access
```

### **Security Model:**
- **Lambda Authorizer**: Validates Telnyx webhook signatures
- **CORS Configuration**: Controlled cross-origin access
- **CloudWatch Logging**: Full request/response logging
- **IAM Roles**: Least privilege access for all functions

## 📊 **API Endpoints Created**

### **1. Health Check Endpoint**
- **URL**: `https://{api-id}.execute-api.{region}.amazonaws.com/{stage}/health`
- **Method**: GET
- **Auth**: None required
- **Response**: `{"status": "healthy", "timestamp": "..."}`
- **Access**: Public (for monitoring)

### **2. SMS Webhook Endpoint**
- **URL**: `https://{api-id}.execute-api.{region}.amazonaws.com/{stage}/webhooks/telnyx/sms`
- **Method**: POST
- **Auth**: Lambda authorizer (Telnyx signature validation)
- **Handler**: Your SMS handler Lambda function
- **Access**: Public with signature validation

### **3. Fallback Webhook Endpoint**
- **URL**: `https://{api-id}.execute-api.{region}.amazonaws.com/{stage}/webhooks/telnyx/fallback`
- **Method**: POST
- **Auth**: Lambda authorizer
- **Handler**: Fallback Lambda function for error handling
- **Access**: Public with signature validation

### **4. Fallback Health Check**
- **URL**: `https://{api-id}.execute-api.{region}.amazonaws.com/{stage}/webhooks/telnyx/fallback`
- **Method**: GET
- **Auth**: None required
- **Response**: `{"status": "fallback-healthy", "timestamp": "..."}`
- **Access**: Public (for monitoring)

## 🔐 **Security Features**

### **Lambda Authorizer:**
- **Function**: `smsbot-{env}-security-lambda-api-authorizer`
- **Purpose**: Validates Telnyx webhook signatures
- **Headers**: Checks `X-Telnyx-Signature` and `Authorization`
- **Cache**: 5-minute TTL for performance
- **Cost**: Only pay for actual authorizer invocations

### **Request Validation:**
- **Signature Verification**: Telnyx webhook signature validation
- **Header Validation**: Required headers checked
- **Request Logging**: All requests logged to CloudWatch
- **Error Handling**: Proper error responses and logging

### **IAM Permissions:**
- **Authorizer Function**: Read access to DynamoDB for validation
- **Fallback Function**: Write access to analytics table
- **KMS Encryption**: All functions can decrypt with customer keys
- **Least Privilege**: Minimal required permissions only

## 📋 **Stack Outputs**

After deployment, you'll see these outputs:

```json
{
  "ApiGatewayUrl": "https://abc123def4.execute-api.us-east-1.amazonaws.com/dev/",
  "WebhookEndpoint": "https://abc123def4.execute-api.us-east-1.amazonaws.com/dev/webhooks/telnyx/sms",
  "FallbackEndpoint": "https://abc123def4.execute-api.us-east-1.amazonaws.com/dev/webhooks/telnyx/fallback", 
  "HealthCheckEndpoint": "https://abc123def4.execute-api.us-east-1.amazonaws.com/dev/health",
  "AuthorizerFunctionArn": "arn:aws:lambda:us-east-1:123456789012:function:smsbot-dev-security-lambda-api-authorizer"
}
```

## 🚀 **Deployment**

### **No Additional Configuration Required:**
```bash
# Deploy as usual - no VPC or domain setup needed
./scripts/deploy.sh dev your-company

# API Gateway will be created automatically as public regional
```

### **What's Automatic:**
- ✅ **Public API**: Created automatically with regional endpoint
- ✅ **Lambda Functions**: Authorizer and fallback functions deployed
- ✅ **IAM Roles**: Proper permissions configured automatically
- ✅ **CloudWatch Logs**: API access logging enabled
- ✅ **CORS**: Cross-origin requests configured for webhooks

## 🔍 **Testing the Public API**

### **Health Check (Public Access):**
```bash
# Health check from anywhere
curl https://abc123def4.execute-api.us-east-1.amazonaws.com/dev/health

# Expected response:
# {"status": "healthy", "timestamp": "2024-01-15T10:30:00Z"}
```

### **Webhook Testing (With Authorization):**
```bash
# Test SMS webhook with proper Telnyx signature
curl -X POST \
  https://abc123def4.execute-api.us-east-1.amazonaws.com/dev/webhooks/telnyx/sms \
  -H "Content-Type: application/json" \
  -H "X-Telnyx-Signature: your-telnyx-signature" \
  -d '{"test": "webhook", "data": {"event_type": "message.received"}}'

# Without proper signature - should return 401 Unauthorized
curl -X POST \
  https://abc123def4.execute-api.us-east-1.amazonaws.com/dev/webhooks/telnyx/sms \
  -H "Content-Type: application/json" \
  -d '{"test": "webhook"}'
```

### **Fallback Testing:**
```bash
# Test fallback endpoint
curl -X POST \
  https://abc123def4.execute-api.us-east-1.amazonaws.com/dev/webhooks/telnyx/fallback \
  -H "Content-Type: application/json" \
  -H "X-Telnyx-Signature: your-telnyx-signature" \
  -d '{"failed_request": "data"}'

# Fallback health check
curl https://abc123def4.execute-api.us-east-1.amazonaws.com/dev/webhooks/telnyx/fallback
```

## 💰 **Cost Analysis**

### **Monthly Costs (Estimated):**

| Component | Development | Production | Notes |
|-----------|-------------|------------|-------|
| **API Gateway Requests** | $0.10-1.00 | $1.00-10.00 | $3.50 per million requests |
| **Lambda Authorizer** | $0.05-0.50 | $0.50-5.00 | Pay per invocation |
| **CloudWatch Logs** | $0.50-2.00 | $2.00-10.00 | Based on log volume |
| **Data Transfer** | $0.10-1.00 | $1.00-5.00 | $0.09/GB outbound |
| **Total** | **$0.75-4.50** | **$4.50-30.00** | Usage-based pricing |

### **Cost Savings vs Private API:**
- **VPC Endpoint**: Saved $7.30/month
- **Simplified Architecture**: Reduced operational overhead
- **No Domain Costs**: Saved $0.50+/month per domain

### **Usage-Based Pricing Benefits:**
- **Low Traffic**: Very low costs for development
- **Scaling**: Costs scale with actual usage
- **No Fixed Costs**: No monthly infrastructure fees

## 🛠️ **Monitoring and Troubleshooting**

### **CloudWatch Logs:**
- **API Access Logs**: `/aws/apigateway/smsbot-{env}-network-api-telnyx-webhooks`
- **Authorizer Logs**: `/aws/lambda/smsbot-{env}-security-lambda-api-authorizer`
- **Fallback Logs**: `/aws/lambda/smsbot-{env}-compute-lambda-api-fallback`
- **SMS Handler Logs**: `/aws/lambda/smsbot-{env}-messaging-lambda-sms-handler`

### **Common Issues:**

1. **401 Unauthorized on Webhooks:**
   - **Check**: Telnyx signature header is present and valid
   - **Verify**: Authorizer function logs for validation errors
   - **Solution**: Ensure proper `X-Telnyx-Signature` header

2. **CORS Issues:**
   - **Check**: Preflight OPTIONS requests are working
   - **Verify**: CORS headers are properly configured
   - **Solution**: API Gateway CORS is pre-configured

3. **High Costs:**
   - **Check**: Request volume in CloudWatch metrics
   - **Monitor**: Authorizer cache hit rate
   - **Optimize**: Increase authorizer cache TTL if needed

### **Debugging Commands:**
```bash
# Check API Gateway
aws apigateway get-rest-apis --profile boss

# Test authorizer function directly
aws lambda invoke --function-name smsbot-dev-security-lambda-api-authorizer \
  --payload '{"headers":{"X-Telnyx-Signature":"test"}}' \
  response.json --profile boss

# Check API Gateway metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ApiGateway \
  --metric-name Count \
  --dimensions Name=ApiName,Value=smsbot-dev-network-api-telnyx-webhooks \
  --start-time 2024-01-01T00:00:00Z \
  --end-time 2024-01-02T00:00:00Z \
  --period 3600 \
  --statistics Sum \
  --profile boss
```

## 🔧 **Configuration for Telnyx**

### **Webhook URL Configuration:**
```bash
# Use the WebhookEndpoint output from your deployment
# Configure in Telnyx dashboard:
Webhook URL: https://abc123def4.execute-api.us-east-1.amazonaws.com/dev/webhooks/telnyx/sms
Failover URL: https://abc123def4.execute-api.us-east-1.amazonaws.com/dev/webhooks/telnyx/fallback
```

### **Security Configuration:**
- **Signature Validation**: Enabled via Lambda authorizer
- **HTTPS Only**: All endpoints use HTTPS
- **Request Logging**: All requests logged for debugging
- **Error Handling**: Proper error responses and fallback processing

## 📚 **Additional Resources**

- [API Gateway Pricing](https://aws.amazon.com/api-gateway/pricing/)
- [Lambda Authorizers](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-lambda-authorizer-lambda-function-create.html)
- [Telnyx Webhooks](https://developers.telnyx.com/docs/v2/messaging/webhooks)
- [API Gateway CORS](https://docs.aws.amazon.com/apigateway/latest/developerguide/how-to-cors.html)

---

**🌐 Your API Gateway is now public, cost-effective, and secure with Lambda authorization - no VPC costs and minimal infrastructure overhead!**
