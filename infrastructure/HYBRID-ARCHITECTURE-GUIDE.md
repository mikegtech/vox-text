# 🏗️ Hybrid Architecture: API Gateway + ECS Fargate + Traefik

## 🎯 **Architecture Overview**

Your SMS Bot now uses a **hybrid architecture** with both **API Gateway** and **ECS Fargate**, allowing Traefik to route to multiple AWS API Gateways and other services.

```
Internet → Traefik → {
  ├── AWS API Gateway (HTTP/REST endpoints)
  ├── ECS Fargate (Containerized services)  
  ├── Other AWS API Gateways
  └── Non-AWS services
}
```

### **Why This Architecture?**
- ✅ **API Gateway**: Provides HTTP/REST endpoints for Traefik routing
- ✅ **ECS Fargate**: Containerized services for complex processing
- ✅ **Traefik**: Central routing to multiple backends
- ✅ **Flexibility**: Mix of serverless and containerized workloads
- ✅ **Scalability**: Each component scales independently

## 🏗️ **Infrastructure Components**

### **1. API Gateway Layer (for Traefik)**
- **Purpose**: HTTP/REST endpoints for external routing
- **Endpoints**: `/webhooks/telnyx/sms`, `/webhooks/telnyx/fallback`, `/health`
- **Authentication**: Lambda authorizer with Telnyx signature validation
- **Scaling**: Automatic based on request volume

### **2. ECS Fargate Layer (for Containers)**
- **Purpose**: Containerized services and complex processing
- **Services**: Long-running processes, background tasks, APIs
- **Communication**: Service discovery for internal communication
- **Scaling**: Task-based scaling with CPU/memory metrics

### **3. Shared Infrastructure**
- **DynamoDB**: Shared data storage for both layers
- **SNS**: Message passing between components
- **KMS**: Encryption for all services
- **Secrets Manager**: Configuration for containers

## 📊 **Resource Overview**

### **API Gateway Resources:**
```
├── smsbot-dev-network-api-telnyx-webhooks (API Gateway)
├── smsbot-dev-security-lambda-api-authorizer (Lambda Authorizer)
├── smsbot-dev-compute-lambda-api-fallback (Lambda Fallback)
└── API Gateway Endpoints:
    ├── GET  /health
    ├── POST /webhooks/telnyx/sms
    └── POST /webhooks/telnyx/fallback
```

### **ECS Fargate Resources:**
```
├── smsbot-dev-compute-cluster-smsbot (ECS Cluster)
├── smsbot-dev-compute-service-smsbot (ECS Service)
├── smsbot-dev-compute-task-smsbot (ECS Task Definition)
├── smsbot-dev-network-sg-ecs-tasks (Security Group)
├── smsbot-dev-security-secret-telnyx (Secrets Manager)
├── smsbot-dev-security-secret-app-config (Secrets Manager)
└── Service Discovery: smsbot-dev.local
```

### **Shared Resources:**
```
├── smsbot-dev-storage-table-conversations (DynamoDB)
├── smsbot-dev-storage-table-analytics (DynamoDB)
├── smsbot-dev-messaging-topic-inbound-sms (SNS)
├── smsbot-dev-messaging-topic-delivery-status (SNS)
├── smsbot-dev-messaging-lambda-sms-handler (Lambda)
└── KMS Keys (4 customer-managed keys)
```

## 🔗 **Traefik Configuration**

