#!/bin/bash
# deployment.sh - Builds and deploys the JSON transformation service to Kubernetes

set -e

echo "Building Docker image..."
docker build -t json-transform-service:latest .

echo "Tagging image for your registry..."
# Replace with your actual registry
REGISTRY="your-registry.example.com"
docker tag json-transform-service:latest ${REGISTRY}/json-transform-service:latest

echo "Pushing image to registry..."
# Uncomment to push to your registry
# docker push ${REGISTRY}/json-transform-service:latest

echo "Applying Kubernetes manifests..."
kubectl apply -f kubernetes.yaml

echo "Waiting for deployment to complete..."
kubectl rollout status deployment/json-transform-service

echo "Deployment completed successfully!"
echo "Service is available at: http://$(kubectl get service json-transform-service -o jsonpath='{.status.loadBalancer.ingress[0].ip}')"
