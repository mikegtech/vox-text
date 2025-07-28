# ☁️ Cloudflare Tunnel + ECS Fargate Configuration Guide

## 🎯 **Architecture Overview**

Your SMS Bot now uses **ECS Fargate** with **Cloudflare Tunnel** for secure ingress, eliminating the need for public load balancers or API Gateway.

```
Internet → Cloudflare → Cloudflare Tunnel → ECS Fargate (Private)
```

### **Benefits:**
- ✅ **No Public Load Balancer**: Save ~$16-25/month on ALB costs
- ✅ **No API Gateway**: Save request-based costs
- ✅ **Secure Ingress**: Cloudflare Tunnel provides secure connectivity
- ✅ **DDoS Protection**: Cloudflare's built-in protection
- ✅ **SSL Termination**: Handled by Cloudflare
- ✅ **Global CDN**: Cloudflare's edge network

## 🏗️ **ECS Fargate Infrastructure**

### **Created Resources:**

| Resource | Name | Purpose |
|----------|------|---------|
| **ECS Cluster** | `smsbot-{env}-compute-cluster-smsbot` | Container orchestration |
| **ECS Service** | `smsbot-{env}-compute-service-smsbot` | Running container service |
| **Task Definition** | `smsbot-{env}-compute-task-smsbot` | Container configuration |
| **Security Group** | `smsbot-{env}-network-sg-ecs-tasks` | Network access control |
| **Service Discovery** | `smsbot-{env}.local` | Internal DNS resolution |
| **Secrets Manager** | `smsbot-{env}-security-secret-telnyx` | Telnyx API configuration |
| **Secrets Manager** | `smsbot-{env}-security-secret-app-config` | Application secrets |

### **Container Configuration:**
- **CPU**: 256 (dev) / 512 (prod)
- **Memory**: 512MB (dev) / 1024MB (prod)
- **Port**: 8080 (HTTP)
- **Health Check**: `/health` endpoint
- **Logging**: CloudWatch Logs

## 🔧 **ECS Task Configuration**

### **Environment Variables:**
```bash
ENVIRONMENT=dev
AWS_REGION=us-east-1
CONVERSATIONS_TABLE=smsbot-dev-storage-table-conversations
ANALYTICS_TABLE=smsbot-dev-storage-table-analytics
INBOUND_SNS_TOPIC=arn:aws:sns:us-east-1:123456789012:smsbot-dev-messaging-topic-inbound-sms
DELIVERY_SNS_TOPIC=arn:aws:sns:us-east-1:123456789012:smsbot-dev-messaging-topic-delivery-status
PORT=8080
```

### **Secrets (from AWS Secrets Manager):**
```bash
TELNYX_CONFIG={"api_key": "your-api-key", "webhook_secret": "your-webhook-secret"}
APP_CONFIG={"jwt_secret": "generated-secret", "encryption_key": "generated-key"}
```

### **IAM Permissions:**
- **DynamoDB**: Read/write access to conversations and analytics tables
- **SNS**: Publish permissions to inbound and delivery topics
- **KMS**: Encrypt/decrypt permissions for customer-managed keys
- **Secrets Manager**: Read access to configuration secrets

## ☁️ **Cloudflare Tunnel Setup**

### **1. Install Cloudflared**
```bash
# On your local machine or CI/CD system
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i cloudflared.deb
```

### **2. Authenticate with Cloudflare**
```bash
cloudflared tunnel login
```

### **3. Create Tunnel**
```bash
# Create tunnel
cloudflared tunnel create smsbot-{environment}

# Note the tunnel ID from the output
```

### **4. Configure DNS**
```bash
# Add DNS record pointing to your tunnel
cloudflared tunnel route dns smsbot-{environment} sms-webhooks.yourdomain.com
```

### **5. Create Configuration File**
Create `~/.cloudflared/config.yml`:
```yaml
tunnel: smsbot-dev  # Your tunnel name
credentials-file: /home/user/.cloudflared/your-tunnel-id.json

ingress:
  # SMS webhook endpoint
  - hostname: sms-webhooks.yourdomain.com
    path: /webhooks/telnyx/sms
    service: http://smsbot-dev-compute-service-smsbot.smsbot-dev.local:8080
    
  # Health check endpoint  
  - hostname: sms-webhooks.yourdomain.com
    path: /health
    service: http://smsbot-dev-compute-service-smsbot.smsbot-dev.local:8080
    
  # Fallback endpoint
  - hostname: sms-webhooks.yourdomain.com
    path: /webhooks/telnyx/fallback
    service: http://smsbot-dev-compute-service-smsbot.smsbot-dev.local:8080
    
  # Catch-all rule (required)
  - service: http_status:404
```

### **6. Run Tunnel**
```bash
# Test the tunnel
cloudflared tunnel run smsbot-dev

# Run as service (production)
sudo cloudflared service install
sudo systemctl start cloudflared
sudo systemctl enable cloudflared
```

## 🐳 **Container Application Structure**

### **Required Endpoints:**
Your containerized application should expose these endpoints:

```python
# Example Flask application structure
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': os.environ.get('APP_VERSION', '1.0.0')
    })

@app.route('/webhooks/telnyx/sms', methods=['POST'])
def telnyx_sms_webhook():
    # Validate Telnyx signature
    # Process SMS webhook
    # Publish to SNS
    # Store in DynamoDB
    return jsonify({'status': 'processed'})

@app.route('/webhooks/telnyx/fallback', methods=['POST'])
def telnyx_fallback():
    # Handle failed webhook processing
    # Log to analytics table
    return jsonify({'status': 'logged'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
```

