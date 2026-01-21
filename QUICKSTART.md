# Data Governance Lakehouse - Complete Project Guide

This project is a **ready-to-run** end-to-end Data Engineering solution demonstrating:
 - ✅ Lakehouse Architecture
 - ✅ Data Governance with DAMA-DMBOK
 - ✅ Full ETL/ELT pipeline
 - ✅ Data Quality checks
 - ✅ Metadata & Lineage tracking
 - ✅ BI integration

---

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)

```bash
# On Windows (PowerShell)
python setup.py

# On Linux/Mac
python setup.py
```

### Вариант 2: Ручной setup

```bash
# 1. Перейти в каталог проекта
cd "Data Governance Lakehouse"

# 2. Создать .env файл
cp infra/env/.env.example infra/env/.env

# 3. Запустить все сервисы
cd infra
docker-compose up -d

# 4. Инициализировать БД
docker-compose exec postgres psql -U datauser -d datalakehouse < ../init_db.sql

# 5. Инициализировать Airflow
docker-compose exec airflow-webserver airflow db init

# 6. Создать admin пользователя для Airflow
docker-compose exec airflow-webserver airflow users create \
  --username admin \
  --password admin \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@example.com
```

### Вариант 3: Использование Makefile

```bash
# Все одной командой
make start

# Или пошагово
make up              # Запустить сервисы
make init-db         # Инициализировать БД
make airflow-init    # Инициализировать Airflow
```

---

## 🌐 Доступ к сервисам

После запуска, откройте в браузере:

| Сервис | URL | Учетные данные |
|--------|-----|-----------------|
| **Airflow** | http://localhost:8080 | admin / admin |
| **Metabase** | http://localhost:3000 | Создать при первом входе |
| **MinIO** | http://localhost:9001 | minioadmin / minioadmin |
| **PostgreSQL** | localhost:5432 | datauser / datapassword |

---

## 📊 Запуск pipeline

### 1. Включить DAGs в Airflow

```bash
# Перейти на http://localhost:8080
# Найти DAGs: data_ingestion_pipeline, dbt_transformation_pipeline
# Нажать на toggle, чтобы включить их
```

Или через CLI:
```bash
make airflow-unpause
```

### 2. Запустить ingestion DAG

```bash
# В веб-интерфейсе Airflow:
# DAGs → data_ingestion_pipeline → Trigger DAG

# Или через CLI:
docker-compose exec airflow-webserver airflow dags trigger data_ingestion_pipeline
```

### 3. Монитор выполнения

```bash
# Веб-интерфейс Airflow покажет прогресс
# Логи: http://localhost:8080/dags/data_ingestion_pipeline/grid

# Или через CLI:
make airflow-logs
```

### 4. Проверить данные в БД

```bash
make postgres-shell

# В интерактивной оболочке SQL:
\dt ods.*
\dt staging.*
\dt marts.*

SELECT * FROM ods.raw_events LIMIT 5;
SELECT * FROM staging.stg_earthquake_events LIMIT 5;
SELECT * FROM marts.fct_earthquake_metrics LIMIT 5;
```

---

## ✅ Проверка качества данных

```bash
# Запустить все quality checks
make quality-check

# Или напрямую:
python quality/data_quality_monitor.py
```

**Ожидаемый результат:**
```json
[
  {
    "check_type": "null_check",
    "table": "ods.raw_events",
    "column": "event_id",
    "null_count": 0,
    "status": "PASS"
  },
  {
    "check_type": "duplicate_check",
    "table": "ods.raw_events",
    "key_column": "event_id",
    "duplicate_count": 0,
    "status": "PASS"
  }
]
```

---

## 📈 Просмотр данных в Metabase

### 1. Подключить PostgreSQL

```
http://localhost:3000 → Settings → Admin Settings → Databases → Add database
- Name: Lakehouse
- Database: PostgreSQL
- Host: postgres
- Port: 5432
- Database: datalakehouse
- User: datauser
- Password: datapassword
```

### 2. Создать запрос

```
New → SQL query

SELECT 
  event_date,
  magnitude_category,
  event_count,
  avg_magnitude
FROM marts.fct_earthquake_metrics
ORDER BY event_date DESC
LIMIT 100;
```

### 3. Создать dashboard

```
+ Create → Dashboard → Add question
```

---

## 📁 Структура проекта

