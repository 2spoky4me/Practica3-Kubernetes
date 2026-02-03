# Práctica 3 – Kubernetes  
Asignatura: Redes Avanzadas  
Autor: Oriol Arderiu  

---

## 1. Introducción

Este proyecto corresponde a la **Práctica 3 de la asignatura Redes Avanzadas**.  
El objetivo es diseñar, desplegar y validar una **aplicación web en Kubernetes**, aplicando conceptos reales de arquitectura cloud, alta disponibilidad, persistencia, monitorización y automatización.

La aplicación está desarrollada en **Flask** y se ejecuta sobre **Kubernetes local (k3d)**.  
Se han definido **dos entornos diferenciados**:

- **DEV**: entorno de desarrollo simplificado
- **PRO**: entorno de producción con servicios adicionales

---

## 2. Requisitos previos

Es necesario tener instalados:

- Docker
- k3d
- kubectl
- helm
- make
- curl
- jq
- mc (MinIO Client)

---

## 3. Configuración obligatoria de /etc/hosts

Antes de desplegar el proyecto, es **imprescindible** añadir las siguientes entradas en `/etc/hosts`:

```txt
127.0.0.1 flask-dev.local
127.0.0.1 flask-pro.local
127.0.0.1 grafana-dev.local
127.0.0.1 grafana-pro.local
127.0.0.1 minio-pro.local
127.0.0.1 minio-api-pro.local
¿Por qué es necesario?
El proyecto utiliza Ingress con hostnames personalizados (virtual hosts).
Traefik enruta el tráfico en función del Host HTTP, no por IP ni por puerto.

Sin estas entradas:

El navegador no resolvería los dominios

Los Ingress no funcionarían correctamente

No se podría simular un entorno real de producción

Esta configuración permite:

Separar DEV y PRO por dominio

Simular un entorno real sin DNS externo

Cumplir buenas prácticas de Kubernetes

4. Estructura del proyecto
.
├── app/
│   ├── Dockerfile
│   ├── app.py
│   └── requirements.txt
│
├── k8s/
│   ├── dev/            # Manifiestos Kubernetes DEV
│   ├── pro/            # Manifiestos Kubernetes PRO
│   └── monitoring/     # Prometheus / Grafana
│
├── scripts/
│   ├── test-e2e.sh     # Tests End-to-End
│   └── cost-estimate.sh
│
├── tests/
│   └── test_probes.py  # Tests de probes
│
├── Makefile
├── README.md
└── logouib.png
5. Descripción de la aplicación
La aplicación web permite:

Insertar usuarios en una base de datos PostgreSQL

Listar usuarios

Mostrar información de estado del sistema

Endpoints expuestos
/live → Liveness Probe

/ready → Readiness Probe

/health → Estado general del sistema

/ → Interfaz web

/form → Inserción de datos

/list → Listado de usuarios

En producción, la aplicación además:

Cachea resultados con Redis

Sirve assets estáticos desde MinIO

Incluye monitorización con Prometheus y Grafana

6. Arquitectura del sistema
Entorno DEV
Flask (2 réplicas)

PostgreSQL (persistente)

Ingress (Traefik)

Entorno PRO
Flask (4 réplicas)

PostgreSQL (persistente)

Redis (cache)

MinIO (almacenamiento de ficheros)

Prometheus + Grafana (monitorización)

Ingress (Traefik)

Diagrama lógico (simplificado)
Usuario
  |
Ingress (Traefik)
  |
Flask (réplicas)
  |
PostgreSQL (PVC)
  |
Redis (solo PRO)
  |
MinIO (assets)
7. Despliegue del proyecto
Entorno DEV
make dev-cluster
make monitoring
make dev
Aplicación disponible en:
👉 http://flask-dev.local:8081

Entorno PRO
make pro-cluster
make monitoring
make prod
Aplicación disponible en:
👉 http://flask-pro.local:8082

8. Tests utilizados
8.1 Tests locales (probes)
Archivo: tests/test_probes.py

Valida:

/live

/ready

/health

Redis solo en PRO

Ejecución:

make test
Ejemplo de salida:

✔ /live OK
✔ /ready OK
✔ /health OK
8.2 Tests End-to-End
Script: scripts/test-e2e.sh

Valida automáticamente:

Número de réplicas desplegadas

Estado Ready de los pods

Balanceo de tráfico entre réplicas

Funcionamiento de MinIO (solo PRO)

Funcionamiento de Redis y TTL (solo PRO)

Correcto estado del endpoint /health

Ejecución:

make test-e2e-dev
make test-e2e-pro
Ejemplo de salida:

OK: 4 replicas Ready
Traffic distribution:
  flask-app-xxx -> 4 requests
  flask-app-yyy -> 6 requests
OK: MinIO file exists and is valid
OK: Redis cache working
OK: /health endpoint valid
9. Uso del Makefile
El Makefile centraliza toda la automatización del proyecto.

Comandos principales
make dev-cluster
make pro-cluster
make build
make dev
make prod
make monitoring
make test
make test-e2e-dev
make test-e2e-pro
make clean
Permite:

Crear y borrar clusters

Construir imágenes Docker

Desplegar entornos

Ejecutar tests

Simular fallos y recuperación

10. CI/CD
Se incluye un workflow de GitHub Actions que realiza:

Lint del código

Tests simulados

Build & push de la imagen Docker

Deploy simulado (instrucciones por consola)

El despliegue real se ejecuta en local, tal como se solicita en la práctica.

11. Conclusión
Con esta práctica se ha implementado una arquitectura Kubernetes realista, separando entornos, integrando servicios habituales (DB, cache, storage, monitoring) y validando el sistema mediante tests automáticos y end-to-end.

El proyecto demuestra:

Uso correcto de Kubernetes

Buenas prácticas de observabilidad

Automatización mediante Makefile

Validación funcional del sistema completo