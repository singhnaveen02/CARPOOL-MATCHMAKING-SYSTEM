# AWS Deployment Guide

## Complete Production Setup for Smart Carpool Matching

This guide provides step-by-step instructions to deploy the Carpool system to AWS production environment.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    CloudFront CDN                            │
│              (Frontend asset distribution)                   │
└─────────────────┬──────────────────────────────────────────┘
                  │
┌─────────────────▼──────────────────────────────────────────┐
│                  Route 53 (DNS)                             │
│            carpool.example.com                              │
└─────────────────┬──────────────────────────────────────────┘
                  │
┌─────────────────▼──────────────────────────────────────────┐
│              Application Load Balancer                      │
│         (Routes requests to EC2/ECS)                        │
└────────┬────────────────────────┬─────────────────────────┘
         │                        │
    ┌────▼─────┐            ┌────▼─────┐
    │  EC2 /   │            │  EC2 /   │
    │  Backend │            │  Backend │
    │  Instance 1│           │  Instance 2│
    └────┬─────┘            └────┬─────┘
         │                   │
         └────────┬──────────┘
                  │
         ┌────────▼──────────┐
         │  RDS PostgreSQL   │
         │  + Read Replicas  │
         │  + Automated      │
         │    Backups        │
         └───────────────────┘

         ┌───────────────────┐
         │  S3 Bucket        │
         │  (File storage)   │
         └───────────────────┘

         ┌───────────────────┐
         │  CloudWatch       │
         │  (Monitoring)     │
         └───────────────────┘
```

---

## Phase 1: Prerequisites & Setup

### 1.1 AWS Account Setup
```bash
# Create AWS account if not exists
# Navigate to AWS Console: https://console.aws.amazon.com

# Create IAM User for deployment
# 1. Go to IAM > Users > Create User
# 2. Set name: carpool-deploy
# 3. Attach policies:
#    - AmazonEC2FullAccess
#    - AmazonRDSFullAccess
#    - AmazonS3FullAccess
#    - AWSCloudFormationFullAccess
#    - CloudWatchFullAccess
# 4. Generate Access Key ID and Secret Key
# 5. Save credentials securely (AWS Secrets Manager)
```

### 1.2 Install AWS CLI
```bash
# macOS / Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Windows PowerShell
$ProgressPreference = 'SilentlyContinue'
Invoke-WebRequest -Uri "https://awscli.amazonaws.com/AWSCLIV2.msi" -OutFile "AWSCLIV2.msi"
./AWSCLIV2.msi /qn

# Verify installation
aws --version
```

### 1.3 Configure AWS Credentials
```bash
aws configure
# Enter: Access Key ID
# Enter: Secret Access Key
# Enter: Default region (us-east-1 or your preferred region)
# Enter: Output format (json)

# Verify configuration
aws sts get-caller-identity
```

---

## Phase 2: Network Infrastructure (VPC, Security Groups)

### 2.1 Create VPC
```bash
# Create VPC with CIDR block 10.0.0.0/16
aws ec2 create-vpc --cidr-block 10.0.0.0/16 --tag-specifications 'ResourceType=vpc,Tags=[{Key=Name,Value=carpool-vpc}]'

# Save VPC ID from response
export VPC_ID="vpc-xxxxx"

# Enable DNS
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames
```

### 2.2 Create Subnets
```bash
# Public subnet for ALB (10.0.1.0/24)
aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.1.0/24 --availability-zone us-east-1a --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=carpool-public-subnet-1}]'

# Private subnet for EC2/RDS (10.0.2.0/24)
aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.2.0/24 --availability-zone us-east-1a --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=carpool-private-subnet-1}]'

# Private subnet for RDS multi-AZ (10.0.3.0/24)
aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.3.0/24 --availability-zone us-east-1b --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=carpool-private-subnet-2}]'

