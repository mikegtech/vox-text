/**
 * AWS Resource Naming Convention Utility
 * 
 * Provides standardized naming for all AWS resources in the SMS Bot project.
 * Pattern: {project}-{environment}-{service}-{resource-type}-{identifier}
 */

export interface NamingConfig {
  project: string;
  environment: string;
  region?: string;
  accountId?: string;
}

export class NamingConvention {
  private readonly project: string;
  private readonly environment: string;
  private readonly region?: string;
  private readonly accountId?: string;

  constructor(config: NamingConfig) {
    this.project = config.project.toLowerCase();
    this.environment = config.environment.toLowerCase();
    this.region = config.region;
    this.accountId = config.accountId;
  }

  // ===========================================
  // IAM RESOURCES
  // ===========================================

  /**
   * Generate IAM role name
   * Pattern: {project}-{env}-{service}-role-{purpose}
   */
  iamRole(service: string, purpose: string): string {
    return `${this.project}-${this.environment}-${service}-role-${purpose}`;
  }

  /**
   * Generate IAM policy name
   * Pattern: {project}-{env}-{service}-policy-{purpose}
   */
  iamPolicy(service: string, purpose: string): string {
    return `${this.project}-${this.environment}-${service}-policy-${purpose}`;
  }

  // ===========================================
  // COMPUTE RESOURCES
  // ===========================================

  /**
   * Generate Lambda function name
   * Pattern: {project}-{env}-{service}-{purpose}
   */
  lambdaFunction(service: string, purpose: string): string {
    const name = `${this.project}-${this.environment}-${service}-${purpose}`;
    // Ensure Lambda naming limits (64 characters)
    return name.length > 64 ? name.substring(0, 64) : name;
  }

  // ===========================================
  // STORAGE RESOURCES
  // ===========================================

  /**
   * Generate DynamoDB table name
   * Pattern: {project}-{env}-{dataType}
   */
  dynamoTable(dataType: string): string {
    return `${this.project}-${this.environment}-${dataType}`;
  }

  /**
   * Generate S3 bucket name (globally unique)
   * Pattern: {project}-{env}-{purpose}-{accountId}-{region}
   */
  s3Bucket(purpose: string): string {
    if (!this.accountId || !this.region) {
      throw new Error('Account ID and region required for S3 bucket naming');
    }
    return `${this.project}-${this.environment}-${purpose}-${this.accountId}-${this.region}`;
  }

  // ===========================================
  // MESSAGING RESOURCES
  // ===========================================

  /**
   * Generate SNS topic name
   * Pattern: {project}-{env}-{messageType}
   */
  snsTopic(messageType: string): string {
    return `${this.project}-${this.environment}-${messageType}`;
  }

  /**
   * Generate SQS queue name
   * Pattern: {project}-{env}-{queueType}
   */
  sqsQueue(queueType: string): string {
    return `${this.project}-${this.environment}-${queueType}`;
  }

  // ===========================================
  // MONITORING RESOURCES
  // ===========================================

  /**
   * Generate CloudWatch log group name
   * Pattern: /aws/{service}/{project}-{env}-{component}
   */
  logGroup(awsService: string, component: string): string {
    return `/aws/${awsService}/${this.project}-${this.environment}-${component}`;
  }

  /**
   * Generate CloudWatch dashboard name
   * Pattern: {project}-{env}-{purpose}
   */
  dashboard(purpose: string): string {
    return `${this.project}-${this.environment}-${purpose}`;
  }

  /**
   * Generate CloudWatch alarm name
   * Pattern: {project}-{env}-{service}-{metric}-{condition}
   */
  alarm(service: string, metric: string, condition: string): string {
    return `${this.project}-${this.environment}-${service}-${metric}-${condition}`;
  }

  // ===========================================
  // NETWORK RESOURCES
  // ===========================================

  /**
   * Generate VPC name
   * Pattern: {project}-{env}-vpc
   */
  vpc(): string {
    return `${this.project}-${this.environment}-vpc`;
  }

  /**
   * Generate subnet name
   * Pattern: {project}-{env}-{subnetType}-{az}
   */
  subnet(subnetType: string, availabilityZone: string): string {
    return `${this.project}-${this.environment}-${subnetType}-${availabilityZone}`;
  }

