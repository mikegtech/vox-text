/**
 * AWS Resource Tagging Strategy Implementation
 * 
 * Provides standardized tagging for all AWS resources in the SMS Bot project.
 * Integrates with naming convention and environment configuration.
 */

import { Tags } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import { EnvironmentConfig } from '../config/environments';

// ===========================================
// TAG INTERFACES AND TYPES
// ===========================================

export interface MandatoryTags {
  Project: string;
  Company: string;
  Tenant: string;
  Environment: string;
  Service: string;
  Owner: string;
  CostCenter: string;
  CreatedBy: string;
  ManagedBy: string;
  OffHoursShutdown: 'enabled' | 'disabled';
}

export interface OperationalTags {
  Application?: string;
  Component?: string;
  Version?: string;
  DeploymentId?: string;
  LastModified?: string;
}

export interface SecurityTags {
  DataClassification: 'public' | 'internal' | 'confidential' | 'restricted';
  Compliance?: 'required' | 'not-required';
  BackupRequired: 'true' | 'false';
  EncryptionRequired?: 'true' | 'false';
}

export interface CostManagementTags {
  BillingCode?: string;
  BusinessUnit?: string;
  CostAllocation?: 'development' | 'production' | 'shared';
  Budget?: string;
}

export interface AllTags extends 
  MandatoryTags, 
  Partial<OperationalTags>, 
  Partial<SecurityTags>, 
  Partial<CostManagementTags> {
  [key: string]: string | undefined;
}

// ===========================================
// SERVICE CATEGORIES
// ===========================================

export const SERVICES = {
  MESSAGING: 'messaging',
  COMPUTE: 'compute',
  STORAGE: 'storage',
  MONITORING: 'monitoring',
  SECURITY: 'security',
  NETWORK: 'network'
} as const;

export type ServiceType = typeof SERVICES[keyof typeof SERVICES];

// ===========================================
// TAGGING STRATEGY CLASS
// ===========================================

export class TaggingStrategy {
  private readonly environment: string;
  private readonly config: EnvironmentConfig;
  private readonly company: string;
  private readonly tenant: string;
  private readonly baseTags: Omit<MandatoryTags, 'Service' | 'OffHoursShutdown'>;

  constructor(
    environment: string, 
    config: EnvironmentConfig, 
    company: string = 'your-company',
    tenant?: string
  ) {
    this.environment = environment;
    this.config = config;
    this.company = company;
    this.tenant = tenant || this.getDefaultTenant();
    this.baseTags = this.createBaseTags();
  }

  // ===========================================
  // BASE TAG CREATION
  // ===========================================

  private createBaseTags(): Omit<MandatoryTags, 'Service' | 'OffHoursShutdown'> {
    return {
      Project: 'SMSBot',
      Company: this.company,
      Tenant: this.tenant,
      Environment: this.environment,
      Owner: 'infrastructure-team',
      CostCenter: this.getCostCenter(),
      CreatedBy: 'cdk',
      ManagedBy: 'infrastructure-team'
    };
  }

  private getDefaultTenant(): string {
    return `${this.environment}-tenant`;
  }

  private getCostCenter(): string {
    return `engineering-${this.environment}`;
  }

  // ===========================================
  // SERVICE-SPECIFIC TAG GENERATORS
  // ===========================================

  /**
   * Generate tags for messaging services (SNS, SQS)
   */
  messagingServiceTags(component: string, additionalTags: Partial<AllTags> = {}): AllTags {
    const baseTags: AllTags = {
      ...this.baseTags,
      Service: SERVICES.MESSAGING,
      OffHoursShutdown: 'disabled', // Messaging services should stay up
      Component: component,
      Application: 'sms-bot',
      DataClassification: this.getDataClassification(),
      BackupRequired: 'false', // SNS/SQS don't need backup
      ...this.getEnvironmentSpecificTags()
    };

    return { ...baseTags, ...additionalTags };
  }

  /**
   * Generate tags for compute services (Lambda)
   */
  computeServiceTags(component: string, additionalTags: Partial<AllTags> = {}): AllTags {
    const baseTags: AllTags = {
      ...this.baseTags,
      Service: SERVICES.COMPUTE,
      OffHoursShutdown: this.getOffHoursShutdown('compute'),
      Component: component,
      Application: 'sms-bot',
      DataClassification: this.getDataClassification(),
      BackupRequired: 'false', // Lambda functions don't need backup
      ...this.getEnvironmentSpecificTags()
    };

    return { ...baseTags, ...additionalTags };
  }