export PUBLIC_SUBNET="subnet-xxxxx"
export PRIVATE_SUBNET_1="subnet-xxxxx"
export PRIVATE_SUBNET_2="subnet-xxxxx"
```

### 2.3 Create Internet Gateway
```bash
# Create IGW
aws ec2 create-internet-gateway --tag-specifications 'ResourceType=internet-gateway,Tags=[{Key=Name,Value=carpool-igw}]'

export IGW_ID="igw-xxxxx"

# Attach to VPC
aws ec2 attach-internet-gateway --internet-gateway-id $IGW_ID --vpc-id $VPC_ID
```

### 2.4 Create Route Table (Public)
```bash
# Create route table
aws ec2 create-route-table --vpc-id $VPC_ID --tag-specifications 'ResourceType=route-table,Tags=[{Key=Name,Value=carpool-public-rt}]'

export PUBLIC_RT="rtb-xxxxx"

# Add route to IGW
aws ec2 create-route --route-table-id $PUBLIC_RT --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID

# Associate with public subnet
aws ec2 associate-route-table --route-table-id $PUBLIC_RT --subnet-id $PUBLIC_SUBNET
```

### 2.5 Create Security Groups
```bash
# ALB Security Group (allow HTTP/HTTPS from internet)
aws ec2 create-security-group --group-name carpool-alb-sg --description "ALB security group" --vpc-id $VPC_ID

export ALB_SG="sg-xxxxx"

aws ec2 authorize-security-group-ingress --group-id $ALB_SG --protocol tcp --port 80 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $ALB_SG --protocol tcp --port 443 --cidr 0.0.0.0/0

# Backend Security Group (allow from ALB)
aws ec2 create-security-group --group-name carpool-backend-sg --description "Backend security group" --vpc-id $VPC_ID

export BACKEND_SG="sg-xxxxx"

aws ec2 authorize-security-group-ingress --group-id $BACKEND_SG --protocol tcp --port 8000 --source-group $ALB_SG
aws ec2 authorize-security-group-ingress --group-id $BACKEND_SG --protocol tcp --port 22 --cidr 0.0.0.0/0  # SSH (restrict in production)

# RDS Security Group (allow from backend)
aws ec2 create-security-group --group-name carpool-rds-sg --description "RDS security group" --vpc-id $VPC_ID

export RDS_SG="sg-xxxxx"

aws ec2 authorize-security-group-ingress --group-id $RDS_SG --protocol tcp --port 5432 --source-group $BACKEND_SG
```

---

## Phase 3: Database Setup (RDS PostgreSQL)

### 3.1 Create DB Subnet Group
```bash
aws rds create-db-subnet-group \
  --db-subnet-group-name carpool-db-subnet-group \
  --db-subnet-group-description "Subnet group for carpool DB" \
  --subnet-ids $PRIVATE_SUBNET_1 $PRIVATE_SUBNET_2 \
  --tags Key=Name,Value=carpool-db-subnet-group
```

### 3.2 Create RDS Instance (PostgreSQL + PostGIS)
```bash
aws rds create-db-instance \
  --db-instance-identifier carpool-db-primary \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 15.3 \
  --master-username postgres \
  --master-user-password "YourSecurePassword123!" \
  --allocated-storage 100 \
  --db-subnet-group-name carpool-db-subnet-group \
  --vpc-security-group-ids $RDS_SG \
  --no-publicly-accessible \
  --enable-cloudwatch-logs-exports '["postgresql"]' \
  --enable-iam-database-authentication \
  --backup-retention-period 30 \
  --preferred-backup-window "03:00-04:00" \
  --preferred-maintenance-window "sun:04:00-sun:05:00" \
  --enable-multiple-az \
  --tags Key=Name,Value=carpool-db-primary

# Wait for DB instance to be available (5-10 minutes)
aws rds describe-db-instances --db-instance-identifier carpool-db-primary

# Once available, get endpoint
export RDS_ENDPOINT=$(aws rds describe-db-instances --db-instance-identifier carpool-db-primary --query 'DBInstances[0].Endpoint.Address' --output text)

