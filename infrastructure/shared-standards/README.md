# AWS CDK Standards Library

A shared library for consistent naming conventions and tagging strategies across AWS CDK applications, supporting both **Python** and **TypeScript**.

## 🎯 **Problem Solved**

This library ensures consistent resource naming and tagging across all your CDK applications, regardless of the programming language used. It implements your SMS Bot infrastructure's proven naming and tagging patterns.

## 🏗️ **Architecture**

### Naming Convention
All resources follow: `{project}-{environment}-{service}-{resource-type}-{identifier}`

**Examples:**
- Lambda: `inventory-prod-api-lambda-handler`
- DynamoDB: `inventory-prod-storage-table-products`
- SNS Topic: `inventory-prod-messaging-topic-orders`

### Tagging Strategy
Comprehensive tagging for:
- **Cost Allocation**: Project, Environment, Service, CostCenter
- **Governance**: Company, Owner, ManagedBy, CreatedBy
- **Operations**: OffHoursShutdown, BackupEnabled, MonitoringLevel
- **Compliance**: Tenant, DataRetention, DeletionProtection

## 📦 **Installation**

### Python
```bash
# Install from local directory (for development)
cd shared-standards
pip install -e .

# Or install from published package (future)
pip install your-company-aws-standards
```

### TypeScript
```bash
# Install from local directory (for development)  
cd shared-standards/typescript
npm install
npm run build
npm link

# In your project
npm link @your-company/aws-cdk-standards

# Or install from published package (future)
npm install @your-company/aws-cdk-standards
```

## 🚀 **Usage**

### Python Example

```python
import aws_cdk as cdk
from m3_aws_standards import (
    StandardizedStack,
    StandardizedLambda, 
    NamingConvention,
    ServiceType
)

class MyStack(StandardizedStack):
    def __init__(self, scope: cdk.App, construct_id: str, **kwargs):
        super().__init__(
            scope,
            construct_id,
            project="my-app",
            environment="prod",
            company="your-company", 
            service="messaging",
            **kwargs
        )
        
        # Automatic naming and tagging
        lambda_fn = StandardizedLambda(
            self,
            "Handler",
            identifier="sms-processor",
            naming=self.naming,
            tagging=self.tagging,
            code=_lambda.Code.from_asset("lambda"),
            handler="index.handler"
        )

app = cdk.App()
MyStack(app, "MyStack")
app.synth()
```

### TypeScript Example

```typescript
import * as cdk from 'aws-cdk-lib';
import { StandardizedStack, ServiceType } from '@your-company/aws-cdk-standards';

class MyStack extends StandardizedStack {
  constructor(scope: cdk.App, id: string, props?: cdk.StackProps) {
    super(scope, id, {
      ...props,
      naming: {
        project: 'my-app',
        environment: 'prod',
        company: 'your-company'
      },
      service: ServiceType.MESSAGING
    });

    // Resources automatically get consistent naming and tagging
    const handler = new lambda.Function(this, 'Handler', {
      functionName: this.naming.lambda('sms-processor'),
      // ... other props
    });
  }
}

const app = new cdk.App();
new MyStack(app, 'MyStack');
app.synth();
```

## 🔧 **Direct Utility Usage**

You can also use the naming and tagging utilities directly without the standardized constructs:

### Python
```python
from m3_aws_standards import NamingConvention, TaggingStrategy

# Create utilities
naming = NamingConvention("my-app", "prod", "your-company")
tagging = TaggingStrategy("my-app", "prod", "your-company", "api")

# Generate names
lambda_name = naming.lambda_function("processor")  # my-app-prod-compute-lambda-processor
table_name = naming.dynamo_table("users")          # my-app-prod-storage-table-users

# Apply tags
tagging.apply_to(my_construct)
```

### TypeScript
```typescript
import { NamingConvention, TaggingStrategy } from '@your-company/aws-cdk-standards';

const naming = new NamingConvention({
  project: 'my-app',
  environment: 'prod', 
  company: 'your-company'
});

const lambdaName = naming.lambda('processor');  // my-app-prod-compute-lambda-processor
const tableName = naming.dynamoTable('users'); // my-app-prod-storage-table-users
```

## 🌍 **Environment-Specific Behavior**

The library automatically applies environment-appropriate settings:

### Development
- Lambda Memory: 256MB
- Log Retention: 7 days
- Off-Hours Shutdown: Enabled for compute resources
- Backup: Disabled
- Monitoring: Basic

### Staging  
- Lambda Memory: 512MB
- Log Retention: 14 days
- Off-Hours Shutdown: Disabled
- Backup: Enabled
- Monitoring: Standard

### Production
- Lambda Memory: 1024MB
- Log Retention: 90 days
- Off-Hours Shutdown: Disabled
- Backup: Enabled with deletion protection
- Monitoring: Comprehensive

## 📊 **Generated Tags**

Every resource automatically gets these tags:

```json
{
  "Project": "my-app",
  "Environment": "prod",
  "Company": "your-company", 
  "Service": "messaging",
  "CreatedBy": "cdk",
  "ManagedBy": "infrastructure-team",
  "CostCenter": "engineering-prod",
  "OffHoursShutdown": "disabled",
  "BackupEnabled": "true",
  "MonitoringLevel": "comprehensive",
  "DataRetention": "90-days"
}
```

## 🔄 **Migration from Existing Infrastructure**

To migrate your SMS Bot infrastructure to use this library:

1. **Install the library** in your project
2. **Replace manual naming** with utility calls:
   ```python
   # Before
   function_name = "smsbot-prod-messaging-sms-handler"
   
   # After  
   function_name = naming.lambda_function("sms-handler", ServiceType.MESSAGING)
   ```
3. **Replace manual tagging** with utility calls:
   ```python
   # Before
   Tags.of(construct).add("Project", "SMSBot")
   Tags.of(construct).add("Environment", "prod")
   # ... many more tags
   
   # After
   tagging.apply_to(construct)
   ```
4. **Use StandardizedStack** for new stacks

## 🧪 **Testing**

The library includes validation to ensure naming and tagging consistency:

```python
# Naming validation
naming = NamingConvention("my-app!", "prod", "company")  # Raises ValueError

# Tag validation  
all_tags = tagging.get_all_tags()
assert "Project" in all_tags
assert "Environment" in all_tags
```

## 📚 **API Reference**

### NamingConvention Methods
- `lambda_function(identifier, service=ServiceType.COMPUTE)` 
- `dynamo_table(table_name)`
- `sns_topic(topic_name)`
- `sqs_queue(queue_name)`
- `iam_role(role_name, service=ServiceType.SECURITY)`
- `s3_bucket(bucket_name)` (globally unique)
- `api_gateway(api_name)`
- `log_group(service, resource_type)`

### TaggingStrategy Methods
- `get_mandatory_tags()` - Core identification tags
- `get_environment_tags()` - Environment-specific tags
- `get_service_tags()` - Service-specific tags  
- `get_all_tags()` - All tags combined
- `apply_to(construct)` - Apply tags to a construct
- `create_aspect()` - Create CDK aspect for automatic tagging

## 🤝 **Contributing**

1. Follow the established patterns from the SMS Bot infrastructure
2. Add tests for new functionality
3. Update documentation
4. Ensure both Python and TypeScript versions stay in sync

## 📞 **Support**

- Check the examples in the `examples/` directory
- Review the SMS Bot infrastructure for reference patterns
- Contact the infrastructure team for questions

---

This library brings the proven naming and tagging patterns from your SMS Bot infrastructure to all your CDK applications, ensuring consistency across your entire AWS estate.
