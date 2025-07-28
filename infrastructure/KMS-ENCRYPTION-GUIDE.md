# 🔐 KMS Encryption Configuration Guide

## 🎯 **Current KMS Key Setup**

Your SMS Bot infrastructure now uses **customer-managed KMS keys** for comprehensive encryption across all services.

## 🔑 **KMS Keys Created**

### **1. Main SMS Bot Key**
- **Alias**: `smsbot-{env}-security-key-smsbot`
- **Purpose**: General encryption for the SMS Bot system
- **Key Rotation**: ✅ Enabled (automatic annual rotation)
- **Used By**: General encryption needs

### **2. SNS Encryption Key**
- **Alias**: `smsbot-{env}-security-key-sns`
- **Purpose**: Encrypt SNS messages in transit and at rest
- **Key Rotation**: ✅ Enabled
- **Used By**: 
  - `smsbot-{env}-messaging-topic-inbound-sms`
  - `smsbot-{env}-messaging-topic-delivery-status`

### **3. DynamoDB Encryption Key**
- **Alias**: `smsbot-{env}-security-key-dynamodb`
- **Purpose**: Encrypt DynamoDB data at rest
- **Key Rotation**: ✅ Enabled
- **Used By**:
  - `smsbot-{env}-storage-table-conversations`
  - `smsbot-{env}-storage-table-analytics`

### **4. CloudWatch Logs Key**
- **Alias**: `smsbot-{env}-security-key-logs`
- **Purpose**: Encrypt CloudWatch log data
- **Key Rotation**: ✅ Enabled
- **Used By**:
  - `smsbot-{env}-messaging-logs-sns`
  - Lambda function logs

## 📊 **Encryption Coverage**

| Service | Resource | Encryption Type | KMS Key |
|---------|----------|----------------|---------|
| **SNS Topics** | Inbound SMS | Customer-managed | SNS Key |
| **SNS Topics** | Delivery Status | Customer-managed | SNS Key |
| **DynamoDB** | Conversations Table | Customer-managed | DynamoDB Key |
| **DynamoDB** | Analytics Table | Customer-managed | DynamoDB Key |
| **CloudWatch** | SNS Logs | Customer-managed | Logs Key |
| **Lambda** | Function Code | AWS-managed | AWS Lambda Key |
| **Lambda** | Environment Variables | AWS-managed | AWS Lambda Key |

## 🔧 **Key Permissions**

### **Automatic Permissions Granted:**
- ✅ **Lambda Function**: Encrypt/decrypt permissions for SNS and DynamoDB keys
- ✅ **CloudWatch Logs**: Service permissions for logs key
- ✅ **SNS Service**: Permissions to use SNS key for message encryption
- ✅ **DynamoDB Service**: Permissions to use DynamoDB key for data encryption

### **IAM Policies Applied:**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "kms:Encrypt",
        "kms:Decrypt",
        "kms:ReEncrypt*",
        "kms:GenerateDataKey*",
        "kms:DescribeKey"
      ],
      "Resource": [
        "arn:aws:kms:region:account:key/sns-key-id",
        "arn:aws:kms:region:account:key/dynamodb-key-id"
      ]
    }
  ]
}
```

## 🚀 **Deployment with KMS**

### **Deploy with Enhanced Encryption:**
```bash
# Deploy with KMS encryption enabled
./scripts/deploy.sh dev your-company

# The stack will create:
# - 4 customer-managed KMS keys
# - Proper key policies and permissions
# - Encrypted resources using these keys
```

### **Verify KMS Keys After Deployment:**
```bash
# List KMS keys
aws kms list-keys --profile boss

# Get key details
aws kms describe-key --key-id alias/smsbot-dev-security-key-smsbot --profile boss
```

## 📋 **Stack Outputs (KMS Information)**

After deployment, you'll see these outputs:

```json
{
  "SMSBotKMSKeyId": "12345678-1234-1234-1234-123456789012",
  "SMSBotKMSKeyArn": "arn:aws:kms:us-east-1:123456789012:key/12345678-1234-1234-1234-123456789012",
  "DynamoDBKMSKeyId": "87654321-4321-4321-4321-210987654321",
  "SNSKMSKeyId": "11111111-2222-3333-4444-555555555555"
}
```

## 💰 **KMS Cost Implications**

### **KMS Key Costs:**
- **Customer-managed keys**: $1/month per key
- **Key usage**: $0.03 per 10,000 requests
- **Total monthly cost**: ~$4/month for 4 keys + usage

### **Environment-specific Costs:**
- **Development**: ~$4-6/month (lower usage)
- **Staging**: ~$6-10/month (moderate usage)
- **Production**: ~$10-20/month (higher usage)

### **Cost Optimization:**
- Keys are tagged with `OffHoursShutdown: disabled` (keys can't be shut down)
- Key rotation is enabled for security (no additional cost)
- Deletion protection matches environment (prod: enabled, dev: disabled)

## 🔒 **Security Benefits**

### **Enhanced Security:**
- ✅ **Customer Control**: You control the encryption keys
- ✅ **Key Rotation**: Automatic annual key rotation
- ✅ **Audit Trail**: All key usage logged in CloudTrail
- ✅ **Granular Permissions**: Service-specific key access
- ✅ **Compliance**: Meets most compliance requirements

### **Data Protection:**
- **SNS Messages**: Encrypted in transit and at rest
- **DynamoDB Data**: Encrypted at rest with customer keys
- **CloudWatch Logs**: Encrypted log data
- **Cross-Service**: Consistent encryption across all services

## 🛠️ **Key Management**

### **Key Rotation:**
```bash
# Check rotation status
aws kms get-key-rotation-status --key-id alias/smsbot-dev-security-key-smsbot --profile boss

# Enable rotation (already enabled by default)
aws kms enable-key-rotation --key-id alias/smsbot-dev-security-key-smsbot --profile boss
```

### **Key Policies:**
```bash
# View key policy
aws kms get-key-policy --key-id alias/smsbot-dev-security-key-smsbot --policy-name default --profile boss
```

### **Key Usage Monitoring:**
- **CloudTrail**: All KMS API calls logged
- **CloudWatch**: Key usage metrics available
- **Cost Explorer**: KMS costs tracked by key

## 🆘 **Troubleshooting KMS Issues**

### **Common Issues:**

1. **Access Denied Errors:**
   ```bash
   # Check key permissions
   aws kms describe-key --key-id alias/smsbot-dev-security-key-smsbot --profile boss
   ```

2. **Lambda Can't Access Encrypted Resources:**
   - Verify Lambda execution role has KMS permissions
   - Check key policies allow Lambda service access

3. **SNS Encryption Errors:**
   - Ensure SNS service has permissions to use the key
   - Verify key policy allows SNS operations

### **Key Recovery:**
- **Development**: Keys can be deleted (7-30 day recovery window)
- **Production**: Keys have deletion protection enabled
- **Backup**: Key policies and configurations are in CDK code

## 📚 **Additional Resources**

- [AWS KMS Best Practices](https://docs.aws.amazon.com/kms/latest/developerguide/best-practices.html)
- [KMS Key Policies](https://docs.aws.amazon.com/kms/latest/developerguide/key-policies.html)
- [SNS Encryption](https://docs.aws.amazon.com/sns/latest/dg/sns-server-side-encryption.html)
- [DynamoDB Encryption](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/encryption.tutorial.html)

---

**🔐 Your SMS Bot infrastructure now uses comprehensive customer-managed KMS encryption for all services!**