echo "RDS Endpoint: $RDS_ENDPOINT"
```

### 3.3 Create PostGIS Extension
```bash
# Connect to database
PGPASSWORD='YourSecurePassword123!' psql -h $RDS_ENDPOINT -U postgres -d postgres

# Create carpool database
CREATE DATABASE carpool_db;

# Connect to new database
\c carpool_db

# Create PostGIS extension
CREATE EXTENSION postgis;

# Verify
\dx

# Exit
\q
```

### 3.4 Initialize Database Schema
```bash
# Upload and run schema.sql
PGPASSWORD='YourSecurePassword123!' psql -h $RDS_ENDPOINT -U postgres -d carpool_db -f database/schema.sql
```

---

## Phase 4: EC2 Instance & Backend Deployment

### 4.1 Create EC2 Instance
```bash
# Create EC2 instance
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.medium \
  --key-name carpool-key \
  --security-group-ids $BACKEND_SG \
  --subnet-id $PRIVATE_SUBNET_1 \
  --associate-public-ip-address \
  --user-data file://backend-setup.sh \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=carpool-backend-1}]'

export EC2_INSTANCE_ID="i-xxxxx"

# Wait for instance to be running
aws ec2 wait instance-running --instance-ids $EC2_INSTANCE_ID

# Get instance IP
export EC2_PRIVATE_IP=$(aws ec2 describe-instances --instance-ids $EC2_INSTANCE_ID --query 'Reservations[0].Instances[0].PrivateIpAddress' --output text)
```

### 4.2 Backend Setup Script
```bash
# Create backend-setup.sh
cat > backend-setup.sh << 'EOF'
#!/bin/bash
set -e

# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install dependencies
sudo apt-get install -y python3.11 python3-pip python3-venv git postgresql-client

# Clone repository
cd /opt
sudo git clone https://github.com/yourusername/carpool-backend.git
cd carpool-backend

# Create virtual environment
sudo python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt

# Create .env file
cat > .env << 'DOTENV'
DATABASE_URL=postgresql://postgres:YourSecurePassword123!@$RDS_ENDPOINT:5432/carpool_db
SECRET_KEY=your-super-secret-key-change-this
GMNI_API_KEY=your-gemini-api-key
OSRM_API_URL=https://router.project-osrm.org
FRONTEND_URL=https://carpool.example.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
DOTENV

# Run migrations (using Alembic - optional Phase 2+)
# alembic upgrade head

# Start backend with systemd
sudo tee /etc/systemd/system/carpool-backend.service > /dev/null << 'SERVICE'
[Unit]
Description=Carpool Backend Service
After=network.target

[Service]
Type=notify
User=ubuntu
WorkingDirectory=/opt/carpool-backend
Environment="PATH=/opt/carpool-backend/venv/bin"
ExecStart=/opt/carpool-backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE

sudo systemctl daemon-reload
sudo systemctl enable carpool-backend
sudo systemctl start carpool-backend
EOF

chmod +x backend-setup.sh
```

### 4.3 Deploy Backend Updates
```bash
# SSH into instance
ssh -i carpool-key.pem ubuntu@$EC2_PRIVATE_IP

# Pull latest changes
cd /opt/carpool-backend
git pull origin main

# Restart service
sudo systemctl restart carpool-backend

# Check status
sudo systemctl status carpool-backend
```

---

## Phase 5: Load Balancer & Frontend

### 5.1 Create Application Load Balancer
```bash
# Create target group for backend
aws elbv2 create-target-group \
  --name carpool-backend-tg \
  --protocol HTTP \
  --port 8000 \
  --vpc-id $VPC_ID \
  --health-check-enabled \
  --health-check-protocol HTTP \
  --health-check-path /api/health \
  --health-check-interval-seconds 30 \
  --health-check-timeout-seconds 5 \
  --healthy-threshold-count 2 \
  --unhealthy-threshold-count 3

export TARGET_GROUP_ARN="arn:aws:elasticloadbalancing:..."

# Register target
aws elbv2 register-targets \
  --target-group-arn $TARGET_GROUP_ARN \
  --targets Id=$EC2_PRIVATE_IP,Port=8000

