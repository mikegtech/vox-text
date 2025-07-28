# AWS Profile Configuration Guide

## 🎯 Current Profile Setup

Your infrastructure uses the **`boss`** AWS profile by default, set in:

```bash
# scripts/setup-aws-env.sh (line 14)
AWS_PROFILE_NAME=${1:-boss}  # 👈 Default is 'boss'
```

## 🔧 How to Change AWS Profile

### **Method 1: Runtime Override (Recommended)**
```bash
# Use different profile for one deployment
source ./scripts/setup-aws-env.sh my-profile
./deploy.py dev your-company
```

### **Method 2: Environment Variable**
```bash
# Set profile directly
export AWS_PROFILE=my-profile
export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export CDK_DEFAULT_ACCOUNT=$AWS_ACCOUNT_ID
./deploy.py dev your-company
```

### **Method 3: Change Default Profile**
Edit `scripts/setup-aws-env.sh`:
```bash
# Change line 14 from:
AWS_PROFILE_NAME=${1:-boss}

# To your preferred default:
AWS_PROFILE_NAME=${1:-my-profile}
```

### **Method 4: Create Profile-Specific Scripts**
```bash
# Create deploy-with-my-profile.sh
cp deploy-with-boss.sh deploy-with-my-profile.sh
# Edit the new script to use your profile
```

## 📋 Profile Validation

The setup script validates your profile:
```bash
# Check if profile exists
if ! aws configure list-profiles | grep -q "^$AWS_PROFILE$"; then
    echo "❌ AWS profile '$AWS_PROFILE' not found"
    aws configure list-profiles  # Shows available profiles
    exit 1
fi
```

## 🔍 Current Profile Detection

Check what profile is currently active:
```bash
echo "Current AWS Profile: $AWS_PROFILE"
aws sts get-caller-identity  # Shows current account/user
```
