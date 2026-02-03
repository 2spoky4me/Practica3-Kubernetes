#!/bin/bash
set -e

ENV=${1:-dev}

if [ "$ENV" = "prod" ]; then
  CONTEXT="k3d-pro"
  NAMESPACE="pro"
  EXPECTED_REPLICAS=3
  BASE_URL="http://flask-pro.local:8082"
  USE_REDIS=true
  USE_MINIO=true
  MINIO_URL="http://minio-api-pro.local:8082"
else
  CONTEXT="k3d-dev"
  NAMESPACE="dev"
  EXPECTED_REPLICAS=2
  BASE_URL="http://flask-dev.local:8081"
  USE_REDIS=false
  USE_MINIO=false
fi

echo "=== E2E tests for environment: $ENV ==="

# -------------------------------------------------
# 1. Réplicas
# -------------------------------------------------
echo "-> Checking replicas"

READY_REPLICAS=$(kubectl get deploy flask-app \
  -n $NAMESPACE \
  --context $CONTEXT \
  -o jsonpath='{.status.readyReplicas}')

if [ -z "$READY_REPLICAS" ] || [ "$READY_REPLICAS" -lt "$EXPECTED_REPLICAS" ]; then
  echo "ERROR: Expected $EXPECTED_REPLICAS ready replicas, got $READY_REPLICAS"
  exit 1
fi

echo "OK: $READY_REPLICAS replicas Ready"

# -------------------------------------------------
# 2. Distribución de tráfico
# -------------------------------------------------
echo "-> Checking traffic distribution"

declare -A PODS

for i in {1..10}; do
  POD=$(curl -s $BASE_URL | grep Instance | awk '{print $2}')
  PODS[$POD]=$((PODS[$POD]+1))
done

echo "Traffic distribution:"
for p in "${!PODS[@]}"; do
  echo "  $p -> ${PODS[$p]} requests"
done

if [ "${#PODS[@]}" -lt 2 ]; then
  echo "ERROR: Traffic is not distributed between replicas"
  exit 1
fi

# -------------------------------------------------
# 3. MinIO (solo prod)
# -------------------------------------------------
if [ "$USE_MINIO" = true ]; then
  echo "-> Checking MinIO"

  MC_ALIAS="minio"
  mc alias rm $MC_ALIAS >/dev/null 2>&1 || true
  mc alias set $MC_ALIAS $MINIO_URL admin admin123

  FILES=$(mc ls $MC_ALIAS/logouib | wc -l)
  if [ "$FILES" -lt 1 ]; then
    echo "ERROR: No files found in MinIO bucket"
    exit 1
  fi

  mc cp $MC_ALIAS/logouib/logouib.png /tmp/logouib.png

  if [ ! -s /tmp/logouib.png ]; then
    echo "ERROR: Downloaded MinIO file is empty or corrupted"
    exit 1
  fi

  echo "OK: MinIO file exists and is valid"
else
  echo "-> Skipping MinIO check (dev)"
fi

# -------------------------------------------------
# 4. Redis cache (solo prod)
# -------------------------------------------------
if [ "$USE_REDIS" = true ]; then
  echo "-> Checking Redis cache"

  # Forzar uso de caché
  curl -s $BASE_URL/list > /dev/null

  REDIS_POD=$(kubectl get pods -n $NAMESPACE -l app=redis \
    -o jsonpath='{.items[0].metadata.name}')

  if [ -z "$REDIS_POD" ]; then
    echo "ERROR: Redis pod not found"
    exit 1
  fi

  KEYS=$(kubectl exec -n $NAMESPACE $REDIS_POD -- redis-cli KEYS '*' | wc -l)

  if [ "$KEYS" -lt 1 ]; then
    echo "ERROR: No keys found in Redis"
    exit 1
  fi

  KEY=$(kubectl exec -n $NAMESPACE $REDIS_POD -- redis-cli KEYS '*' | head -n 1)
  TTL=$(kubectl exec -n $NAMESPACE $REDIS_POD -- redis-cli TTL "$KEY")

  echo "Redis key: $KEY"
  echo "TTL: $TTL seconds"

  if [ "$TTL" -le 0 ]; then
    echo "ERROR: Redis key has no TTL"
    exit 1
  fi

  echo "OK: Redis cache working"
fi

# -------------------------------------------------
# 5. Health + latencias 
# -------------------------------------------------
echo "-> Checking /health endpoint"

HEALTH=$(curl -s $BASE_URL/health)

APP_STATUS=$(echo "$HEALTH" | jq -r '.app')
DB_STATUS=$(echo "$HEALTH" | jq -r '.database.status')

REDIS_TYPE=$(echo "$HEALTH" | jq -r '.redis | type')

if [ "$REDIS_TYPE" = "object" ]; then
  REDIS_STATUS=$(echo "$HEALTH" | jq -r '.redis.status')
  REDIS_LATENCY=$(echo "$HEALTH" | jq -r '.redis.latency_ms')
else
  REDIS_STATUS=$(echo "$HEALTH" | jq -r '.redis')
  REDIS_LATENCY="n/a"
fi

APP_LATENCY=$(echo "$HEALTH" | jq -r '.latency_ms')
DB_LATENCY=$(echo "$HEALTH" | jq -r '.database.latency_ms')

if [ "$APP_STATUS" != "up" ]; then
  echo "ERROR: app not up"
  exit 1
fi

if [ "$DB_STATUS" != "ok" ]; then
  echo "ERROR: database not ok"
  exit 1
fi

if [ "$USE_REDIS" = true ] && [ "$REDIS_STATUS" != "ok" ]; then
  echo "ERROR: redis not ok"
  exit 1
fi

echo "Latencies:"
echo "  App: ${APP_LATENCY} ms"
echo "  Database: ${DB_LATENCY} ms"

if [ "$USE_REDIS" = true ]; then
  echo "  Redis: ${REDIS_LATENCY} ms"
fi

echo "OK: /health endpoint valid"
echo "=== E2E tests completed successfully ==="
