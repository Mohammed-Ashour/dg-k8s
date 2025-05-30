.PHONY: install-core install-dev install format build deploy clean

install-core:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

install:
	make install-core
	make install-dev
	@echo "All dependencies installed successfully."

format:
	ruff check --fix

populate_db:
	python -m src.init_data.populate_db
	@echo "Database populated successfully."

up_local:
	dagster dev

create_k8s_namespace:
	kubectl create namespace dagster

clean_k8s:
	kubectl delete namespace dagster --ignore-not-found


forward_k8s:
	@echo "Port forwarding to service dg-k8s-service on port 3002"
	kubectl port-forward service/dagster-webserver 3002:3000 -n dagster
	
build_docker:
	docker build -t dg-k8s:latest .
	minikube image load dg-k8s:latest

check_pod_status:
	kubectl get pods -n dagster
	@echo "Check the status of the pods in the dagster namespace"

check_deamon_logs:
	kubectl logs -f deployment/dagster-daemon -n dagster
	@echo "Check the logs of the dagster-daemon deployment in the dagster namespace"

rebuild_k8s: 
	make clean_k8s
	make create_k8s_namespace
	make build_docker
	make apply_k8s
	make check_pod_status


deploy: clean
	kubectl apply -f deployment/k8s/storage.yaml
	kubectl apply -f deployment/k8s/dagster-webserver.yaml
	kubectl apply -f deployment/k8s/dagster-daemon.yaml
	kubectl get pods -n dagster


logs-webserver:
	kubectl logs -f deployment/dagster-webserver -n dagster

logs-daemon:
	kubectl logs -f deployment/dagster-daemon -n dagster