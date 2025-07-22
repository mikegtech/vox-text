/**
 * Environment-specific configuration for SMS Bot infrastructure
 */

export interface EnvironmentConfig {
  environment: string;
  region: string;
  company: string;
  tenant: string;
  smsConfig: {
    monthlySpendLimit: number;
    defaultSmsType: 'Promotional' | 'Transactional';
    deliveryStatusSamplingRate: number;
    defaultSenderId?: string;
  };
  lambdaConfig: {
    timeout: number;
    memorySize: number;
    reservedConcurrency?: number;
  };
  dynamoConfig: {
    pointInTimeRecovery: boolean;
    deletionProtection: boolean;
  };
  monitoringConfig: {
    logRetentionDays: number;
    enableDetailedMonitoring: boolean;
    createAlarms: boolean;
  };
  tags: {
    [key: string]: string;
  };
}

// ===========================================
// DEVELOPMENT ENVIRONMENT
// ===========================================

export const developmentConfig: EnvironmentConfig = {
  environment: 'dev',
  region: 'us-east-1',
  company: 'your-company',
  tenant: 'dev-tenant',
  smsConfig: {
    monthlySpendLimit: 10, // $10 for development
    defaultSmsType: 'Transactional',
    deliveryStatusSamplingRate: 100,
    defaultSenderId: 'DEVBOT'
  },
  lambdaConfig: {
    timeout: 30,
    memorySize: 256,
    // No reserved concurrency for dev
  },
  dynamoConfig: {
    pointInTimeRecovery: false, // Cost optimization for dev
    deletionProtection: false
  },
  monitoringConfig: {
    logRetentionDays: 7, // Short retention for dev
    enableDetailedMonitoring: false,
    createAlarms: false
  },
  tags: {
    Environment: 'Development',
    CostCenter: 'engineering-dev'
  }
};

// ===========================================
// STAGING ENVIRONMENT
// ===========================================

export const stagingConfig: EnvironmentConfig = {
  environment: 'staging',
  region: 'us-east-1',
  company: 'your-company',
  tenant: 'staging-tenant',
  smsConfig: {
    monthlySpendLimit: 50, // $50 for staging
    defaultSmsType: 'Transactional',
    deliveryStatusSamplingRate: 100,
    defaultSenderId: 'STGBOT'
  },
  lambdaConfig: {
    timeout: 30,
    memorySize: 512,
    reservedConcurrency: 10 // Limited concurrency for staging
  },
  dynamoConfig: {
    pointInTimeRecovery: true,
    deletionProtection: false
  },
  monitoringConfig: {
    logRetentionDays: 14,
    enableDetailedMonitoring: true,
    createAlarms: true
  },
  tags: {
    Environment: 'Staging',
    CostCenter: 'engineering-staging',
    BackupRequired: 'true'
  }
};

// ===========================================
// PRODUCTION ENVIRONMENT
// ===========================================

export const productionConfig: EnvironmentConfig = {
  environment: 'prod',
  region: 'us-east-1',
  company: 'your-company',
  tenant: 'prod-tenant',
  smsConfig: {
    monthlySpendLimit: 1000, // $1000 for production
    defaultSmsType: 'Transactional',
    deliveryStatusSamplingRate: 100,
    defaultSenderId: 'AIBOT'
  },
  lambdaConfig: {
    timeout: 30,
    memorySize: 1024,
    reservedConcurrency: 100 // Higher concurrency for production
  },
  dynamoConfig: {
    pointInTimeRecovery: true,
    deletionProtection: true // Protect production data
  },
  monitoringConfig: {
    logRetentionDays: 90, // Longer retention for production
    enableDetailedMonitoring: true,
    createAlarms: true
  },
  tags: {
    Environment: 'Production',
    CostCenter: 'engineering-prod',
    BackupRequired: 'true',
    Compliance: 'required',
    DataClassification: 'confidential'
  }
};

// ===========================================
// CONFIGURATION FACTORY
// ===========================================

export function getEnvironmentConfig(environment: string): EnvironmentConfig {
  switch (environment.toLowerCase()) {
    case 'dev':
    case 'development':
      return developmentConfig;
    case 'staging':
    case 'stage':
      return stagingConfig;
    case 'prod':
    case 'production':
      return productionConfig;
    default:
      throw new Error(`Unknown environment: ${environment}. Supported: dev, staging, prod`);
  }
}

// ===========================================
// VALIDATION
// ===========================================

export function validateEnvironmentConfig(config: EnvironmentConfig): void {
  // Validate SMS spend limits
  if (config.smsConfig.monthlySpendLimit <= 0) {
    throw new Error('SMS monthly spend limit must be greater than 0');
  }

  // Validate Lambda configuration
  if (config.lambdaConfig.timeout < 1 || config.lambdaConfig.timeout > 900) {
    throw new Error('Lambda timeout must be between 1 and 900 seconds');
  }

  if (config.lambdaConfig.memorySize < 128 || config.lambdaConfig.memorySize > 10240) {
    throw new Error('Lambda memory size must be between 128 and 10240 MB');
  }

  // Validate log retention
  const validRetentionDays = [1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653];
  if (!validRetentionDays.includes(config.monitoringConfig.logRetentionDays)) {
    throw new Error(`Invalid log retention days: ${config.monitoringConfig.logRetentionDays}`);
  }

  console.log(`✅ Environment configuration validated for: ${config.environment}`);
}

// ===========================================
// HELPER FUNCTIONS
// ===========================================

/**
 * Get all available environments
 */
export function getAvailableEnvironments(): string[] {
  return ['dev', 'staging', 'prod'];
}

/**
 * Check if environment is production
 */
export function isProduction(environment: string): boolean {
  return environment.toLowerCase() === 'prod' || environment.toLowerCase() === 'production';
}

/**
 * Get environment-specific resource removal policy
 */
export function getRemovalPolicy(environment: string): 'DESTROY' | 'RETAIN' | 'SNAPSHOT' {
  if (isProduction(environment)) {
    return 'RETAIN'; // Protect production resources
  }
  return 'DESTROY'; // Allow cleanup for dev/staging
}
