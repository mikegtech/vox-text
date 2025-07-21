# SMS/Voice Communications Platform PRD

## Overview

This platform provides a cost-optimized, dual-number architecture for handling high-volume AI bot SMS communications and professional business voice/SMS services. The system leverages AWS for economical bot messaging ($0.00645/SMS) while maintaining a local Dallas/Fort Worth presence through Telnyx for voice and business communications.

The solution addresses the need for automated bot interactions at scale while preserving traditional business communication channels, avoiding vendor lock-in, and maintaining flexibility for future voice bot capabilities.

## Core Features

### 1. AI Bot SMS System (AWS)
- **Automated SMS Processing**: Handles incoming commands and triggers bot actions via text
- **Conversation State Management**: Tracks multi-message conversations and context
- **Action Execution**: Processes commands like "ACTION restart server" or "REPORT status"
- **Bulk Messaging**: Supports high-volume outbound campaigns via Amazon Pinpoint
- **Real-time Processing**: Lambda-based architecture for instant responses

### 2. Business Communications (Telnyx)
- **Local DFW Presence**: 214/469/972/817/682 area code for regional credibility
- **Voice Calling**: Inbound/outbound with forwarding to cell phone
- **Professional Voicemail**: With transcription capabilities
- **Business SMS**: Human-handled text conversations
- **Voice-Ready**: Pre-configured for future voice bot implementations

### 3. Unified Management Layer
- **Cross-Number Intelligence**: Shared customer data between systems
- **Centralized Logging**: CloudWatch for all interactions
- **Cost Tracking**: Detailed usage analytics
- **Simple Web Dashboard**: Monitor both numbers from one interface

## User Experience

### User Personas

**Bot User**: 
- Technical staff using SMS commands to control systems
- Needs quick, reliable command execution
- Values 24/7 availability and instant responses

**Business Contact**:
- Customers calling/texting for support
- Expects local number and human interaction
- Needs professional voice experience

**Administrator**:
- Manages both communication channels
- Monitors usage and costs
- Configures bot commands and responses

### Key User Flows

**Bot Command Flow**:
1. User texts command to bot number
2. Bot processes and executes action
3. User receives confirmation
4. Conversation state saved for context

**Business Call Flow**:
1. Customer calls business number
2. Call forwards to owner's cell
3. If no answer, professional voicemail
4. Optional: Future IVR integration

**Cross-Channel Flow**:
1. Bot detects user needs human help
2. Bot provides business number
3. System notes context for continuity

## Technical Architecture

### System Components

**AWS Infrastructure**:
- Amazon SNS: SMS sending/receiving
- Amazon Pinpoint: Campaign management
- AWS Lambda: Message processing
- DynamoDB: Conversation storage
- CloudWatch: Logging and monitoring
- API Gateway: Webhook endpoints

**Telnyx Services**:
- Phone number hosting
- Voice call routing
- SMS messaging API
- SIP trunking (future)
- Programmable voice (future)

### Data Models

**Conversation Record**:
```json
{
  "phone_number": "+12145551234",
  "created_at": "2024-01-20T10:00:00Z",
  "updated_at": "2024-01-20T10:05:00Z",
  "message_count": 5,
  "last_message": "STATUS server1",
  "last_response": "Server1 is operational",
  "conversation_state": "active",
  "user_context": {}
}
```

**Bot Command Structure**:
```
COMMAND [parameters]
Examples:
- START [service_name]
- ACTION [task_description]
- REPORT [report_type]
- SCHEDULE [task] [time]
```

### APIs and Integrations

**Inbound Webhooks**:
- Telnyx SMS → AWS Lambda
- SNS notifications → Lambda

**Outbound APIs**:
- AWS SNS Publish API
- Telnyx Voice/SMS APIs
- Future: External action APIs

### Infrastructure Requirements

**AWS Resources**:
- Lambda: 256MB, 30s timeout
- DynamoDB: On-demand pricing
- API Gateway: Regional endpoint
- CloudWatch: 30-day retention

**Network**:
- HTTPS webhooks
- No VPC requirements
- Public API endpoints

## Development Roadmap

### Phase 1: MVP - Basic Bot SMS (Week 1)
**Foundation Setup**:
- AWS account configuration
- SNS enablement for SMS
- DynamoDB table creation
- IAM roles and permissions

**Bot Implementation**:
- Lambda function for message processing
- Basic command parser (HELP, STATUS, START, STOP)
- Conversation state tracking
- Error handling and logging

**Deliverables**:
- Working bot number accepting commands
- 5 basic commands functional
- Conversation history in DynamoDB
- CloudWatch logging active

### Phase 2: Business Communications (Week 1-2)
**Telnyx Setup**:
- Account creation and verification
- DFW number procurement
- Voice forwarding configuration
- Messaging profile creation