# Create ALB
aws elbv2 create-load-balancer \
  --name carpool-alb \
  --subnets $PUBLIC_SUBNET \
  --security-groups $ALB_SG \
  --scheme internet-facing \
  --type application

export ALB_ARN="arn:aws:elasticloadbalancing:..."

# Get ALB DNS
export ALB_DNS=$(aws elbv2 describe-load-balancers --load-balancer-arns $ALB_ARN --query 'LoadBalancers[0].DNSName' --output text)
```

### 5.2 Create Listener & Rules
```bash
# Create HTTP listener (redirect to HTTPS)
aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=redirect,RedirectConfig="{Protocol=HTTPS,Port=443,StatusCode=HTTP_301}"

# Create HTTPS listener (requires SSL cert)
# First, create or import SSL certificate in ACM
# Then create listener pointing to target group
aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=arn:aws:acm:... \
  --default-actions Type=forward,TargetGroupArn=$TARGET_GROUP_ARN
```

### 5.3 Deploy Frontend to CloudFront + S3
```bash
# Create S3 bucket for frontend
aws s3 mb s3://carpool-frontend-prod --region us-east-1

# Build frontend
cd carpool-frontend
npm install
npm run build

# Upload to S3
aws s3 sync build/ s3://carpool-frontend-prod/ --delete

# Create CloudFront distribution
aws cloudfront create-distribution \
  --origin-domain-name carpool-frontend-prod.s3.us-east-1.amazonaws.com \
  --default-root-object index.html \
  --enabled

# Get CloudFront domain
export CLOUDFRONT_DOMAIN="d123456.cloudfront.net"
```

---

## Phase 6: Domain & DNS (Route 53)

### 6.1 Register Domain (or use existing)
```bash
# Register domain in Route 53
aws route53 register-domain --domain-name carpool.example.com --duration-in-years 1

# Or use existing hosted zone
export HOSTED_ZONE_ID="Z123456..."
```

### 6.2 Create DNS Records
```bash
# Create A record for API (ALB)
aws route53 change-resource-record-sets \
  --hosted-zone-id $HOSTED_ZONE_ID \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "api.carpool.example.com",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "Z35SXDOTRQ7X7K",
          "DNSName": "'$ALB_DNS'",
          "EvaluateTargetHealth": false
        }
      }
    }]
  }'

# Create A record for Frontend (CloudFront)
aws route53 change-resource-record-sets \
  --hosted-zone-id $HOSTED_ZONE_ID \
  --change-batch '{
    "Changes": [{
      "Action": "CREATE",
      "ResourceRecordSet": {
        "Name": "carpool.example.com",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "Z2FDTNDATAQYW2",
          "DNSName": "'$CLOUDFRONT_DOMAIN'",
          "EvaluateTargetHealth": false
        }
      }
    }]
  }'
```

---

## Phase 7: Monitoring & Logging

### 7.1 CloudWatch Metrics
```bash
# Create custom metrics
aws cloudwatch put-metric-data \
  --namespace Carpool \
  --metric-name MatchScore \
  --value 75.5

# Create alarm for high error rate
aws cloudwatch put-metric-alarm \
  --alarm-name carpool-high-error-rate \
  --alarm-description "Alert if error rate exceeds 5%" \
  --metric-name ErrorRate \
  --namespace Carpool \
  --statistic Average \
  --period 60 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold
```

### 7.2 RDS Monitoring
```bash
# Enable enhanced monitoring
aws rds modify-db-instance \
  --db-instance-identifier carpool-db-primary \
  --enable-cloudwatch-logs-exports postgresql \
  --apply-immediately
```

### 7.3 Application Logging
```bash
# Configure CloudWatch Logs in backend
# Update config.py:
# LOG_GROUP = "/aws/ec2/carpool-backend"
# LOG_STREAM = "backend-logs"
```

---

## Phase 8: Scaling & Auto-Recovery

### 8.1 Auto-Scaling Group
```bash
# Create launch template
aws ec2 create-launch-template \
  --launch-template-name carpool-backend-template \
  --launch-template-data '{
    "ImageId": "ami-0c55b159cbfafe1f0",
    "InstanceType": "t3.medium",
    "KeyName": "carpool-key",
    "SecurityGroupIds": ["'$BACKEND_SG'"]
  }'

