#!/bin/bash
set -e

echo "1. Installing ingress controller..."
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

echo "2. Waiting for ingress to be ready..."
kubectl wait --namespace ingress-nginx --for=condition=ready pod --selector=app.kubernetes.io/component=controller --timeout=90s

echo "3. Pinning ingress to control-plane node..."
kubectl patch deployment ingress-nginx-controller -n ingress-nginx --type='json' \
  -p='[{"op":"add","path":"/spec/template/spec/nodeSelector","value":{"kubernetes.io/hostname":"scholarrag-control-plane"}}]'

echo "4. Creating secrets..."
kubectl create secret generic scholarrag-secret --from-env-file=/home/ubuntu/.env

echo "5. Applying manifests..."
kubectl apply -f ~/k8s/qdrant-deployment.yaml
kubectl apply -f ~/k8s/backend-deployment.yaml
kubectl apply -f ~/k8s/frontend-deployment.yaml
kubectl apply -f ~/k8s/ingress.yaml

echo "Done! Run: kubectl get pods"
