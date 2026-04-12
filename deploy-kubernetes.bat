@echo off
REM Deploy Agent Factory to Kubernetes
REM Prerequisites: minikube running, kubectl configured

echo =========================================
echo   Agent Factory - Kubernetes Deployment
echo =========================================
echo.

REM Step 1: Create namespace
echo [1/6] Creating namespace...
kubectl create namespace agent-factory --dry-run=client -o yaml | kubectl apply -f -

REM Step 2: Deploy Dapr components
echo [2/6] Deploying Dapr components...
kubectl apply -f infrastructure/dapr/components/ -n agent-factory
kubectl apply -f infrastructure/dapr/configurations/ -n agent-factory

REM Step 3: Deploy FTEs
echo [3/6] Deploying Digital FTEs...
kubectl apply -f infrastructure/kubernetes/deployments/ -n agent-factory

REM Step 4: Deploy Services
echo [4/6] Deploying services...
kubectl apply -f infrastructure/kubernetes/services/ -n agent-factory

REM Step 5: Verify deployment
echo [5/6] Verifying deployment...
kubectl get pods -n agent-factory
kubectl get services -n agent-factory

REM Step 6: Show status
echo.
echo [6/6] Deployment complete!
echo.
echo To check status:
echo   kubectl get pods -n agent-factory
echo   kubectl get services -n agent-factory
echo   kubectl logs -f deployment/customer-success-fte -n agent-factory
echo.
echo To access backend:
echo   kubectl port-forward svc/agent-factory-backend 8003:8003 -n agent-factory
echo.
pause
