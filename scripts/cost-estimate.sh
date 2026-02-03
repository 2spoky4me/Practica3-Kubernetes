#!/bin/bash
set -e

ENV=${ENV:-dev}

REGION="eu-south-2"
HOURS=730

if [ "$ENV" = "pro" ]; then
  NAMESPACE="pro"
  EC2_TYPE="t3.medium"
  EC2_PRICE=0.0416        # €/hour
  RDS_PRICE=0.068         # €/hour
  REDIS_PRICE=0.034       # €/hour
  ALB_PRICE=18            # €/month
else
  NAMESPACE="dev"
  EC2_TYPE="t3.small"
  EC2_PRICE=0.0208
  RDS_PRICE=0.034
  REDIS_PRICE=0
  ALB_PRICE=18
fi

echo "=========================================="
echo " AWS Monthly Cost Estimate ($ENV)"
echo " Region: $REGION"
echo "=========================================="

# -------------------------------------------------
# Compute - Application (EC2)
# -------------------------------------------------
APP_REPLICAS=$(kubectl get deploy flask-app -n $NAMESPACE -o jsonpath='{.status.replicas}')
EC2_TOTAL=$(echo "$APP_REPLICAS * $EC2_PRICE * $HOURS" | bc)

echo
echo "Compute (EC2 - Application)"
echo "  Replicas: $APP_REPLICAS"
echo "  Instance type: $EC2_TYPE"
echo "  Monthly cost: €$EC2_TOTAL"

# -------------------------------------------------
# Load Balancer
# -------------------------------------------------
echo
echo "Load Balancer (Application Load Balancer)"
echo "  Monthly cost: €$ALB_PRICE"

# -------------------------------------------------
# Database - PostgreSQL
# -------------------------------------------------
RDS_TOTAL=$(echo "$RDS_PRICE * $HOURS" | bc)

echo
echo "Database (RDS PostgreSQL)"
echo "  Monthly cost: €$RDS_TOTAL"

# -------------------------------------------------
# Redis
# -------------------------------------------------
if [ "$ENV" = "pro" ]; then
  REDIS_TOTAL=$(echo "$REDIS_PRICE * $HOURS" | bc)
  echo
  echo "Cache (ElastiCache Redis)"
  echo "  Monthly cost: €$REDIS_TOTAL"
else
  REDIS_TOTAL=0
fi

# -------------------------------------------------
# Object Storage
# -------------------------------------------------
S3_PRICE=2

echo
echo "Object Storage (S3 Standard)"
echo "  Estimated cost: €$S3_PRICE"

# -------------------------------------------------
# TOTAL
# -------------------------------------------------
TOTAL=$(echo "$EC2_TOTAL + $ALB_PRICE + $RDS_TOTAL + $REDIS_TOTAL + $S3_PRICE" | bc)

echo
echo "------------------------------------------"
echo " Estimated TOTAL monthly cost: €$TOTAL"
echo "------------------------------------------"

echo
echo "DISCLAIMER:"
echo "- Prices based on AWS on-demand pricing"
echo "- Region: eu-south-2 (Milan)"
echo "- Pods are mapped to AWS managed services"
echo "- Network traffic, backups and data transfer not included"
echo "- Costs are approximate and may vary depending on usage"