### **Traefik Dynamic Configuration:**
```yaml
# traefik-dynamic.yml
http:
  routers:
    # SMS Bot API Gateway routes
    smsbot-api-webhooks:
      rule: "Host(`api.yourdomain.com`) && PathPrefix(`/sms/webhooks`)"
      service: smsbot-api-gateway
      middlewares:
        - strip-sms-prefix
        
    smsbot-api-health:
      rule: "Host(`api.yourdomain.com`) && Path(`/sms/health`)"
      service: smsbot-api-gateway
      middlewares:
        - strip-sms-prefix
    
    # Other API Gateway routes
    other-service-api:
      rule: "Host(`api.yourdomain.com`) && PathPrefix(`/other`)"
      service: other-api-gateway
      
    # ECS Fargate routes (if needed for direct access)
    smsbot-ecs-admin:
      rule: "Host(`admin.yourdomain.com`) && PathPrefix(`/sms`)"
      service: smsbot-ecs-fargate

  services:
    # SMS Bot API Gateway
    smsbot-api-gateway:
      loadBalancer:
        servers:
          - url: "https://abc123def4.execute-api.us-east-1.amazonaws.com/dev/"
        healthCheck:
          path: "/health"
          interval: "30s"
          timeout: "5s"
          
    # Other API Gateway
    other-api-gateway:
      loadBalancer:
        servers:
          - url: "https://xyz789ghi0.execute-api.us-east-1.amazonaws.com/prod/"
          
    # ECS Fargate (internal access)
    smsbot-ecs-fargate:
      loadBalancer:
        servers:
          - url: "http://smsbot-dev-compute-service-smsbot.smsbot-dev.local:8080"

  middlewares:
    strip-sms-prefix:
      stripPrefix:
        prefixes:
          - "/sms"
```

### **Traefik Static Configuration:**
```yaml
# traefik.yml
api:
  dashboard: true
  insecure: true

entryPoints:
  web:
    address: ":80"
  websecure:
    address: ":443"

providers:
  file:
    filename: /etc/traefik/traefik-dynamic.yml
    watch: true

certificatesResolvers:
  letsencrypt:
    acme:
      email: admin@yourdomain.com
      storage: acme.json
      httpChallenge:
        entryPoint: web
```

## 🚀 **Deployment Outputs**

After deployment, you'll get both API Gateway and ECS endpoints:

### **API Gateway Endpoints (for Traefik):**
```json
{
  "ApiGatewayUrl": "https://abc123def4.execute-api.us-east-1.amazonaws.com/dev/",
  "WebhookEndpoint": "https://abc123def4.execute-api.us-east-1.amazonaws.com/dev/webhooks/telnyx/sms",
  "FallbackEndpoint": "https://abc123def4.execute-api.us-east-1.amazonaws.com/dev/webhooks/telnyx/fallback",
  "HealthCheckEndpoint": "https://abc123def4.execute-api.us-east-1.amazonaws.com/dev/health"
}
```

### **ECS Fargate Endpoints (internal):**
```json
{
  "ServiceDiscoveryURL": "http://smsbot-dev-compute-service-smsbot.smsbot-dev.local:8080",
  "ECSHealthCheckURL": "http://smsbot-dev-compute-service-smsbot.smsbot-dev.local:8080/health",
  "ECSClusterName": "smsbot-dev-compute-cluster-smsbot",
  "ECSServiceName": "smsbot-dev-compute-service-smsbot"
}
```

## 🔄 **Request Flow Examples**

### **1. Webhook via API Gateway:**
```
Telnyx → Traefik → API Gateway → Lambda Authorizer → SMS Handler Lambda → SNS/DynamoDB
```

### **2. Admin Interface via ECS:**
```
Admin User → Traefik → ECS Fargate → Container App → DynamoDB
```

### **3. Background Processing:**
```
SNS Message → Lambda → ECS Task (via ECS API) → Container Processing
```

### **4. Inter-service Communication:**
```
API Gateway Lambda → SNS → ECS Container → Service Discovery → Another ECS Service
```

## 💰 **Cost Analysis**

### **Monthly Costs by Component:**

| Component | Development | Production | Notes |
|-----------|-------------|------------|-------|
| **API Gateway** | $0.10-1.00 | $1.00-10.00 | Request-based pricing |
| **Lambda Functions** | $0.25-2.00 | $2.00-20.00 | Authorizer + SMS handler |
| **ECS Fargate** | $6.50 | $26.00 | Container compute |
| **DynamoDB** | $0.25-2.00 | $2.50-25.00 | Pay-per-request |
| **SNS** | $0.50 | $5.00 | Message publishing |
| **KMS Keys** | $4.00 | $4.00 | 4 customer-managed keys |
| **Secrets Manager** | $0.80 | $0.80 | 2 secrets |
| **CloudWatch Logs** | $0.50-2.00 | $5.00-15.00 | Log retention |
| **Service Discovery** | $0.50 | $0.50 | Private DNS namespace |
| **Total** | **$13-19** | **$46-106** | Usage-dependent |

