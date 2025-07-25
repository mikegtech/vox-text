# 🎯 Correct Telnyx Signature Validation Architecture

## 🚨 **You Were Right Again!**

The issue was that API Gateway custom authorizers don't receive the request body/payload, making proper signature validation impossible. I've restructured the architecture to validate signatures in the SMS handler where we have access to the full payload.

## ❌ **Previous Problem:**

### **API Gateway Custom Authorizer Limitations:**
- ✅ **Headers available**: `telnyx-signature-ed25519`, `telnyx-timestamp`
- ❌ **Payload NOT available**: `event.body` is always empty
- ❌ **Can't validate signature**: Need `timestamp|payload` for proper validation

### **What We Were Doing Wrong:**
```python
# In authorizer - payload is always empty!
payload = event.get('body', '') or ''  # Always empty!
signed_payload = timestamp_bytes + b"|" + payload_bytes  # Wrong!
```

## ✅ **New Architecture: Signature Validation in SMS Handler**

### **Flow:**
```
Telnyx Webhook → API Gateway → Basic Authorizer → SMS Handler (with signature validation) → DynamoDB
```

### **Component Responsibilities:**

### **1. Basic Authorizer (telnyx-authorizer):**
- ✅ **Header validation**: Checks for required Telnyx headers
- ✅ **Basic timestamp validation**: Prevents very old requests
- ✅ **IP validation**: Optional Telnyx CIDR validation
- ❌ **No signature validation**: Passes through to SMS handler

### **2. SMS Handler (sms-handler):**
- ✅ **Full signature validation**: Has access to complete payload
- ✅ **Official Telnyx SDK pattern**: Uses PyNaCl library
- ✅ **Webhook processing**: Handles all Telnyx event types
- ✅ **DynamoDB integration**: Stores conversations and analytics

### **3. Fallback Handler (telnyx-fallback):**
- ✅ **No authentication**: Emergency fallback endpoint
- ✅ **Basic processing**: Handles failed deliveries
- ✅ **Error logging**: Stores events for manual review

## 🔧 **Updated Lambda Functions**

### **Basic Authorizer (Simplified):**
```python
# Only validates headers and basic timestamp
def lambda_handler(event, context):
    headers = {k.lower(): v for k, v in event.get('headers', {}).items()}
    signature = headers.get('telnyx-signature-ed25519', '')
    timestamp = headers.get('telnyx-timestamp', '')
    
    if not signature or not timestamp:
        return generate_policy('user', 'Deny', event['methodArn'])
    
    # Basic timestamp validation only
    if int(timestamp) < time.time() - 3600:  # 1 hour tolerance
        return generate_policy('user', 'Deny', event['methodArn'])
    
    return generate_policy('user', 'Allow', event['methodArn'])
```

### **SMS Handler (Full Validation):**
```python
# Has access to full payload for proper signature validation
def lambda_handler(event, context):
    headers = {k.lower(): v for k, v in event.get('headers', {}).items()}
    payload = event.get('body', '') or ''  # Full payload available!
    
    signature = headers.get('telnyx-signature-ed25519', '')
    timestamp = headers.get('telnyx-timestamp', '')
    
    # Official Telnyx SDK validation
    if not validate_telnyx_webhook(payload, signature, timestamp):
        return {'statusCode': 401, 'body': 'Unauthorized'}
    
    # Process webhook
    webhook_data = json.loads(payload)
    result = process_telnyx_webhook(webhook_data)
    
    return {'statusCode': 200, 'body': json.dumps(result)}
```

## 🚀 **Deployment with New Architecture**

### **Package All Functions:**
```bash
cd infrastructure

# Package all Lambda functions with dependencies
./deploy-with-packaging.sh
```

This will:
1. ✅ **Package authorizer** (basic validation only)
2. ✅ **Package SMS handler** (with PyNaCl for signature validation)
3. ✅ **Package fallback handler** (no authentication)
4. ✅ **Deploy all functions** with proper dependencies

## 📊 **Expected Behavior**

### **Authorizer Logs (Basic Validation):**
```
Request from IP: 65.154.156.118
Headers: ['telnyx-signature-ed25519', 'telnyx-timestamp', 'content-type']
SUCCESS: Basic validation passed - signature validation will happen in SMS handler
Generated policy: {"Effect": "Allow"}
```

### **SMS Handler Logs (Full Validation):**
```
INFO: PyNaCl library loaded successfully
Request details:
  - Payload length: 788
  - Has signature: True
  - Has timestamp: True
Signature validation details:
  - Signed payload length: 800 bytes
  - Timestamp: 1753440891
  - Payload preview: {"data":{"event_type":"message.received"...
SUCCESS: Signature verified with PyNaCl library (official Telnyx method)
Processing webhook event: message.received
Stored message from +1234567890 in DynamoDB
```

## 🎯 **Benefits of New Architecture**

### ✅ **Proper Signature Validation:**
- **Full payload access** in SMS handler
- **Official Telnyx SDK pattern** with PyNaCl
- **Correct `timestamp|payload` validation**

### ✅ **Layered Security:**
- **Basic filtering** in authorizer (headers, IP, timestamp)
- **Full validation** in SMS handler (signature verification)
- **Fallback endpoint** for emergency access

### ✅ **Production Ready:**
- **No payload limitations** 
- **Proper error handling** and logging
- **DynamoDB integration** for conversations
- **Analytics tracking** for all events

## 🧪 **Testing the New Architecture**

### **Test with Postman:**
Your Postman requests will now:
1. **Pass basic authorizer** (headers present)
2. **Reach SMS handler** with full payload
3. **Validate signature properly** with complete data
4. **Process webhook** and store in DynamoDB

### **Expected Flow:**
```
POST https://api.movearound.co/dev/webhooks/telnyx/sms
Headers: telnyx-signature-ed25519, telnyx-timestamp
Body: {"data": {"event_type": "message.received", ...}}

→ Basic Authorizer: ✅ Headers OK, Allow
→ SMS Handler: ✅ Full signature validation, Process webhook
→ DynamoDB: ✅ Store conversation and analytics
→ Response: 200 OK
```

## 🎉 **Ready to Deploy!**

The new architecture properly separates concerns:
- **Authorizer**: Basic filtering and security
- **SMS Handler**: Full validation and processing
- **Fallback**: Emergency handling

**Deploy the corrected architecture:**

```bash
./deploy-with-packaging.sh
```

**Now signature validation will work correctly with access to the full payload!** 🚀