```
Data Governance Lakehouse/
├── airflow/                    # Orchestration
│   ├── dags/
│   │   ├── data_ingestion_pipeline.py    # Ingestion DAG
│   │   └── dbt_transformation_pipeline.py # Transformation DAG
│   ├── plugins/
│   │   └── quality_operators.py           # Custom operators
│   └── requirements.txt
│
├── dbt/                        # Transformations
│   ├── models/
│   │   ├── staging/           # stg_earthquake_events
│   │   ├── ods/               # dim_earthquake_events
│   │   └── marts/             # fct_earthquake_metrics
│   ├── tests/                 # dbt tests
│   ├── dbt_project.yml
│   └── profiles.yml
│
├── quality/                    # Data Quality
│   ├── data_quality_monitor.py
│   └── great_expectations/
│       ├── expectations.py
│       └── ge_config.yml
│
├── metadata/                   # Metadata & Lineage
│   └── openmetadata/
│       └── metadata_config.yaml
│
├── lakehouse/                  # Data storage zones
│   ├── raw/                   # Raw ingested data
│   ├── bronze/
│   ├── silver/
│   └── gold/
│
├── infra/                      # Infrastructure
│   ├── docker-compose.yml
│   └── env/
│       └── .env.example
│
├── docs/                       # Documentation
│   ├── architecture.md
│   ├── governance.md
│   └── data_dictionary.md
│
├── Dockerfile.airflow
├── Makefile
├── setup.py
├── init_db.sql
└── README.md
```

---

## 🛠️ Команды Makefile

```bash
make up              # Запустить все сервисы
make down            # Остановить сервисы
make restart         # Перезагрузить сервисы
make build           # Собрать Docker образы

make logs            # Просмотреть логи
make airflow-logs    # Логи только Airflow
make postgres-shell  # Подключиться к БД

make quality-check   # Проверить качество данных
make lineage-report  # Показать lineage

make dbt-run         # Запустить dbt модели
make dbt-test        # Запустить dbt тесты

make clean           # Удалить контейнеры и volumes
make start           # Полный setup и запуск
make help            # Показать все команды
```

---

## 📝 Data Pipeline Flow

### Этап 1: Ingestion (Bronze)
```python
USGS API
  ↓
Airflow fetch_earthquake_data()
  ↓
Parse JSON
  ↓
ods.raw_events (PostgreSQL)
```

**Данные:** 100-1000 событий/день
**Источник:** https://earthquake.usgs.gov
**Обновление:** Ежедневно в 02:00 UTC

### Этап 2: Cleaning (Silver)
```sql
-- staging.stg_earthquake_events
SELECT
  event_id,
  magnitude::FLOAT,
  place,
  latitude::FLOAT,
  longitude::FLOAT,
  depth::FLOAT,
  event_time::TIMESTAMP
FROM ods.raw_events
WHERE event_id IS NOT NULL
```

**Операции:**
- ✅ Извлечение из JSON
- ✅ Type casting
- ✅ Null checks
- ✅ Validation rules

### Этап 3: Normalization
```sql
-- ods.dim_earthquake_events
CREATE TABLE AS
SELECT
  MD5(event_id) AS event_sk,
  event_id,
  magnitude,
  place,
  ...
FROM staging.stg_earthquake_events
```

**Результат:** Normalized dimension table

### Этап 4: Aggregation (Gold)
```sql
-- marts.fct_earthquake_metrics
SELECT
  DATE(event_time) AS event_date,
  magnitude_category,
  COUNT(*) AS event_count,
  AVG(magnitude) AS avg_magnitude,
  MAX(magnitude) AS max_magnitude
FROM ods.dim_earthquake_events
GROUP BY 1, 2
```

**Для BI:** Metabase dashboards

---

## 🔍 Data Quality Framework

### Автоматические проверки

```python
# 1. Null checks
SELECT COUNT(*) FROM ods.raw_events 
WHERE event_id IS NULL  -- должен быть 0

# 2. Duplicate checks
SELECT COUNT(*) - COUNT(DISTINCT event_id) 
FROM ods.raw_events  -- должен быть 0

# 3. Range validation
SELECT COUNT(*) FROM staging.stg_earthquake_events
WHERE magnitude BETWEEN -2 AND 10  -- все должны быть в диапазоне

# 4. Freshness monitoring
SELECT COUNT(*) FROM ods.raw_events
WHERE ingested_at > NOW() - INTERVAL '24 hours'
-- должны быть последние 24 часа
```

### Результаты проверок

```sql
SELECT * FROM metadata.data_quality_checks
WHERE checked_at >= CURRENT_DATE
ORDER BY checked_at DESC;
```

---

## 🔐 Governance & Security

### Data Ownership

| Dataset | Owner | Контакт |
|---------|-------|---------|
| ods.raw_events | Data Engineering | data-eng@company.com |
| staging.stg_* | Data Engineering | data-eng@company.com |
| marts.fct_* | Analytics Engineering | analytics-eng@company.com |

### Access Control

```sql
-- Data Engineer (полный доступ)
GRANT SELECT, INSERT, UPDATE, DELETE 
ON ALL TABLES IN SCHEMA ods, staging, marts 
TO data_engineer;

-- Analyst (чтение marts)
GRANT SELECT ON ALL TABLES IN SCHEMA marts TO analyst;

-- Metabase (чтение all)
GRANT SELECT ON ALL TABLES IN SCHEMA ods, staging, marts TO metabase_user;
```

### Metadata & Lineage