  /**
   * Generate tags for storage services (DynamoDB, S3)
   */
  storageServiceTags(component: string, additionalTags: Partial<AllTags> = {}): AllTags {
    const baseTags: AllTags = {
      ...this.baseTags,
      Service: SERVICES.STORAGE,
      OffHoursShutdown: 'disabled', // Storage should always be available
      Component: component,
      Application: 'sms-bot',
      DataClassification: this.getDataClassification(),
      BackupRequired: this.getBackupRequired(),
      EncryptionRequired: 'true',
      ...this.getEnvironmentSpecificTags()
    };

    return { ...baseTags, ...additionalTags };
  }

  /**
   * Generate tags for monitoring services (CloudWatch)
   */
  monitoringServiceTags(component: string, additionalTags: Partial<AllTags> = {}): AllTags {
    const baseTags: AllTags = {
      ...this.baseTags,
      Service: SERVICES.MONITORING,
      OffHoursShutdown: 'disabled', // Monitoring should always be on
      Component: component,
      Application: 'sms-bot',
      DataClassification: 'internal',
      BackupRequired: 'false',
      ...this.getEnvironmentSpecificTags()
    };

    return { ...baseTags, ...additionalTags };
  }

  /**
   * Generate tags for security services (IAM)
   */
  securityServiceTags(component: string, additionalTags: Partial<AllTags> = {}): AllTags {
    const baseTags: AllTags = {
      ...this.baseTags,
      Service: SERVICES.SECURITY,
      OffHoursShutdown: 'disabled', // Security services must always be on
      Component: component,
      Application: 'sms-bot',
      DataClassification: 'confidential',
      BackupRequired: 'false',
      ...this.getEnvironmentSpecificTags()
    };

    return { ...baseTags, ...additionalTags };
  }

  // ===========================================
  // ENVIRONMENT-SPECIFIC HELPERS
  // ===========================================

  private getDataClassification(): SecurityTags['DataClassification'] {
    switch (this.environment) {
      case 'prod':
        return 'confidential';
      case 'staging':
        return 'internal';
      case 'dev':
        return 'internal';
      default:
        return 'internal';
    }
  }

  private getBackupRequired(): SecurityTags['BackupRequired'] {
    return this.environment === 'prod' || this.environment === 'staging' ? 'true' : 'false';
  }

  private getOffHoursShutdown(serviceType: string): MandatoryTags['OffHoursShutdown'] {
    // Only enable off-hours shutdown for compute resources in dev environment
    if (this.environment === 'dev' && serviceType === 'compute') {
      return 'enabled';
    }
    return 'disabled';
  }

  private getEnvironmentSpecificTags(): Partial<AllTags> {
    const envTags: Partial<AllTags> = {};

    // Add environment-specific tags from config (excluding Environment to avoid conflict)
    Object.entries(this.config.tags).forEach(([key, value]) => {
      if (key !== 'Environment') { // Skip Environment tag to avoid conflict with mandatory tag
        envTags[key] = value;
      }
    });

    // Add compliance tags for prod/staging
    if (this.environment === 'prod' || this.environment === 'staging') {
      envTags.Compliance = 'required';
    }

    return envTags;
  }

  // ===========================================
  // CDK INTEGRATION METHODS
  // ===========================================

