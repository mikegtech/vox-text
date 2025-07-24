# 🌐 Custom Domain Setup for API Gateway

## 📋 **Prerequisites**

Before setting up a custom domain, you need:
- ✅ **Domain name** you own (e.g., `sms-api.yourdomain.com`)
- ✅ **SSL certificate** in AWS Certificate Manager (ACM)
- ✅ **DNS access** to create CNAME records

## 🔧 **Step-by-Step Setup**

### Step 1: Request SSL Certificate
```bash
# Request certificate for your domain
aws acm request-certificate \
  --domain-name "sms-api.yourdomain.com" \
  --validation-method DNS \
  --profile boss

# Note the certificate ARN from the output
```

### Step 2: Validate Certificate
1. **Go to AWS Console** → Certificate Manager
2. **Find your certificate** and click on it
3. **Create DNS records** as shown in the validation section
4. **Wait for validation** (usually 5-10 minutes)
5. **Certificate status** should change to "Issued"

### Step 3: Deploy with Custom Domain
```bash
# Deploy with custom domain configuration
cd infrastructure
./scripts/deploy-with-custom-domain.sh \
  dev \
  your-company \
  "sms-api.yourdomain.com" \
  "arn:aws:acm:us-east-1:123456789012:certificate/your-cert-id" \
  boss
```

### Step 4: Configure DNS
After deployment, create a CNAME record:
```
Name: sms-api.yourdomain.com
Type: CNAME
Value: d-abc123.execute-api.us-east-1.amazonaws.com (from deployment output)
```

### Step 5: Test Custom Domain
```bash
# Test health endpoint
curl https://sms-api.yourdomain.com/health

# Should return: {"status":"healthy","timestamp":"...","environment":"dev"}
```

## 🎯 **What You Get**

### **Custom Domain Benefits:**
- ✅ **Professional URLs**: `https://sms-api.yourdomain.com/webhook/sms`
- ✅ **SSL/TLS Security**: Automatic HTTPS with your certificate
- ✅ **Brand Consistency**: Uses your domain instead of AWS URLs
- ✅ **Easy Management**: Update backend without changing webhook URLs

### **Resources Created:**
```
Custom Domain Resources:
├── API Gateway Domain Name (sms-api.yourdomain.com)
├── Base Path Mapping (/ → your API)
├── SSL Certificate (from ACM)
└── DNS CNAME (points to API Gateway)
```

## 📊 **Deployment Outputs**

After successful deployment, you'll see:
```json
{
  "WebhookEndpoint": "https://sms-api.yourdomain.com/webhook/sms",
  "HealthCheckEndpoint": "https://sms-api.yourdomain.com/health",
  "CustomDomainName": "sms-api.yourdomain.com",
  "DomainNameTarget": "d-abc123.execute-api.us-east-1.amazonaws.com"
}
```

## 🔍 **Troubleshooting**

### **Certificate Issues:**
```bash
# Check certificate status
aws acm describe-certificate --certificate-arn "your-cert-arn" --profile boss

# List all certificates
aws acm list-certificates --profile boss
```

### **DNS Issues:**
```bash
# Test DNS resolution
nslookup sms-api.yourdomain.com

# Test with dig
dig sms-api.yourdomain.com CNAME
```

### **API Gateway Issues:**
```bash
# Check custom domain status
aws apigateway get-domain-name --domain-name "sms-api.yourdomain.com" --profile boss

# Check base path mappings
aws apigateway get-base-path-mappings --domain-name "sms-api.yourdomain.com" --profile boss
```

## 🚀 **Quick Commands**

### **Deploy with Custom Domain:**
```bash
./scripts/deploy-with-custom-domain.sh dev your-company sms-api.yourdomain.com arn:aws:acm:us-east-1:123456789012:certificate/abc123 boss
```

### **Deploy without Custom Domain:**
```bash
./deploy-with-boss.sh dev your-company
```

### **Update Existing Stack with Custom Domain:**
```bash
# Just run the custom domain deployment script
./scripts/deploy-with-custom-domain.sh dev your-company sms-api.yourdomain.com arn:aws:acm:us-east-1:123456789012:certificate/abc123 boss
```

## 📋 **Next Steps After Custom Domain Setup**

1. ✅ **Test custom domain** health endpoint
2. ✅ **Configure Telnyx webhook** with custom URL
3. ✅ **Add Telnyx public key** to Secrets Manager
4. ✅ **Test SMS integration** end-to-end
5. ✅ **Monitor logs** and metrics

Your custom domain will make your SMS bot infrastructure look professional and provide a stable endpoint for Telnyx webhooks! 🎉