# Create auto-scaling group
aws autoscaling create-auto-scaling-group \
  --auto-scaling-group-name carpool-asg \
  --launch-template LaunchTemplateName=carpool-backend-template \
  --min-size 2 \
  --max-size 10 \
  --desired-capacity 3 \
  --vpc-zone-identifier "$PRIVATE_SUBNET_1,$PRIVATE_SUBNET_2" \
  --target-group-arns $TARGET_GROUP_ARN
```

### 8.2 Scaling Policies
```bash
# Scale up policy
aws autoscaling put-scaling-policy \
  --auto-scaling-group-name carpool-asg \
  --policy-name scale-up \
  --policy-type TargetTrackingScaling \
  --target-tracking-configuration '{
    "TargetValue": 70.0,
    "PredefinedMetricSpecification": {
      "PredefinedMetricType": "ASGAverageCPUUtilization"
    }
  }'
```

---

## Phase 9: Backup & Disaster Recovery

### 9.1 Automated Backups
```bash
# RDS backups are automatic (30-day retention)
# Create manual snapshot
aws rds create-db-snapshot \
  --db-instance-identifier carpool-db-primary \
  --db-snapshot-identifier carpool-db-snapshot-$(date +%Y%m%d)

# Test restore process (optional)
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier carpool-db-restore-test \
  --db-snapshot-identifier carpool-db-snapshot-20240101
```

### 9.2 Cross-Region Backup
```bash
# Create read replica in different region
aws rds create-db-instance-read-replica \
  --db-instance-identifier carpool-db-replica-us-west-2 \
  --source-db-instance-identifier carpool-db-primary \
  --source-region us-east-1 \
  --region us-west-2
```

---

## Phase 10: SSL/TLS Certificate

### 10.1 Create Certificate in ACM
```bash
# Request certificate
aws acm request-certificate \
  --domain-name carpool.example.com \
  --subject-alternative-names api.carpool.example.com \
  --validation-method DNS

# Get certificate ARN for use in ALB
export CERT_ARN="arn:aws:acm:..."
```

---

## Troubleshooting

### Cannot Connect to RDS
```bash
# Check security group rules
aws ec2 describe-security-groups --group-ids $RDS_SG

# Test connectivity from EC2
ssh -i carpool-key.pem ubuntu@$EC2_PRIVATE_IP
psql -h $RDS_ENDPOINT -U postgres -d postgres
```

### Backend Not Responding
```bash
# SSH into instance and check logs
ssh -i carpool-key.pem ubuntu@$EC2_PRIVATE_IP
sudo journalctl -u carpool-backend -f

# Check if service is running
sudo systemctl status carpool-backend

# Restart service
sudo systemctl restart carpool-backend
```

### High Database Load
```bash
# Check connections
SELECT count(*) FROM pg_stat_activity;

# Optimize indexes
VACUUM ANALYZE;

# Consider read replicas
```

---

## Cost Estimation (Monthly)

- **EC2 (t3.medium x 3)**: ~$90 × 3 = $270
- **RDS (db.t3.micro)**: ~$30
- **S3**: ~$5
- **CloudFront**: ~$20
- **Data Transfer**: ~$50
- **Route 53**: ~$0.50
- **CloudWatch**: ~$10
- **Total**: ~$385/month

*Optimize with Reserved Instances for 40-60% savings*

---

## Next Steps

1. ✅ Set up VPC & Security
2. ✅ Deploy RDS PostgreSQL
3. ✅ Launch EC2 backend instances
4. ✅ Configure ALB & Route 53
5. ⏳ Deploy frontend to CloudFront
6. ⏳ Set up monitoring & alerts
7. ⏳ Configure auto-scaling
8. ⏳ Implement disaster recovery
