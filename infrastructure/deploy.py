#!/usr/bin/env python3
"""
SMS Bot Infrastructure Deployment Script

This script handles deployment of the SMS Bot infrastructure using the new Python CDK setup.
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path


def setup_environment():
    """Ensure the environment is properly configured"""
    required_vars = ['CDK_DEFAULT_ACCOUNT', 'AWS_PROFILE']
    missing_vars = [var for var in required_vars if not os.environ.get(var)]
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n💡 Please run: source ./scripts/setup-aws-env.sh")
        return False
    
    return True


def run_command(command: list[str], description: str) -> bool:
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Command: {' '.join(command)}")
        print(f"Error: {e.stderr}")
        return False


def main():
    """Main deployment function"""
    parser = argparse.ArgumentParser(description="Deploy SMS Bot Infrastructure")
    parser.add_argument("environment", choices=["dev", "staging", "prod"], 
                       help="Target environment")
    parser.add_argument("company", help="Company name for tagging")
    parser.add_argument("--tenant", help="Tenant identifier (optional)")
    parser.add_argument("--synth-only", action="store_true", 
                       help="Only synthesize, don't deploy")
    parser.add_argument("--diff", action="store_true", 
                       help="Show differences before deploying")
    
    args = parser.parse_args()
    
    # Check environment setup
    if not setup_environment():
        sys.exit(1)
    
    # Set CDK context
    context_args = [
        "--context", f"environment={args.environment}",
        "--context", f"company={args.company}"
    ]
    
    if args.tenant:
        context_args.extend(["--context", f"tenant={args.tenant}"])
    
    print(f"🚀 Deploying SMS Bot Infrastructure")
    print(f"   Environment: {args.environment}")
    print(f"   Company: {args.company}")
    print(f"   Tenant: {args.tenant or f'{args.environment}-tenant'}")
    print(f"   Account: {os.environ.get('CDK_DEFAULT_ACCOUNT')}")
    print(f"   Region: {os.environ.get('CDK_DEFAULT_REGION', 'us-east-1')}")
    print()
    
    # Synthesize the app
    synth_cmd = ["python3", "app.py"] + context_args
    if not run_command(synth_cmd, "Synthesizing CDK app"):
        sys.exit(1)
    
    if args.synth_only:
        print("✅ Synthesis complete (synth-only mode)")
        return
    
    # Show diff if requested
    if args.diff:
        diff_cmd = ["cdk", "diff"] + context_args
        run_command(diff_cmd, "Showing differences")
        
        response = input("\n❓ Continue with deployment? (y/N): ")
        if response.lower() != 'y':
            print("❌ Deployment cancelled")
            return
    
    # Deploy the stack
    deploy_cmd = ["cdk", "deploy", "--require-approval", "never"] + context_args
    if not run_command(deploy_cmd, f"Deploying to {args.environment}"):
        sys.exit(1)
    
    print(f"✅ SMS Bot infrastructure successfully deployed to {args.environment}!")
    print(f"📋 Check the outputs above for important resource information")


if __name__ == "__main__":
    main()
