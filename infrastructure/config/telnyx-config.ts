/**
 * Telnyx-specific configuration for SMS Bot infrastructure
 */

export interface TelnyxConfig {
  // Telnyx IP CIDR blocks for API Gateway resource policy
  ipCidrBlocks: string[];
  
  // Webhook configuration
  webhookConfig: {
    signatureHeader: string;
    timestampHeader: string;
    maxTimestampAge: number; // seconds
  };
  
  // API Gateway configuration
  apiConfig: {
    throttling: {
      rateLimit: number;
      burstLimit: number;
    };
    cors: {
      allowOrigins: string[];
      allowMethods: string[];
      allowHeaders: string[];
    };
  };
}

// ===========================================
// TELNYX CONFIGURATION
// ===========================================

export const telnyxConfig: TelnyxConfig = {
  // Telnyx IP CIDR blocks (updated as of 2024)
  // Note: These should be verified with Telnyx documentation
  ipCidrBlocks: [
    '185.86.151.0/24',    // Telnyx primary block
    '185.86.150.0/24',    // Telnyx secondary block
    '147.75.0.0/16',      // Telnyx infrastructure
    '139.178.0.0/16',     // Telnyx infrastructure
    '136.144.0.0/16',     // Telnyx infrastructure
    '192.168.1.0/24'      // Add your development IP for testing
  ],
  
  webhookConfig: {
    signatureHeader: 'telnyx-signature-ed25519',
    timestampHeader: 'telnyx-timestamp',
    maxTimestampAge: 300 // 5 minutes
  },
  
  apiConfig: {
    throttling: {
      rateLimit: 100,   // requests per second
      burstLimit: 200   // burst capacity
    },
    cors: {
      allowOrigins: ['*'], // Restrict in production
      allowMethods: ['POST', 'GET', 'OPTIONS'],
      allowHeaders: [
        'Content-Type',
        'telnyx-signature-ed25519',
        'telnyx-timestamp',
        'Authorization'
      ]
    }
  }
};

// ===========================================
// HELPER FUNCTIONS
// ===========================================

/**
 * Get Telnyx IP CIDR blocks for resource policy
 */
export function getTelnyxCidrBlocks(): string[] {
  return telnyxConfig.ipCidrBlocks;
}

/**
 * Get webhook signature validation configuration
 */
export function getWebhookConfig() {
  return telnyxConfig.webhookConfig;
}

/**
 * Get API Gateway throttling configuration
 */
export function getApiThrottlingConfig() {
  return telnyxConfig.apiConfig.throttling;
}

/**
 * Validate Telnyx webhook signature headers
 */
export function validateWebhookHeaders(headers: { [key: string]: string }): boolean {
  const config = telnyxConfig.webhookConfig;
  
  return !!(
    headers[config.signatureHeader] &&
    headers[config.timestampHeader]
  );
}

// ===========================================
// ENVIRONMENT-SPECIFIC OVERRIDES
// ===========================================

/**
 * Get environment-specific Telnyx configuration
 */
export function getTelnyxConfigForEnvironment(environment: string): TelnyxConfig {
  const baseConfig = { ...telnyxConfig };
  
  switch (environment) {
    case 'dev':
      // Development: More permissive settings
      baseConfig.apiConfig.throttling = {
        rateLimit: 10,
        burstLimit: 20
      };
      // Add local development IPs
      baseConfig.ipCidrBlocks.push('127.0.0.1/32', '0.0.0.0/0'); // Allow all for dev
      break;
      
    case 'staging':
      // Staging: Moderate restrictions
      baseConfig.apiConfig.throttling = {
        rateLimit: 50,
        burstLimit: 100
      };
      break;
      
    case 'prod':
      // Production: Strict settings (use defaults)
      // Remove development IPs
      baseConfig.ipCidrBlocks = baseConfig.ipCidrBlocks.filter(
        cidr => !cidr.includes('192.168.1.0/24')
      );
      break;
  }
  
  return baseConfig;
}

// ===========================================
// CONSTANTS
// ===========================================

export const TELNYX_CONSTANTS = {
  // Webhook event types
  EVENT_TYPES: {
    MESSAGE_RECEIVED: 'message.received',
    MESSAGE_SENT: 'message.sent',
    MESSAGE_DELIVERED: 'message.delivered',
    MESSAGE_FAILED: 'message.failed'
  },
  
  // Message directions
  MESSAGE_DIRECTIONS: {
    INBOUND: 'inbound',
    OUTBOUND: 'outbound'
  },
  
  // Message types
  MESSAGE_TYPES: {
    SMS: 'SMS',
    MMS: 'MMS'
  }
} as const;
