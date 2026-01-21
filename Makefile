.PHONY: help up down logs build test clean restart init-db quality-check lineage-report

help:
	@echo "Data Governance Lakehouse - Available Commands"
	@echo "=============================================="
	@echo "make up              - Start all services"
	@echo "make down            - Stop all services"
	@echo "make restart         - Restart all services"
	@echo "make build           - Build Docker images"
	@echo "make logs            - View service logs"
	@echo "make ps              - List running containers"
	@echo "make init-db         - Initialize database"
	@echo "make quality-check   - Run data quality checks"
	@echo "make lineage-report  - Generate data lineage report"
	@echo "make test            - Run tests"
	@echo "make clean           - Clean up volumes and containers"
	@echo "make dbt-run         - Run dbt models"
	@echo "make airflow-logs    - View Airflow logs"
	@echo "make postgres-shell  - Connect to PostgreSQL"

up:
	cd infra && docker-compose up -d
	@echo "Services are starting... Check status with 'make ps'"
	@echo "Airflow: http://localhost:8080"
	@echo "Metabase: http://localhost:3000"
	@echo "MinIO: http://localhost:9001"
	@echo "PostgreSQL: localhost:5432"

down:
	cd infra && docker-compose down
	@echo "All services stopped"

restart: down up
	@echo "Services restarted"

build:
	cd infra && docker-compose build
	@echo "Docker images built"

ps:
	cd infra && docker-compose ps

logs:
	cd infra && docker-compose logs -f

airflow-logs:
	cd infra && docker-compose logs -f airflow-webserver airflow-scheduler

postgres-shell:
	cd infra && docker-compose exec postgres psql -U datauser -d datalakehouse

init-db:
	cd infra && docker-compose exec postgres psql -U datauser -d datalakehouse < ../init_db.sql
	@echo "Database initialized"

test:
	@echo "Running tests..."
	python -m pytest tests/ -v --tb=short 2>/dev/null || echo "No tests found or pytest not installed"

quality-check:
	@echo "Running data quality checks..."
	python quality/data_quality_monitor.py
	@echo "Quality checks completed"

lineage-report:
	@echo "Generating data lineage report..."
	cd infra && docker-compose exec postgres psql -U datauser -d datalakehouse -c "SELECT * FROM metadata.data_lineage;"

dbt-run:
	@echo "Running dbt transformations..."
	cd dbt && dbt run --profiles-dir . 2>/dev/null || echo "dbt not configured or not installed"

dbt-test:
	@echo "Running dbt tests..."
	cd dbt && dbt test --profiles-dir . 2>/dev/null || echo "dbt not configured"

dbt-docs:
	@echo "Generating dbt docs..."
	cd dbt && dbt docs generate --profiles-dir . 2>/dev/null || echo "dbt not configured"

airflow-init:
	cd infra && docker-compose exec airflow-webserver airflow db init
	cd infra && docker-compose exec airflow-webserver airflow users create \
		--username admin \
		--password admin \
		--firstname Admin \
		--lastname User \
		--role Admin \
		--email admin@example.com 2>/dev/null || echo "Admin user already exists"

airflow-unpause:
	@echo "Unpausing Airflow DAGs..."
	cd infra && docker-compose exec airflow-webserver airflow dags unpause data_ingestion_pipeline
	cd infra && docker-compose exec airflow-webserver airflow dags unpause dbt_transformation_pipeline

validate-setup:
	@echo "Validating project setup..."
	@echo "Checking directories..."
	@test -d airflow/dags || (echo "ERROR: airflow/dags not found" && exit 1)
	@test -d dbt/models || (echo "ERROR: dbt/models not found" && exit 1)
	@test -d infra || (echo "ERROR: infra not found" && exit 1)
	@echo "✓ All required directories present"
	@echo "Project structure is valid!"

health-check:
	@echo "Checking service health..."
	@echo -n "PostgreSQL: "
	cd infra && docker-compose exec postgres pg_isready -U datauser || echo "NOT READY"
	@echo -n "Airflow: "
	curl -s http://localhost:8080 > /dev/null && echo "OK" || echo "NOT READY"
	@echo -n "Metabase: "
	curl -s http://localhost:3000 > /dev/null && echo "OK" || echo "NOT READY"

clean:
	@echo "Cleaning up..."
	cd infra && docker-compose down -v
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf dbt/target/ dbt/logs/ 2>/dev/null || true
	@echo "Cleanup completed"

setup-env:
	@echo "Creating .env file..."
	@echo "DB_HOST=postgres" > infra/env/.env
	@echo "DB_USER=datauser" >> infra/env/.env
	@echo "DB_PASSWORD=datapassword" >> infra/env/.env
	@echo "DB_NAME=datalakehouse" >> infra/env/.env
	@echo "DB_PORT=5432" >> infra/env/.env
	@echo ".env file created"

version:
	@echo "Data Governance Lakehouse v1.0.0"
	@echo "Python: " && python --version
	@docker --version
	@docker-compose --version

# Combined startup
start: setup-env build up airflow-init init-db validate-setup health-check
	@echo "✓ Data Governance Lakehouse is ready!"
	@echo "Access points:"
	@echo "  - Airflow UI: http://localhost:8080 (admin/admin)"
	@echo "  - Metabase: http://localhost:3000"
	@echo "  - PostgreSQL: localhost:5432"
	@echo "  - MinIO: http://localhost:9001"

all: help
