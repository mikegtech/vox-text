#!/usr/bin/env node
/**
 * Example TypeScript CDK stack using the shared standards library
 */
import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import { Construct } from 'constructs';

// Import your shared standards (when published)
// import { 
//   StandardizedStack, 
//   NamingConvention, 
//   TaggingStrategy, 
//   ServiceType 
// } from '@your-company/aws-cdk-standards';

// For now, assuming you copy the utilities locally:
import { NamingConvention, ServiceType } from '../lib/naming-convention';
import { TaggingStrategy } from '../lib/tagging-strategy';
import { StandardizedStack } from '../lib/constructs';

class MyTypeScriptStack extends StandardizedStack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, {
      ...props,
      naming: {
        project: 'my-typescript-app',
        environment: 'dev',
        company: 'your-company',
        tenant: 'client-b'
      },
      service: ServiceType.API,
      owner: 'frontend-team'
    });

    // Resources are automatically named and tagged through the base class
    
    // Create Lambda function
    const apiHandler = new lambda.Function(this, 'ApiHandler', {
      functionName: this.naming.lambda('api-handler', ServiceType.API),
      runtime: lambda.Runtime.NODEJS_18_X,
      code: lambda.Code.fromAsset('lambda'),
      handler: 'index.handler'
    });

    // Create DynamoDB table  
    const usersTable = new dynamodb.Table(this, 'UsersTable', {
      tableName: this.naming.dynamoTable('users'),
      partitionKey: {
        name: 'user_id',
        type: dynamodb.AttributeType.STRING
      }
    });

    // Tags are automatically applied via the StandardizedStack aspect
  }
}

// Example using utilities directly
class DirectUtilityStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Create naming and tagging utilities
    const naming = new NamingConvention({
      project: 'analytics-platform',
      environment: 'prod',
      company: 'your-company'
    });

    const tagging = new TaggingStrategy({
      project: 'analytics-platform',
      environment: 'prod', 
      company: 'your-company',
      service: ServiceType.COMPUTE,
      owner: 'data-team',
      costCenter: 'analytics-prod'
    });

    // Use naming convention
    const processorName = naming.lambda('data-processor');
    const metricsTableName = naming.dynamoTable('metrics');

    // Create resources with generated names
    const dataProcessor = new lambda.Function(this, 'DataProcessor', {
      functionName: processorName,
      runtime: lambda.Runtime.PYTHON_3_11,
      code: lambda.Code.fromAsset('lambda'),
      handler: 'processor.handler'
    });

    const metricsTable = new dynamodb.Table(this, 'MetricsTable', {
      tableName: metricsTableName,
      partitionKey: {
        name: 'metric_id',
        type: dynamodb.AttributeType.STRING
      }
    });

    // Apply tags manually
    tagging.applyTo(dataProcessor);
    tagging.applyTo(metricsTable);

    // Or apply to entire stack
    cdk.Aspects.of(this).add(tagging.createAspect());
  }
}

// Create app and stacks
const app = new cdk.App();

new MyTypeScriptStack(app, 'MyTypeScriptStack');
new DirectUtilityStack(app, 'DirectUtilityStack');

app.synth();
