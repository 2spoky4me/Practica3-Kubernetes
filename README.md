# Práctica 3 – Despliegue de Aplicaciones con Kubernetes

## Descripción
Esta práctica consiste en el despliegue de una aplicación web desarrollada en Flask sobre Kubernetes, utilizando un clúster local con k3d.  
La solución implementa separación de entornos (desarrollo y producción), alta disponibilidad, monitorización, health-checks y automatización del despliegue.
# Práctica 3 – Despliegue de Aplicaciones con Kubernetes

## Descripción
Esta práctica consiste en el despliegue de una aplicación web desarrollada en Flask sobre Kubernetes, utilizando un clúster local con **k3d**.  
La solución implementa separación de entornos (desarrollo y producción), alta disponibilidad, monitorización, health-checks y automatización del despliegue.

El objetivo es simular un entorno real de despliegue cloud empleando herramientas habituales en entornos **DevOps**.

---

## Arquitectura

- **Clúster Kubernetes**: k3d (nombre del clúster: `prac3`)
- **Namespaces**:
  - `dev` → entorno de desarrollo
  - `pro` → entorno de producción
  - `monitoring` → monitorización
- **Aplicación web**: Flask
- **Base de datos**: PostgreSQL
- **Caché**: Redis (solo en producción)
- **Ingress Controller**: Traefik
- **Monitorización**: Prometheus + Grafana
- **Automatización**: Makefile
- **CI/CD**: GitHub Actions

---

## Requisitos previos

Antes de comenzar, es necesario tener instaladas las siguientes herramientas:

- Docker
- kubectl
- k3d
- helm
- make
- git

El proyecto ha sido desarrollado y probado en **Linux / WSL** con **Docker Desktop**.

---

## Clonar el repositorio

```bash
git clone https://github.com/2spoky4me/Practica3-Kubernetes.git
cd Practica3-Kubernetes
Configuración DNS local
Para poder acceder a la aplicación mediante Ingress, es necesario modificar el archivo hosts del sistema.

En Windows, editar el archivo:

makefile
Copiar código
C:\Windows\System32\drivers\etc\hosts
Añadir las siguientes líneas:

lua
Copiar código
127.0.0.1 flask-dev.local
127.0.0.1 flask-pro.local
Despliegue completo desde cero
1. Limpiar cualquier estado previo
Este paso elimina completamente el clúster Kubernetes si existiera previamente.

bash
Copiar código
make clean
2. Crear el clúster Kubernetes
bash
Copiar código
make cluster
Este comando crea un clúster k3d llamado prac3 y expone el LoadBalancer en el puerto 8081.

Despliegue de entornos
Entorno de producción
bash
Copiar código
make prod
Este comando realiza:

Construcción de la imagen Docker de la aplicación

Importación de la imagen al clúster

Creación del namespace pro

Despliegue de la aplicación Flask, PostgreSQL y Redis

Configuración del Ingress de producción

Acceso a la aplicación:

arduino
Copiar código
http://flask-pro.local:8081
Entorno de desarrollo
bash
Copiar código
make dev
Este comando realiza:

Despliegue del entorno de desarrollo en el namespace dev

Despliegue de la aplicación Flask y PostgreSQL

Redis no se utiliza en este entorno

Menor número de réplicas que en producción

Acceso a la aplicación:

arduino
Copiar código
http://flask-dev.local:8081
Los entornos dev y pro pueden estar levantados simultáneamente dentro del mismo clúster gracias al uso de namespaces.

Health-checks
La aplicación expone el endpoint:

bash
Copiar código
/status
Este endpoint:

Devuelve el estado de la aplicación

Es utilizado por Kubernetes como livenessProbe y readinessProbe

Ejemplo de acceso:

bash
Copiar código
http://flask-pro.local:8081/status
Alta disponibilidad
DEV: 2 réplicas de la aplicación

PRO: 4 réplicas de la aplicación

El balanceo de carga se realiza automáticamente mediante Kubernetes Service e Ingress.
Cada petición puede ser atendida por una réplica distinta, lo que se puede comprobar refrescando la página y observando el identificador de instancia.

Redis
Redis solo está desplegado en el entorno de producción

En producción, la aplicación utiliza Redis como sistema de caché

En desarrollo, Redis no se utiliza

Esto permite diferenciar claramente el comportamiento entre ambos entornos.

Monitorización
Despliegue del stack de monitorización
bash
Copiar código
make monitoring
Este comando despliega Prometheus, Grafana y Alertmanager en el namespace monitoring.

Acceso a Grafana
bash
Copiar código
make grafana
Acceso vía navegador:

arduino
Copiar código
http://localhost:3000
Usuario por defecto:

nginx
Copiar código
admin
Para obtener la contraseña de Grafana:

bash
Copiar código
kubectl get secret -n monitoring monitoring-grafana \
  -o jsonpath="{.data.admin-password}" | base64 -d
En Grafana se pueden visualizar métricas como:

Uso de CPU de los pods

Uso de memoria

Estado de las réplicas

Estado general del clúster

Automatización
El proyecto incluye un Makefile que permite:

Crear y eliminar el clúster Kubernetes

Desplegar los entornos dev y pro de forma independiente

Levantar el stack de monitorización

Acceder fácilmente a Grafana

Esto permite repetir el despliegue de forma reproducible y controlada.

CI/CD
El repositorio incluye un workflow de GitHub Actions que:

Se ejecuta automáticamente en cada push

Ejecuta tests básicos de la aplicación

Verifica el correcto funcionamiento del endpoint /status

Simula un pipeline de integración continua

Autor
Oriol Arderi
