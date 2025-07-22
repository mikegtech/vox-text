#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { InfrastructureStack } from '../lib/infrastructure-stack';
import { getEnvironmentConfig, validateEnvironmentConfig } from '../config/environments';
import { NamingConvention } from '../lib/naming-convention';

const app = new cdk.App();

// Get environment from context or default to 'dev'
const environment = app.node.tryGetContext('environment') || 'dev';
const company = app.node.tryGetContext('company') || 'your-company';
const tenant = app.node.tryGetContext('tenant');

// Get environment configuration
const config = getEnvironmentConfig(environment);

// Validate configuration
validateEnvironmentConfig(config);

// Create naming convention for stack name
const naming = new NamingConvention({
  project: 'smsbot',
  environment: environment,
  region: config.region
});

// Create the infrastructure stack
new InfrastructureStack(app, naming.stack(), {
  environment: environment,
  config: config,
  company: company,
  tenant: tenant,
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: config.region
  },
  description: `SMS Bot infrastructure for ${environment} environment`,
  tags: {
    Project: 'SMSBot',
    Environment: environment,
    Company: company,
    CreatedBy: 'cdk'
  }
});

// Add stack-level tags
cdk.Tags.of(app).add('Project', 'SMSBot');
cdk.Tags.of(app).add('ManagedBy', 'cdk');

console.log(`✅ SMS Bot infrastructure stack created for ${environment} environment`);
console.log(`📋 Stack name: ${naming.stack()}`);
console.log(`🏢 Company: ${company}`);
console.log(`🏷️  Tenant: ${tenant || `${environment}-tenant`}`);
console.log(`🌍 Region: ${config.region}`);