  /**
   * Apply tags to a CDK construct
   */
  applyTags(construct: Construct, service: ServiceType, component: string, additionalTags: Partial<AllTags> = {}): void {
    let tags: AllTags;

    switch (service) {
      case SERVICES.MESSAGING:
        tags = this.messagingServiceTags(component, additionalTags);
        break;
      case SERVICES.COMPUTE:
        tags = this.computeServiceTags(component, additionalTags);
        break;
      case SERVICES.STORAGE:
        tags = this.storageServiceTags(component, additionalTags);
        break;
      case SERVICES.MONITORING:
        tags = this.monitoringServiceTags(component, additionalTags);
        break;
      case SERVICES.SECURITY:
        tags = this.securityServiceTags(component, additionalTags);
        break;
      default:
        throw new Error(`Unknown service type: ${service}`);
    }

    // Apply tags to the construct, filtering out undefined values
    Object.entries(tags).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value.trim() !== '') {
        Tags.of(construct).add(key, value);
      }
    });
  }

  /**
   * Apply stack-level tags (inherited by all resources)
   */
  applyStackTags(construct: Construct): void {
    const stackTags: { [key: string]: string } = {
      ...this.baseTags,
      Application: 'sms-bot',
      Version: process.env.APP_VERSION || 'latest',
      DeploymentId: process.env.DEPLOYMENT_ID || 'manual',
      LastModified: new Date().toISOString()
    };

    Object.entries(stackTags).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value.trim() !== '') {
        Tags.of(construct).add(key, value);
      }
    });
  }

  // ===========================================
  // VALIDATION METHODS
  // ===========================================

  /**
   * Validate that all mandatory tags are present
   */
  validateMandatoryTags(tags: { [key: string]: string }): boolean {
    const mandatoryTagKeys = [
      'Project', 'Company', 'Tenant', 'Environment', 'Service', 
      'Owner', 'CostCenter', 'CreatedBy', 'ManagedBy', 'OffHoursShutdown'
    ];
    
    return mandatoryTagKeys.every(key => 
      tags.hasOwnProperty(key) && tags[key].trim() !== ''
    );
  }

  /**
   * Validate tag values against constraints
   */
  validateTagValues(tags: { [key: string]: string }): string[] {
    const errors: string[] = [];
    const constraints: { [key: string]: string[] } = {
      'Environment': ['dev', 'staging', 'prod'],
      'Service': Object.values(SERVICES),
      'CreatedBy': ['cdk', 'manual', 'terraform'],
      'OffHoursShutdown': ['enabled', 'disabled'],
      'DataClassification': ['public', 'internal', 'confidential', 'restricted'],
      'BackupRequired': ['true', 'false'],
      'Compliance': ['required', 'not-required']
    };

    Object.entries(constraints).forEach(([tagKey, validValues]) => {
      if (tags[tagKey] && !validValues.includes(tags[tagKey])) {
        errors.push(`Invalid value '${tags[tagKey]}' for tag '${tagKey}'. Valid values: ${validValues.join(', ')}`);
      }
    });

    return errors;
  }

  // ===========================================
  // UTILITY METHODS
  // ===========================================

  /**
   * Get cost allocation tags for billing
   */
  getCostAllocationTags(): CostManagementTags {
    return {
      BillingCode: `SMS-BOT-${this.tenant.toUpperCase()}-${this.environment.toUpperCase()}`,
      BusinessUnit: 'engineering',
      CostAllocation: this.environment === 'prod' ? 'production' : 'development',
      Budget: `sms-bot-${this.environment}`
    };
  }

  /**
   * Get compliance tags for governance
   */
  getComplianceTags(): Partial<SecurityTags> {
    if (this.environment === 'prod') {
      return {
        Compliance: 'required',
        DataClassification: 'confidential',
        EncryptionRequired: 'true',
        BackupRequired: 'true'
      };
    }
    return {
      Compliance: 'not-required',
      DataClassification: 'internal'
    };
  }

  /**
   * Check if resource should be shut down during off-hours
   */
  shouldShutdownOffHours(serviceType: ServiceType): boolean {
    return this.environment === 'dev' && serviceType === SERVICES.COMPUTE;
  }
}

// ===========================================
// FACTORY FUNCTIONS
// ===========================================

/**
 * Create tagging strategy for specific environment
 */
export function createTaggingStrategy(
  environment: string, 
  config: EnvironmentConfig, 
  company: string = 'your-company',
  tenant?: string
): TaggingStrategy {
  return new TaggingStrategy(environment, config, company, tenant);
}

// ===========================================
// CONSTANTS AND EXPORTS
// ===========================================

export const TAG_CONSTRAINTS = {
  MAX_KEY_LENGTH: 128,
  MAX_VALUE_LENGTH: 256,
  MAX_TAGS_PER_RESOURCE: 50,
  ALLOWED_CHARACTERS: /^[a-zA-Z0-9\s._\-:/=+@]*$/
};

export const MANDATORY_TAG_KEYS = [
  'Project',
  'Company',
  'Tenant',
  'Environment',
  'Service',
  'Owner',
  'CostCenter',
  'CreatedBy',
  'ManagedBy',
  'OffHoursShutdown'
];