```sql
-- Просмотреть lineage
SELECT * FROM metadata.data_lineage;

-- Качество данных
SELECT * FROM metadata.data_quality_checks 
WHERE checked_at >= CURRENT_DATE;

-- Ownership
SELECT * FROM metadata.dataset_ownership;
```

---

## 🐛 Troubleshooting

### Проблема: Airflow не запускается

```bash
# Проверить логи
make airflow-logs

# Перестартовать
make restart

# Очистить и пересоздать
make clean
make start
```

### Проблема: PostgreSQL не доступна

```bash
# Проверить статус
make ps

# Проверить logs
docker-compose logs postgres

# Перезапустить
docker-compose restart postgres
```

### Проблема: DAG не видно в Airflow

```bash
# Проверить, что файл в правильной папке
ls airflow/dags/

# Перезагрузить DAGs в Airflow
docker-compose exec airflow-webserver airflow dags reserialize

# Рестартовать scheduler
docker-compose restart airflow-scheduler
```

### Проблема: Данные не загружаются

```bash
# Проверить DAG логи в веб-интерфейсе
# Или:
docker-compose logs airflow-webserver

# Проверить БД напрямую
make postgres-shell
SELECT COUNT(*) FROM ods.raw_events;
```

---

## 📚 Документация

- **[Architecture](docs/architecture.md)** - Системная архитектура и компоненты
- **[Governance](docs/governance.md)** - Data governance framework (DAMA-DMBOK)
- **[Data Dictionary](docs/data_dictionary.md)** - Описание всех таблиц и колонок

---

## 🧪 Примеры запросов

### Найти последние землетрясения

```sql
SELECT 
  event_date,
  event_type,
  magnitude_category,
  event_count,
  avg_magnitude
FROM marts.fct_earthquake_metrics
WHERE event_date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY event_date DESC, event_count DESC;
```

### Проверить качество данных

```sql
SELECT 
  table_name,
  check_type,
  status,
  COUNT(*) as checks
FROM metadata.data_quality_checks
WHERE checked_at >= CURRENT_DATE
GROUP BY 1, 2, 3;
```

### Посмотреть lineage

```sql
SELECT 
  source_system,
  source_table,
  target_table,
  transformation_type,
  created_at
FROM metadata.data_lineage
ORDER BY created_at DESC;
```

---

## 🎯 Сценарии использования

### 1. Portfolio Demo (собеседования)
```
✅ Показать Airflow UI с DAGs
✅ Запустить pipeline перед интервью
✅ Показать данные в Metabase
✅ Объяснить governance framework
```

### 2. Training & Learning
```
✅ Разобрать каждый компонент
✅ Запустить пошагово
✅ Модифицировать под свои нужды
✅ Добавить новые данные
```

### 3. Reference Implementation
```
✅ Скопировать структуру в реальный проект
✅ Адаптировать DAGs под вашу БД
✅ Добавить свои качественные checks
✅ Расширить governance policies
```

---

## 📈 Следующие шаги

1. **Запустить pipeline**
   - `make start` или `python setup.py`
   - Проверить http://localhost:8080

2. **Исследовать данные**
   - Подключиться к PostgreSQL
   - Запросить из marts слоя
   - Посмотреть quality checks

3. **Создать BI**
   - Открыть Metabase
   - Создать вопросы и dashboard'ы
   - Поделиться инсайтами

4. **Кастомизировать**
   - Добавить свои источники данных
   - Расширить dbt модели
   - Добавить свои quality checks

5. **Развернуть**
   - Настроить production БД
   - Добавить оповещения
   - Настроить масштабирование

---

## 🤝 Контрибьютинг

Этот проект можно расширять:
- Добавить CDC потоковую обработку
- Добавить Machine Learning pipeline
- Расширить metadata management
- Добавить Advanced BI features

---

## 📄 Лицензия

MIT License

---

## 🆘 Помощь

### Документация в проекте
- `docs/architecture.md` - как все устроено
- `docs/governance.md` - governance policies
- `docs/data_dictionary.md` - описание всех таблиц

### Команды помощи
```bash
make help              # Все команды Makefile
docker-compose help    # Справка Docker Compose
airflow --help         # Справка Airflow
dbt --help             # Справка dbt
```

### Логирование
```bash
make logs              # Все сервисы
make airflow-logs      # Только Airflow
docker-compose logs -f # Детальные логи
```

---

## ⚡ Quick Reference

```bash
# Стартовать все
make start

# Посмотреть статус
make ps

# Запустить quality checks
make quality-check

# Подключиться к БД
make postgres-shell

# Посмотреть логи
make logs

# Очистить все
make clean

# Помощь
make help
```

---

**🎉 Проект готов к использованию! Выберите вариант запуска выше и начните.**

**Рекомендуемый путь:**
1. `python setup.py` - автоматический setup
2. Открыть http://localhost:8080 - Airflow
3. Включить DAGs и запустить pipeline
4. Проверить http://localhost:3000 - Metabase
5. Изучить документацию в docs/