**Integration**:
- Webhook endpoint for Telnyx
- Business SMS auto-responses
- Voice forwarding testing
- Voicemail configuration

**Deliverables**:
- Professional business number active
- Voice calls forwarding properly
- Basic SMS handling
- Contact information updated

### Phase 3: Advanced Bot Features (Week 2-3)
**Enhanced Commands**:
- ACTION commands with parameters
- SCHEDULE functionality
- REPORT generation
- Bulk notification system

**Security & Auth**:
- Phone number whitelist
- Command authentication
- Rate limiting
- Audit logging

**Deliverables**:
- 15+ bot commands
- Scheduled task system
- Security measures active
- Bulk messaging capability

### Phase 4: Management Interface (Week 3-4)
**Web Dashboard**:
- React-based interface
- Real-time statistics
- Message history viewer
- Command builder

**Monitoring**:
- CloudWatch dashboards
- Cost tracking
- Usage analytics
- Alert configuration

**Deliverables**:
- Web UI deployed
- Analytics dashboard
- Cost monitoring
- Alert system

### Phase 5: Voice Bot Preparation (Future)
**Voice Infrastructure**:
- Telnyx programmable voice setup
- Speech-to-text integration
- Text-to-speech configuration
- IVR flow design

**Bot Voice Features**:
- Call handling webhooks
- Voice command processing
- Audio response generation
- Call routing logic

## Logical Dependency Chain

1. **AWS Foundation** (Required first)
   - Account setup → SNS configuration → DynamoDB creation

2. **Phone Numbers** (Parallel)
   - Telnyx number (immediate) + AWS number request (1-2 days)

3. **Basic Bot** (Depends on AWS setup)
   - Lambda deployment → SNS integration → Command parsing

4. **Business Features** (Depends on Telnyx)
   - Number configuration → Voice setup → SMS webhooks

5. **Enhanced Features** (Depends on basic bot)
   - State management → Advanced commands → Security layer

6. **Management UI** (Depends on core features)
   - API development → Frontend → Analytics

7. **Voice Bots** (Future, depends on all above)
   - Voice APIs → Bot integration → Testing

## Risks and Mitigations

### Technical Challenges

**Risk**: AWS number assignment (random area code)
- **Impact**: No local presence for bot number
- **Mitigation**: Accept for bot use; use Telnyx for local presence

**Risk**: Webhook reliability
- **Impact**: Missed messages
- **Mitigation**: Implement retry logic, use SQS for queuing

**Risk**: Rate limiting on APIs
- **Impact**: Service interruption
- **Mitigation**: Implement exponential backoff, monitor limits

### Figuring out the MVP

**Core MVP Requirements**:
1. Bot responds to basic commands
2. Business number forwards calls
3. Both numbers active and tested
4. Basic logging implemented
5. Cost tracking enabled

**MVP Success Metrics**:
- Bot responds within 2 seconds
- 99% message delivery rate
- Zero missed business calls
- Daily cost under $5

### Resource Constraints

**Budget**: 
- Monthly: $3.50 base + usage
- Development: 40 hours total
- No additional staff needed

**Timeline**:
- MVP: 1 week
- Full platform: 4 weeks
- Voice bots: Future phase

## Appendix

### Research Findings

**Cost Analysis**:
- AWS SMS: 38% cheaper than alternatives
- Telnyx voice: 40% cheaper than AWS Connect
- Total solution: 85% cheaper than RingCentral

**Provider Comparison**:
- AWS: Best for high-volume SMS
- Telnyx: Best for voice flexibility
- Hybrid: Optimal cost/feature balance

### Technical Specifications

**Message Format**:
```
Inbound: +1XXXXXXXXXX: COMMAND parameters
Outbound: [BOT] Response message
```

**Webhook Payload**:
```json
{
  "event_type": "message.received",
  "payload": {
    "from": {"phone_number": "+1234567890"},
    "to": [{"phone_number": "+0987654321"}],
    "text": "Message content"
  }
}
```

**Lambda Environment**:
- Runtime: Python 3.9
- Memory: 256MB
- Timeout: 30 seconds
- Concurrent executions: 100

### Command Reference

**Basic Commands**:
- `START` - Initialize bot interaction
- `STOP` - Unsubscribe from bot
- `HELP` - List available commands
- `STATUS` - Check system status

**Action Commands**:
- `ACTION [task]` - Execute specific task
- `REPORT [type]` - Generate report
- `SCHEDULE [task] [time]` - Schedule future action
- `ALERT [condition]` - Set up monitoring alert

**Admin Commands**:
- `STATS` - View usage statistics
- `WHITELIST [number]` - Add authorized user
- `BROADCAST [message]` - Send to all users
- `DEBUG [feature]` - Enable debug logging