### **Cost Benefits:**
- **Hybrid Approach**: Pay for what you use in each layer
- **No ALB**: ECS uses service discovery (save $16-25/month)
- **Shared Resources**: DynamoDB and SNS used by both layers
- **Efficient Scaling**: Each component scales independently

## 🔧 **Development Workflow**

### **1. API Gateway Development:**
```bash
# Test API Gateway endpoints
curl https://abc123def4.execute-api.us-east-1.amazonaws.com/dev/health

# Test webhook with Telnyx signature
curl -X POST \
  https://abc123def4.execute-api.us-east-1.amazonaws.com/dev/webhooks/telnyx/sms \
  -H "X-Telnyx-Signature: your-signature" \
  -d '{"test": "webhook"}'
```

### **2. ECS Container Development:**
```bash
# Build and test container locally
docker build -t smsbot:latest .
docker run -p 8080:8080 smsbot:latest

# Test container health
curl http://localhost:8080/health
```

### **3. Deploy Infrastructure:**
```bash
# Deploy both API Gateway and ECS
./scripts/deploy.sh dev your-company

# Update container image
aws ecs update-service \
  --cluster smsbot-dev-compute-cluster-smsbot \
  --service smsbot-dev-compute-service-smsbot \
  --force-new-deployment \
  --profile boss
```

### **4. Configure Traefik:**
```bash
# Update Traefik configuration with new endpoints
# Point to API Gateway URLs from deployment outputs
# Configure health checks and load balancing
```

## 🔍 **Monitoring and Observability**

### **API Gateway Monitoring:**
- **CloudWatch Metrics**: Request count, latency, errors
- **Access Logs**: Detailed request/response logging
- **Lambda Metrics**: Authorizer performance and errors

### **ECS Fargate Monitoring:**
- **Container Insights**: CPU, memory, network metrics
- **Task Health**: Health check status and failures
- **Service Events**: Deployment and scaling events

### **Shared Resource Monitoring:**
- **DynamoDB**: Read/write capacity, throttling
- **SNS**: Message publishing, delivery status
- **KMS**: Key usage and rotation status

### **Traefik Monitoring:**
- **Request Metrics**: Response times, status codes
- **Backend Health**: API Gateway and ECS health checks
- **Load Distribution**: Traffic routing patterns

## 🛠️ **Troubleshooting**

### **Common Issues:**

1. **API Gateway 401 Errors:**
   - Check Lambda authorizer logs
   - Verify Telnyx signature validation
   - Ensure proper headers are sent

2. **ECS Task Startup Failures:**
   - Check CloudWatch logs for container errors
   - Verify secrets are properly configured
   - Ensure security group allows port 8080

3. **Traefik Routing Issues:**
   - Verify backend health checks are passing
   - Check Traefik dashboard for service status
   - Ensure DNS resolution for service discovery

4. **Inter-service Communication:**
   - Verify service discovery DNS resolution
   - Check security group rules
   - Ensure proper IAM permissions

### **Debugging Commands:**
```bash
# Check API Gateway
aws apigateway get-rest-apis --profile boss

# Check ECS service status
aws ecs describe-services \
  --cluster smsbot-dev-compute-cluster-smsbot \
  --services smsbot-dev-compute-service-smsbot \
  --profile boss

# Test service discovery
nslookup smsbot-dev-compute-service-smsbot.smsbot-dev.local

# Check Traefik logs
docker logs traefik-container
```

## 📚 **Next Steps**

1. **Deploy Infrastructure:**
   ```bash
   ./scripts/deploy.sh dev your-company
   ```

2. **Configure Traefik:**
   - Update dynamic configuration with API Gateway URLs
   - Set up health checks for both layers
   - Configure SSL certificates

3. **Build Container Applications:**
   - Create containerized services for ECS
   - Implement health check endpoints
   - Configure secrets and environment variables

4. **Test End-to-End:**
   - Verify Traefik routing to API Gateway
   - Test ECS container deployment
   - Validate inter-service communication

5. **Monitor and Optimize:**
   - Set up CloudWatch dashboards
   - Configure alerts for both layers
   - Optimize costs based on usage patterns

---

**🏗️ Your hybrid architecture provides the flexibility of API Gateway endpoints for Traefik routing plus the power of containerized ECS services!**
