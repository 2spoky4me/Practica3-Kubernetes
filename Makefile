CLUSTER_NAME=prac3
LB_PORT=8081

.PHONY: clean cluster build dev prod monitoring grafana

# --------------------
# CLEAN: borra TODO el clúster
# --------------------
clean:
	k3d cluster delete $(CLUSTER_NAME) || true

# --------------------
# CLUSTER: crea el clúster una sola vez
# --------------------
cluster:
	k3d cluster create $(CLUSTER_NAME) -p "$(LB_PORT):80@loadbalancer" || true

# --------------------
# BUILD: construye la imagen Docker
# --------------------
build:
	docker build -t flask-app:prac3 app

# --------------------
# DEV: despliega SOLO el entorno dev
# --------------------
dev: build
	kubectl create namespace dev || true
	k3d image import flask-app:prac3 -c $(CLUSTER_NAME)
	kubectl apply -f k8s/dev

# --------------------
# PROD: despliega SOLO el entorno pro
# --------------------
prod: build
	kubectl create namespace pro || true
	k3d image import flask-app:prac3 -c $(CLUSTER_NAME)
	kubectl apply -f k8s/pro

# --------------------
# MONITORING
# --------------------
monitoring:
	kubectl create namespace monitoring || true
	helm repo add prometheus-community https://prometheus-community.github.io/helm-charts || true
	helm repo update
	helm install monitoring prometheus-community/kube-prometheus-stack \
		--namespace monitoring || true

# --------------------
# GRAFANA
# --------------------
grafana:
	kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80
