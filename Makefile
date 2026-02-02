# ====================
# VARIABLES
# ====================

DEV_CLUSTER=dev
PRO_CLUSTER=pro

DEV_LB_PORT=8081
PRO_LB_PORT=8082

IMAGE_NAME=flask-app
IMAGE_TAG=prac3

# ====================
# PHONY
# ====================

.PHONY: clean \
        dev-cluster pro-cluster \
        build \
        dev prod \
        monitoring grafana \
        test

# ====================
# CLEAN: borra TODOS los clusters
# ====================

clean:
	k3d cluster delete $(DEV_CLUSTER) || true
	k3d cluster delete $(PRO_CLUSTER) || true

# ====================
# CLUSTERS
# ====================

dev-cluster:
	k3d cluster create $(DEV_CLUSTER) \
		--servers 1 \
		--agents 2 \
		-p "$(DEV_LB_PORT):80@loadbalancer" \
		--wait || true

pro-cluster:
	k3d cluster create $(PRO_CLUSTER) \
		--servers 1 \
		--agents 3 \
		-p "$(PRO_LB_PORT):80@loadbalancer" \
		--wait || true

# ====================
# BUILD: imagen Docker
# ====================

build:
	docker build -t $(IMAGE_NAME):$(IMAGE_TAG) app

# ====================
# DEV: despliegue completo DEV
# ====================

dev: build
	kubectl config use-context k3d-$(DEV_CLUSTER)
	kubectl create namespace dev || true
	k3d image import $(IMAGE_NAME):$(IMAGE_TAG) -c $(DEV_CLUSTER)
	kubectl apply -f k8s/dev

# ====================
# PROD: despliegue completo PRO
# ====================

prod: build
	kubectl config use-context k3d-$(PRO_CLUSTER)
	kubectl create namespace pro || true
	k3d image import $(IMAGE_NAME):$(IMAGE_TAG) -c $(PRO_CLUSTER)
	kubectl apply -f k8s/pro

# ====================
# MONITORING
# ====================

monitoring:
	kubectl create namespace monitoring || true
	helm repo add prometheus-community https://prometheus-community.github.io/helm-charts || true
	helm repo update
	helm install monitoring prometheus-community/kube-prometheus-stack \
		--namespace monitoring || true

# ====================
# GRAFANA
# ====================

grafana:
	kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80

# ====================
# TESTS LOCALES
# ====================

test:
	pytest -v tests/test_probes.py

# --------------------
# PRO - Persistencia Postgres
# --------------------

.PHONY: pro-db-kill pro-db-wait pro-db-status

# Borra el pod de Postgres (simula caída)
pro-db-kill:
	@echo "💥 Borrando pod de Postgres en PRO..."
	kubectl delete pod -n pro -l app=postgres

# Espera a que Postgres vuelva a estar Ready
pro-db-wait:
	@echo "⏳ Esperando a que Postgres vuelva a estar Ready..."
	kubectl wait --for=condition=ready pod -n pro -l app=postgres --timeout=120s

# Muestra el estado actual de Postgres
pro-db-status:
	kubectl get pods -n pro -l app=postgres