### **Dockerfile Example:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Run application
CMD ["python", "app.py"]
```

## 📊 **Service Discovery URLs**

After deployment, your ECS service will be available at:

```bash
# Internal service discovery (for Cloudflare Tunnel)
http://smsbot-dev-compute-service-smsbot.smsbot-dev.local:8080

# Health check
http://smsbot-dev-compute-service-smsbot.smsbot-dev.local:8080/health

# SMS webhook
http://smsbot-dev-compute-service-smsbot.smsbot-dev.local:8080/webhooks/telnyx/sms

# Fallback webhook
http://smsbot-dev-compute-service-smsbot.smsbot-dev.local:8080/webhooks/telnyx/fallback
```

## 🚀 **Deployment Process**

### **1. Deploy Infrastructure**
```bash
# Deploy ECS Fargate infrastructure
./scripts/deploy.sh dev your-company

# Note the outputs:
# - ECSClusterName
# - ECSServiceName  
# - ServiceDiscoveryURL
# - TelnyxSecretArn
```

### **2. Configure Secrets**
```bash
# Update Telnyx configuration
aws secretsmanager update-secret \
  --secret-id smsbot-dev-security-secret-telnyx \
  --secret-string '{"api_key":"your-telnyx-api-key","webhook_secret":"your-webhook-secret"}' \
  --profile boss

# Application config is auto-generated
```

### **3. Build and Push Container**
```bash
# Build your container image
docker build -t smsbot:latest .

# Tag for ECR (if using ECR)
docker tag smsbot:latest 123456789012.dkr.ecr.us-east-1.amazonaws.com/smsbot:latest

# Push to registry
docker push 123456789012.dkr.ecr.us-east-1.amazonaws.com/smsbot:latest
```

### **4. Update Task Definition**
```bash
# Update the task definition with your actual image
# This can be done via CDK or AWS CLI
```

### **5. Setup Cloudflare Tunnel**
```bash
# Follow the Cloudflare Tunnel setup steps above
# Point tunnel to your service discovery URL
```

## 💰 **Cost Analysis**

### **ECS Fargate Costs:**

| Environment | vCPU | Memory | Hours/Month | Cost/Month |
|-------------|------|--------|-------------|------------|
| **Development** | 0.25 | 0.5GB | 730 | ~$6.50 |
| **Production** | 0.5 | 1GB | 730 × 2 tasks | ~$26.00 |

### **Additional Costs:**
- **Secrets Manager**: $0.40/month per secret (2 secrets = $0.80)
- **CloudWatch Logs**: $0.50-5.00/month depending on volume
- **Service Discovery**: $0.50/month per namespace

### **Total Monthly Costs:**
- **Development**: ~$8-10/month
- **Production**: ~$30-35/month

### **Cost Savings vs ALB:**
- **No Application Load Balancer**: Save $16-25/month
- **No API Gateway**: Save request-based costs
- **Cloudflare Tunnel**: Free (with Cloudflare account)

## 🔍 **Monitoring and Troubleshooting**

### **CloudWatch Logs:**
- **ECS Task Logs**: `/aws/ecs/smsbot-{env}-compute-task-smsbot`
- **Service Events**: Available in ECS console

### **Health Checks:**
```bash
# Check service health via Cloudflare Tunnel
curl https://sms-webhooks.yourdomain.com/health

# Check internal health (from within VPC)
curl http://smsbot-dev-compute-service-smsbot.smsbot-dev.local:8080/health
```

### **Common Issues:**

1. **Container Won't Start:**
   - Check CloudWatch logs for startup errors
   - Verify secrets are properly configured
   - Ensure container image is accessible

2. **Cloudflare Tunnel Connection Issues:**
   - Verify service discovery DNS resolution
   - Check security group allows port 8080
   - Ensure tunnel configuration is correct

3. **High Costs:**
   - Monitor task CPU/memory utilization
   - Adjust task size if over-provisioned
   - Consider spot capacity for development

### **Debugging Commands:**
```bash
# Check ECS service status
aws ecs describe-services \
  --cluster smsbot-dev-compute-cluster-smsbot \
  --services smsbot-dev-compute-service-smsbot \
  --profile boss

# Check task health
aws ecs describe-tasks \
  --cluster smsbot-dev-compute-cluster-smsbot \
  --tasks $(aws ecs list-tasks --cluster smsbot-dev-compute-cluster-smsbot --query 'taskArns[0]' --output text) \
  --profile boss

# View logs
aws logs tail /aws/ecs/smsbot-dev-compute-task-smsbot --follow --profile boss
```

## 📚 **Next Steps**

1. **Build Your Container**: Create a containerized version of your SMS webhook handler
2. **Configure Secrets**: Update the Telnyx and application secrets
3. **Setup Cloudflare Tunnel**: Configure tunnel to point to your ECS service
4. **Test Webhooks**: Verify Telnyx webhooks are properly routed
5. **Monitor Performance**: Set up CloudWatch alarms and dashboards

---

**☁️ Your SMS Bot now runs on ECS Fargate with secure Cloudflare Tunnel ingress - no public load balancers needed!**
