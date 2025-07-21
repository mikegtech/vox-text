# .gitignore Checklist for CDK Project

## ✅ Files and Directories Excluded from Git

### CDK Specific Files
- ✅ `cdk.out/` - CDK synthesis output directory
- ✅ `.cdk.staging/` - CDK asset staging directory  
- ✅ `cdk.context.json` - CDK context cache (auto-generated)
- ✅ `.cdk-bootstrapped*` - Bootstrap tracking files
- ✅ `outputs-*.json` - Deployment output files

### AWS Credentials and Secrets
- ✅ `.aws/` - AWS credentials directory
- ✅ `aws-credentials*` - Any AWS credential files
- ✅ `*.pem` - Private key files
- ✅ `*.key` - Key files
- ✅ `.aws-sso-cache/` - AWS SSO cache

### Environment Variables
- ✅ `.env` - Environment variables
- ✅ `.env.*` - All environment variable files
- ✅ `.env.local` - Local environment overrides
- ✅ `.env.development.local` - Development environment
- ✅ `.env.test.local` - Test environment
- ✅ `.env.production.local` - Production environment

### Node.js and Build Artifacts
- ✅ `node_modules/` - Dependencies
- ✅ `*.js` - Compiled JavaScript (except jest.config.js)
- ✅ `*.d.ts` - TypeScript declaration files
- ✅ `*.tsbuildinfo` - TypeScript build cache
- ✅ `dist/` - Distribution directory
- ✅ `build/` - Build output
- ✅ `out/` - Output directory

### Logs and Temporary Files
- ✅ `*.log` - All log files
- ✅ `logs/` - Log directory
- ✅ `*.tmp` - Temporary files
- ✅ `*.temp` - Temporary files
- ✅ `.tmp/` - Temporary directory
- ✅ `.temp/` - Temporary directory

### Editor and OS Files
- ✅ `.vscode/` - VS Code settings
- ✅ `.idea/` - IntelliJ IDEA settings
- ✅ `*.swp` - Vim swap files
- ✅ `*.swo` - Vim swap files
- ✅ `.DS_Store` - macOS Finder info
- ✅ `Thumbs.db` - Windows thumbnail cache

### Test and Coverage
- ✅ `coverage/` - Test coverage reports
- ✅ `.nyc_output/` - NYC coverage output
- ✅ `test-results/` - Test result files
- ✅ `test-reports/` - Test report files

### CloudFormation Templates
- ✅ `*.template.json` - Generated CF templates
- ✅ `*.template.yaml` - Generated CF templates
- ✅ `template.yml` - Generated CF templates
- ✅ `template.yaml` - Generated CF templates

## 🚨 Critical Security Items

These files should **NEVER** be committed:

### AWS Credentials
- ❌ AWS access keys
- ❌ AWS secret keys  
- ❌ AWS session tokens
- ❌ Private key files (.pem, .key)
- ❌ AWS SSO cache files

### Environment Variables
- ❌ Database passwords
- ❌ API keys
- ❌ Service account credentials
- ❌ Encryption keys
- ❌ Any .env files with secrets

### Generated Files
- ❌ CDK synthesis output (cdk.out/)
- ❌ Deployment outputs with sensitive data
- ❌ CloudFormation templates with hardcoded values

## 📋 Verification Commands

### Check for Accidentally Committed Files
```bash
# Check git status
git status

# Check for AWS credentials in history
git log --all --full-history -- .aws/
git log --all --full-history -- "*.pem"
git log --all --full-history -- "*.key"

# Check for environment files
git log --all --full-history -- ".env*"
```

### Clean Up if Files Were Committed
```bash
# Remove from git but keep locally
git rm --cached filename

# Remove from git history (dangerous - use carefully)
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch filename' \
  --prune-empty --tag-name-filter cat -- --all
```

## 🔍 Regular Maintenance

### Monthly Checks
- [ ] Review .gitignore for new file types
- [ ] Check for any credentials in git history
- [ ] Verify CDK output files are excluded
- [ ] Update .gitignore for new tools/dependencies

### Before Each Commit
- [ ] Run `git status` to check staged files
- [ ] Ensure no .env files are staged
- [ ] Verify no AWS credentials are staged
- [ ] Check no build artifacts are staged

## 📚 Additional Resources

- [Git .gitignore documentation](https://git-scm.com/docs/gitignore)
- [GitHub .gitignore templates](https://github.com/github/gitignore)
- [AWS CDK .gitignore best practices](https://docs.aws.amazon.com/cdk/latest/guide/best-practices.html)

---

**Remember**: It's better to exclude too much than too little when it comes to sensitive files!
