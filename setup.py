"""
Quick start setup script for Data Governance Lakehouse
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Run a shell command and report status"""
    print(f"\n{'='*60}")
    print(f"▶ {description}")
    print(f"{'='*60}")
    print(f"$ {cmd}")
    
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"⚠ Warning: {description} had issues")
        return False
    return True

def main():
    """Main setup sequence"""
    print("\n" + "="*60)
    print("🚀 Data Governance Lakehouse - Quick Start Setup")
    print("="*60)
    
    # Check prerequisites
    print("\n📋 Checking prerequisites...")
    
    checks = [
        ("docker", "Docker"),
        ("docker-compose", "Docker Compose"),
        ("python", "Python 3"),
    ]
    
    for cmd, name in checks:
        try:
            subprocess.run(f"{cmd} --version", shell=True, capture_output=True, check=True)
            print(f"✓ {name} is installed")
        except subprocess.CalledProcessError:
            print(f"✗ {name} is NOT installed")
            print(f"  Please install {name} and try again")
            sys.exit(1)
    
    # Setup steps
    steps = [
        ("python -m pip install --upgrade pip", "Upgrading pip"),
        ("docker-compose --version", "Verifying Docker Compose"),
        ("cd infra && docker-compose down -v 2>/dev/null || true", "Cleaning previous setup"),
        ("cd infra && docker-compose build", "Building Docker images"),
        ("cd infra && docker-compose up -d", "Starting services"),
        ("sleep 30", "Waiting for services to initialize"),
        ("cd infra && docker-compose exec -T postgres psql -U datauser -d datalakehouse < ../init_db.sql", "Initializing database"),
        ("cd infra && docker-compose exec -T airflow-webserver airflow db init", "Initializing Airflow DB"),
    ]
    
    for cmd, desc in steps:
        if not run_command(cmd, desc):
            if "optional" in desc.lower():
                continue
            else:
                print(f"\n❌ Setup failed at: {desc}")
                sys.exit(1)
    
    # Post-setup info
    print("\n" + "="*60)
    print("✅ Setup Complete!")
    print("="*60)
    
    print("\n🌐 Service URLs:")
    print("  • Airflow UI: http://localhost:8080")
    print("    Username: admin, Password: admin")
    print("  • Metabase: http://localhost:3000")
    print("  • MinIO: http://localhost:9001")
    print("    Access Key: minioadmin, Secret: minioadmin")
    print("  • PostgreSQL: localhost:5432")
    print("    User: datauser, Password: datapassword")
    
    print("\n📚 Next Steps:")
    print("  1. Create an Airflow admin user (if not auto-created)")
    print("  2. Trigger the data_ingestion_pipeline DAG")
    print("  3. Monitor pipeline progress in Airflow UI")
    print("  4. Check data quality in metadata tables")
    print("  5. Build dashboards in Metabase")
    
    print("\n💡 Useful Commands:")
    print("  make logs                - View service logs")
    print("  make quality-check       - Run data quality checks")
    print("  make postgres-shell      - Connect to PostgreSQL")
    print("  make clean               - Clean everything")
    print("  make help                - Show all available commands")
    
    print("\n📖 Documentation:")
    print("  • Architecture: docs/architecture.md")
    print("  • Governance: docs/governance.md")
    print("  • Data Dictionary: docs/data_dictionary.md")
    print("\n")

if __name__ == "__main__":
    main()