  // ===========================================
  // SECURITY RESOURCES
  // ===========================================

  /**
   * Generate security group name
   * Pattern: {project}-{env}-{service}-sg
   */
  securityGroup(service: string): string {
    return `${this.project}-${this.environment}-${service}-sg`;
  }

  // ===========================================
  // TAGGING
  // ===========================================

  /**
   * Generate standard tags for all resources
   */
  standardTags(service: string, additionalTags: { [key: string]: string } = {}): { [key: string]: string } {
    return {
      Project: 'SMSBot',
      Environment: this.environment,
      Service: service,
      Owner: 'infrastructure-team',
      CostCenter: 'engineering',
      CreatedBy: 'cdk',
      ManagedBy: 'infrastructure-team',
      ...additionalTags
    };
  }

  // ===========================================
  // STACK NAMING
  // ===========================================

  /**
   * Generate CDK stack name
   * Pattern: {project}-{env}-{stackType}
   */
  stack(stackType: string = 'infrastructure'): string {
    return `${this.project}-${this.environment}-${stackType}`;
  }

  // ===========================================
  // VALIDATION
  // ===========================================

  /**
   * Validate resource name against AWS constraints
   */
  validateName(name: string, resourceType: string): boolean {
    const constraints: { [key: string]: { maxLength: number; pattern: RegExp } } = {
      'lambda': { maxLength: 64, pattern: /^[a-zA-Z0-9-_]+$/ },
      'dynamodb': { maxLength: 255, pattern: /^[a-zA-Z0-9._-]+$/ },
      'sns': { maxLength: 256, pattern: /^[a-zA-Z0-9._-]+$/ },
      'iam-role': { maxLength: 64, pattern: /^[a-zA-Z0-9+=,.@_-]+$/ },
      's3': { maxLength: 63, pattern: /^[a-z0-9.-]+$/ }
    };

    const constraint = constraints[resourceType];
    if (!constraint) {
      console.warn(`No validation rules for resource type: ${resourceType}`);
      return true;
    }

    if (name.length > constraint.maxLength) {
      throw new Error(`${resourceType} name '${name}' exceeds maximum length of ${constraint.maxLength}`);
    }

    if (!constraint.pattern.test(name)) {
      throw new Error(`${resourceType} name '${name}' contains invalid characters`);
    }

    return true;
  }

  // ===========================================
  // UTILITY METHODS
  // ===========================================

  /**
   * Get current configuration
   */
  getConfig(): NamingConfig {
    return {
      project: this.project,
      environment: this.environment,
      region: this.region,
      accountId: this.accountId
    };
  }

  /**
   * Generate resource identifier with timestamp (for unique resources)
   */
  withTimestamp(baseName: string): string {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    return `${baseName}-${timestamp}`;
  }
}

// ===========================================
// ENVIRONMENT CONSTANTS
// ===========================================

export const ENVIRONMENTS = {
  DEVELOPMENT: 'dev',
  STAGING: 'staging',
  PRODUCTION: 'prod'
} as const;

export const SERVICES = {
  MESSAGING: 'messaging',
  COMPUTE: 'compute',
  STORAGE: 'storage',
  MONITORING: 'monitoring',
  SECURITY: 'security',
  NETWORK: 'network'
} as const;

// ===========================================
// FACTORY FUNCTIONS
// ===========================================

/**
 * Create naming convention instance for development environment
 */
export function createDevNaming(region?: string, accountId?: string): NamingConvention {
  return new NamingConvention({
    project: 'smsbot',
    environment: ENVIRONMENTS.DEVELOPMENT,
    region,
    accountId
  });
}

/**
 * Create naming convention instance for staging environment
 */
export function createStagingNaming(region?: string, accountId?: string): NamingConvention {
  return new NamingConvention({
    project: 'smsbot',
    environment: ENVIRONMENTS.STAGING,
    region,
    accountId
  });
}

/**
 * Create naming convention instance for production environment
 */
export function createProdNaming(region?: string, accountId?: string): NamingConvention {
  return new NamingConvention({
    project: 'smsbot',
    environment: ENVIRONMENTS.PRODUCTION,
    region,
    accountId
  });
}
