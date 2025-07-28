# 🌐 Private API Gateway Configuration Guide

## 🎯 **API Gateway Changes Made**

Your SMS Bot infrastructure now uses a **private API Gateway** in the default VPC **without custom domains or certificates**. This provides secure, internal-only access to your webhook endpoints.

## 🔧 **What Was Removed**

### ❌ **Removed Components:**
- **Custom Domain**: No more `customDomain` configuration
- **SSL Certificates**: No ACM certificate management
- **Public Access**: API is now private to VPC only
- **DNS Configuration**: No Route53 or CNAME setup required

### ✅ **What Remains:**
- **Lambda Authorizer**: Telnyx signature validation
- **Webhook Endpoints**: SMS and fallback endpoints
- **Health Checks**: API health monitoring
- **Logging**: CloudWatch access logs and metrics
- **CORS**: Cross-origin request handling

## 🏗️ **New Private API Architecture**

### **API Gateway Configuration:**
```python
# Private API in default VPC
endpoint_configuration=apigateway.EndpointConfiguration(
    types=[apigateway.EndpointType.PRIVATE],
    vpc_endpoints=[vpc_endpoint]
)

# Resource policy restricts access to VPC only
policy=self._create_resource_policy(default_vpc.vpc_id)
```

### **VPC Endpoint:**
- **Type**: Gateway VPC Endpoint for API Gateway
- **Location**: Default VPC
- **Access**: Internal VPC traffic only

### **Resource Policy:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": "execute-api:Invoke",
      "Resource": "execute-api:/*",
      "Condition": {
        "StringEquals": {
          "aws:sourceVpc": "vpc-xxxxxxxxx"
        }
      }
    },
    {
      "Effect": "Deny",
      "Principal": "*", 
      "Action": "execute-api:Invoke",
      "Resource": "execute-api:/*",
      "Condition": {
        "StringNotEquals": {
          "aws:sourceVpc": "vpc-xxxxxxxxx"
        }
      }
    }
  ]
}
```

## 📊 **API Endpoints Created**

### **1. Health Check Endpoint**
- **URL**: `https://{api-id}.execute-api.{region}.amazonaws.com/{stage}/health`
- **Method**: GET
- **Auth**: None required
- **Response**: `{"status": "healthy", "timestamp": "..."}`

### **2. SMS Webhook Endpoint**
- **URL**: `https://{api-id}.execute-api.{region}.amazonaws.com/{stage}/webhooks/telnyx/sms`
- **Method**: POST
- **Auth**: Lambda authorizer (Telnyx signature validation)
- **Handler**: Your existing SMS handler Lambda function

### **3. Fallback Webhook Endpoint**
- **URL**: `https://{api-id}.execute-api.{region}.amazonaws.com/{stage}/webhooks/telnyx/fallback`
- **Method**: POST
- **Auth**: Lambda authorizer
- **Handler**: New fallback Lambda function for error handling

### **4. Fallback Health Check**
- **URL**: `https://{api-id}.execute-api.{region}.amazonaws.com/{stage}/webhooks/telnyx/fallback`
- **Method**: GET
- **Auth**: None required
- **Response**: `{"status": "fallback-healthy", "timestamp": "..."}`

## 🔐 **Security Features**

### **Lambda Authorizer:**
- **Function**: `smsbot-{env}-security-lambda-api-authorizer`
- **Purpose**: Validates Telnyx webhook signatures
- **Headers**: Checks `X-Telnyx-Signature` and `Authorization`
- **Cache**: 5-minute TTL for performance

### **VPC-Only Access:**
- **Private API**: Only accessible from within the VPC
- **No Internet Access**: External requests are blocked
- **Internal Services**: Perfect for internal microservices

### **IAM Permissions:**
- **Authorizer Function**: Read access to DynamoDB for validation
- **Fallback Function**: Write access to analytics table
- **KMS Encryption**: All functions can decrypt with customer keys

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

## 🚀 **Deployment Changes**

### **No Additional Configuration Required:**
```bash
# Deploy as usual - no domain/certificate setup needed
./scripts/deploy.sh dev your-company

# API Gateway will be created automatically as private
```

### **What's Automatic:**
- ✅ **VPC Endpoint**: Created automatically in default VPC
- ✅ **Resource Policy**: Applied automatically for VPC-only access
- ✅ **Lambda Functions**: Authorizer and fallback functions deployed
- ✅ **IAM Roles**: Proper permissions configured automatically
- ✅ **CloudWatch Logs**: API access logging enabled

## 🔍 **Testing the Private API**

### **From Within VPC:**
```bash
# Health check (from EC2 instance in same VPC)
curl https://abc123def4.execute-api.us-east-1.amazonaws.com/dev/health

# Expected response:
# {"status": "healthy", "timestamp": "2024-01-15T10:30:00Z"}
```

### **From Outside VPC:**
```bash
# This will fail with 403 Forbidden
curl https://abc123def4.execute-api.us-east-1.amazonaws.com/dev/health

# Expected response:
# {"message": "Forbidden"}
```

### **Webhook Testing (from within VPC):**
```bash
# Test SMS webhook with proper headers
curl -X POST \
  https://abc123def4.execute-api.us-east-1.amazonaws.com/dev/webhooks/telnyx/sms \
  -H "Content-Type: application/json" \
  -H "X-Telnyx-Signature: your-signature" \
  -d '{"test": "webhook"}'
```

## 💰 **Cost Implications**

### **Cost Savings:**
- ❌ **No Custom Domain**: Save ~$0.50/month per domain
- ❌ **No ACM Certificate**: Free certificates not needed
- ❌ **No Route53**: No DNS hosting costs
- ✅ **VPC Endpoint**: ~$7.30/month (730 hours × $0.01/hour)

### **API Gateway Costs:**
- **Requests**: $3.50 per million requests
- **Data Transfer**: $0.09/GB for data transfer out
- **VPC Endpoint**: $7.30/month for gateway endpoint

### **Total Monthly Cost:**
- **Development**: ~$10-15/month
- **Production**: ~$15-30/month (depending on traffic)

## 🛠️ **Monitoring and Troubleshooting**

### **CloudWatch Logs:**
- **API Access Logs**: `/aws/apigateway/smsbot-{env}-network-api-telnyx-webhooks`
- **Authorizer Logs**: `/aws/lambda/smsbot-{env}-security-lambda-api-authorizer`
- **Fallback Logs**: `/aws/lambda/smsbot-{env}-compute-lambda-api-fallback`

### **Common Issues:**

1. **403 Forbidden from Outside VPC:**
   - **Expected**: API is private to VPC only
   - **Solution**: Access from within VPC or use VPN

2. **Authorizer Failures:**
   - **Check**: Lambda authorizer logs
   - **Verify**: Telnyx signature headers are present

3. **VPC Endpoint Issues:**
   - **Check**: VPC endpoint is created and active
   - **Verify**: Security groups allow HTTPS traffic

### **Debugging Commands:**
```bash
# Check VPC endpoints
aws ec2 describe-vpc-endpoints --profile boss

# Check API Gateway
aws apigateway get-rest-apis --profile boss

# Test authorizer function
aws lambda invoke --function-name smsbot-dev-security-lambda-api-authorizer \
  --payload '{"headers":{"X-Telnyx-Signature":"test"}}' \
  response.json --profile boss
```

## 📚 **Additional Resources**

- [Private API Gateways](https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-private-apis.html)
- [VPC Endpoints](https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints.html)
- [Lambda Authorizers](https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-lambda-authorizer-lambda-function-create.html)

---

**🌐 Your API Gateway is now private, secure, and accessible only from within your VPC - no custom domains or certificates required!**
