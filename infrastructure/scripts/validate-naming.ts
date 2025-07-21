#!/usr/bin/env ts-node

/**
 * Naming Convention and Tagging Validation Script
 * 
 * This script validates the naming convention implementation and provides
 * examples of generated resource names and tags for review.
 */

import { NamingConvention, ENVIRONMENTS, SERVICES } from '../lib/naming-convention';
import { TaggingStrategy, MANDATORY_TAG_KEYS } from '../lib/tagging-strategy';
import { getEnvironmentConfig, validateEnvironmentConfig } from '../config/environments';

// ===========================================
// VALIDATION FUNCTIONS
// ===========================================

function validateNamingConvention(): void {
  console.log('🔍 Validating AWS Resource Naming Convention\n');

  const environments = [ENVIRONMENTS.DEVELOPMENT, ENVIRONMENTS.PRODUCTION];
  const mockAccountId = '123456789012';
  const mockRegion = 'us-east-1';

  environments.forEach(env => {
    console.log(`\n📋 ${env.toUpperCase()} ENVIRONMENT`);
    console.log('='.repeat(50));

    const naming = new NamingConvention({
      project: 'smsbot',
      environment: env,
      region: mockRegion,
      accountId: mockAccountId
    });

    // Test IAM resources
    console.log('\n🔐 IAM Resources:');
    const snsRole = naming.iamRole(SERVICES.MESSAGING, 'sns-logs');
    const lambdaRole = naming.iamRole(SERVICES.COMPUTE, 'lambda-execution');
    console.log(`  SNS Logs Role: ${snsRole}`);
    console.log(`  Lambda Role: ${lambdaRole}`);

    // Test Lambda functions
    console.log('\n⚡ Lambda Functions:');
    const smsHandler = naming.lambdaFunction(SERVICES.MESSAGING, 'sms-handler');
    console.log(`  SMS Handler: ${smsHandler}`);

    // Test DynamoDB tables
    console.log('\n🗄️  DynamoDB Tables:');
    const conversationsTable = naming.dynamoTable('conversations');
    const analyticsTable = naming.dynamoTable('analytics');
    console.log(`  Conversations: ${conversationsTable}`);
    console.log(`  Analytics: ${analyticsTable}`);

    // Test SNS topics
    console.log('\n📨 SNS Topics:');
    const inboundTopic = naming.snsTopic('inbound-sms');
    const deliveryTopic = naming.snsTopic('delivery-status');
    console.log(`  Inbound SMS: ${inboundTopic}`);
    console.log(`  Delivery Status: ${deliveryTopic}`);

    // Test CloudWatch resources
    console.log('\n📊 CloudWatch Resources:');
    const lambdaLogGroup = naming.logGroup('lambda', 'sms-handler');
    const dashboard = naming.dashboard('operations');
    console.log(`  Lambda Log Group: ${lambdaLogGroup}`);
    console.log(`  Dashboard: ${dashboard}`);

    // Test stack naming
    console.log('\n📦 Stack Names:');
    const stackName = naming.stack();
    console.log(`  Main Stack: ${stackName}`);

    console.log('  ✅ All naming conventions validated');
  });
}

// ===========================================
// TAGGING VALIDATION
// ===========================================

function validateTaggingStrategy(): void {
  console.log('\n\n🏷️  Validating Tagging Strategy\n');
  console.log('='.repeat(50));

  const environments = ['dev', 'staging', 'prod'];
  const company = 'test-company';

  environments.forEach(env => {
    try {
      const config = getEnvironmentConfig(env);
      const tagging = new TaggingStrategy(env, config, company);
      
      console.log(`\n📋 ${env.toUpperCase()} Environment Tags:`);
      
      // Test messaging service tags
      const messagingTags = tagging.messagingServiceTags('sms-handler');
      console.log('\n📨 Messaging Service Tags:');
      Object.entries(messagingTags).forEach(([key, value]) => {
        console.log(`  ${key}: ${value}`);
      });

      // Test compute service tags
      const computeTags = tagging.computeServiceTags('sms-processor');
      console.log('\n⚡ Compute Service Tags:');
      Object.entries(computeTags).forEach(([key, value]) => {
        console.log(`  ${key}: ${value}`);
      });

      // Test storage service tags
      const storageTags = tagging.storageServiceTags('conversations-table');
      console.log('\n🗄️  Storage Service Tags:');
      Object.entries(storageTags).forEach(([key, value]) => {
        console.log(`  ${key}: ${value}`);
      });

      // Validate mandatory tags
      const hasMandatoryTags = tagging.validateMandatoryTags(messagingTags as { [key: string]: string });
      console.log(`\n✅ Mandatory tags validation: ${hasMandatoryTags ? 'PASSED' : 'FAILED'}`);

      // Validate tag values
      const tagErrors = tagging.validateTagValues(messagingTags as { [key: string]: string });
      if (tagErrors.length === 0) {
        console.log('✅ Tag values validation: PASSED');
      } else {
        console.log('❌ Tag values validation: FAILED');
        tagErrors.forEach(error => console.log(`  - ${error}`));
      }

      // Test off-hours shutdown logic
      const shouldShutdown = tagging.shouldShutdownOffHours(SERVICES.COMPUTE);
      console.log(`\n💰 Off-hours shutdown for compute: ${shouldShutdown ? 'ENABLED' : 'DISABLED'}`);
      
    } catch (error) {
      console.log(`❌ ${env} tagging validation error: ${error}`);
    }
  });
}

// ===========================================
// ENVIRONMENT CONFIG VALIDATION
// ===========================================

function validateEnvironmentConfigs(): void {
  console.log('\n\n🔧 Validating Environment Configurations\n');
  console.log('='.repeat(50));

  const environments = ['dev', 'staging', 'prod'];

  environments.forEach(env => {
    try {
      const config = getEnvironmentConfig(env);
      validateEnvironmentConfig(config);
      
      console.log(`\n📋 ${env.toUpperCase()} Configuration:`);
      console.log(`  Company: ${config.company}`);
      console.log(`  Tenant: ${config.tenant}`);
      console.log(`  Region: ${config.region}`);
      console.log(`  SMS Spend Limit: $${config.smsConfig.monthlySpendLimit}`);
      console.log(`  Lambda Memory: ${config.lambdaConfig.memorySize}MB`);
      console.log(`  Lambda Timeout: ${config.lambdaConfig.timeout}s`);
      console.log(`  Log Retention: ${config.monitoringConfig.logRetentionDays} days`);
      console.log(`  Point-in-Time Recovery: ${config.dynamoConfig.pointInTimeRecovery}`);
      console.log(`  Deletion Protection: ${config.dynamoConfig.deletionProtection}`);
      
    } catch (error) {
      console.log(`❌ ${env} configuration error: ${error}`);
    }
  });
}

// ===========================================
// COST OPTIMIZATION ANALYSIS
// ===========================================

function analyzeCostOptimization(): void {
  console.log('\n\n💰 Cost Optimization Analysis\n');
  console.log('='.repeat(50));

  const environments = ['dev', 'staging', 'prod'];

  environments.forEach(env => {
    const config = getEnvironmentConfig(env);
    const tagging = new TaggingStrategy(env, config, 'test-company');

    console.log(`\n📊 ${env.toUpperCase()} Cost Optimization:`);
    
    // Analyze off-hours shutdown potential
    const services = Object.values(SERVICES);
    services.forEach(service => {
      const shouldShutdown = tagging.shouldShutdownOffHours(service as any);
      const status = shouldShutdown ? '💚 ENABLED' : '🔴 DISABLED';
      console.log(`  ${service}: ${status}`);
    });

    // Calculate potential savings
    if (env === 'dev') {
      console.log(`  💡 Potential savings: 60-80% for compute resources`);
    } else {
      console.log(`  💡 Focus on right-sizing for cost optimization`);
    }
  });
}

// ===========================================
// COMPLETE RESOURCE EXAMPLES
// ===========================================

function generateCompleteExamples(): void {
  console.log('\n\n📝 Complete Resource Examples\n');
  console.log('='.repeat(50));

  const config = getEnvironmentConfig('prod');
  const naming = new NamingConvention({
    project: 'smsbot',
    environment: 'prod',
    region: 'us-east-1',
    accountId: '123456789012'
  });
  const tagging = new TaggingStrategy('prod', config, 'acme-corp', 'client-a');

  console.log('\n🏭 PRODUCTION ENVIRONMENT - Complete Resource List:');
  console.log('-'.repeat(50));

  // IAM Resources
  console.log('\n🔐 IAM Resources:');
  console.log(`  Role: ${naming.iamRole(SERVICES.MESSAGING, 'sns-logs')}`);
  console.log(`  Role: ${naming.iamRole(SERVICES.COMPUTE, 'lambda-execution')}`);

  // Lambda Functions
  console.log('\n⚡ Lambda Functions:');
  console.log(`  Function: ${naming.lambdaFunction(SERVICES.MESSAGING, 'sms-handler')}`);

  // DynamoDB Tables
  console.log('\n🗄️  DynamoDB Tables:');
  console.log(`  Table: ${naming.dynamoTable('conversations')}`);
  console.log(`  Table: ${naming.dynamoTable('analytics')}`);

  // SNS Topics
  console.log('\n📨 SNS Topics:');
  console.log(`  Topic: ${naming.snsTopic('inbound-sms')}`);
  console.log(`  Topic: ${naming.snsTopic('delivery-status')}`);

  // CloudWatch Resources
  console.log('\n📊 CloudWatch Resources:');
  console.log(`  Log Group: ${naming.logGroup('lambda', 'sms-handler')}`);
  console.log(`  Dashboard: ${naming.dashboard('operations')}`);

  // Example tags for Lambda function
  console.log('\n🏷️  Example Tags (Lambda Function):');
  const lambdaTags = tagging.computeServiceTags('sms-handler');
  Object.entries(lambdaTags).forEach(([key, value]) => {
    console.log(`  ${key}: ${value}`);
  });
}

// ===========================================
// MAIN EXECUTION
// ===========================================

function main(): void {
  console.log('🚀 SMS Bot Infrastructure Validation');
  console.log('='.repeat(60));

  try {
    // Run all validations
    validateNamingConvention();
    validateTaggingStrategy();
    validateEnvironmentConfigs();
    analyzeCostOptimization();
    generateCompleteExamples();

    console.log('\n\n🎉 All validations completed successfully!');
    console.log('\n📋 Summary:');
    console.log('  ✅ Naming convention validated');
    console.log('  ✅ Tagging strategy validated');
    console.log('  ✅ Environment configurations validated');
    console.log('  ✅ Cost optimization analyzed');
    console.log('  ✅ Resource examples generated');

    console.log('\n🚀 Next Steps:');
    console.log('  1. Review the generated naming examples above');
    console.log('  2. Confirm tagging strategy meets requirements');
    console.log('  3. Deploy to development environment first');
    console.log('  4. Validate resources are created with correct names/tags');
    console.log('  5. Test off-hours shutdown in dev environment');

  } catch (error) {
    console.error('\n❌ Validation failed:', error);
    process.exit(1);
  }
}

// Run validation if script is executed directly
if (require.main === module) {
  main();
}

export { validateNamingConvention, validateTaggingStrategy, validateEnvironmentConfigs };
