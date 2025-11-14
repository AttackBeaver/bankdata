# Платформа аналитики Банка

## Общее описание

Платформа решает проблему этичного использования банковских данных, предоставляя клиентам полный контроль над их обезличенными данными, а бизнесу - доступ к качественной аналитике на основе реальных транзакций.

### Ключевые возможности

#### Для клиентов

- Просмотр и визуализация своих финансовых данных

- Полный контроль над согласием на использование данных

- Прозрачность - видно, кому и какие данные передаются

- Возможность отозвать согласие в любой момент

#### Для бизнес-партнеров

- Доступ к агрегированным обезличенным данным

- Аналитические дашборды и визуализации

- Сегментация данных по различным параметрам

- API для интеграции с аналитическими системами

## Архитектура системы

```text
bankdata/
├── api.py                 # FastAPI бэкенд
├── app.py                 # Streamlit фронтенд  
├── requirements.txt       # Зависимости
└── README.md             # Документация
```

### Технологический стек

- Frontend: Streamlit (Python)
- Backend: FastAPI (Python)
- Хранилище: In-memory структуры данных
- Визуализация: Plotly, Pandas
- Протокол: REST API over HTTP/JSON

### Схема взаимодействия

```txt
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   Streamlit     │    │   FastAPI API    │    │   Демо-данные    │
│   Web App       │◄──►│  (localhost:8000)│◄──►│   в памяти       │
│ (localhost:8501)│    │                  │    │                  │
└─────────────────┘    └──────────────────┘    └──────────────────┘
```

## Компоненты системы

### Backend API (FastAPI)

#### Модели данных

```txt
ClientProfile:

- client_id: str
- client_name: str  
- age_group: str
- city: str
- total_balance: float
- transactions: List[Transaction]

Transaction:

- id: str
- amount: float
- category: str
- date: str
- merchant: str

ConsentRequest:

- client_id: str
- company: str
- data_types: List[str]
- is_active: bool

AggregatedData:

- company: str
- data_type: str
- metrics: Dict
- sample_size: int
- generated_at: str
```

### 1. Импорты и настройка приложения

```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
import uuid

app = FastAPI(title="Bank Analytics Platform API", version="1.0.0")

# CORS для взаимодействия со Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### Как работает

- FastAPI() создает экземпляр веб-приложения с автоматической документацией

- CORSMiddleware разрешает кросс-доменные запросы от Streamlit фронтенда

- В продакшене allow_origins должен содержать конкретные домены вместо "*"

### 2. Модели данных Pydantic

```python
class Transaction(BaseModel):
    """Модель транзакции клиента"""
    id: str
    amount: float
    category: str
    date: str
    merchant: str

class ClientProfile(BaseModel):
    """Полный профиль клиента с транзакциями"""
    client_id: str
    client_name: str
    age_group: str
    city: str
    total_balance: float
    transactions: List[Transaction]

class ConsentRequest(BaseModel):
    """Запрос на согласие использования данных"""
    client_id: str
    company: str
    data_types: List[str]
    is_active: bool

class AggregatedData(BaseModel):
    """Агрегированные обезличенные данные"""
    company: str
    data_type: str
    metrics: Dict
    sample_size: int
    generated_at: str
```

#### Как работает

- Модели наследуются от BaseModel и автоматически валидируют данные

- FastAPI использует эти модели для генерации OpenAPI документации

- При несоответствии данных модели возвращается HTTP 422 ошибка

### 3. In-Memory базы данных

```python
# Демо-профили клиентов
client_profiles_db: Dict[str, ClientProfile] = {
    "client_1": ClientProfile(
        client_id="client_1",
        client_name="Иван Петров",
        age_group="25-35",
        city="Москва",
        total_balance=150000,
        transactions=[
            Transaction(id="t1", amount=2500, category="Рестораны", 
                       date="2024-01-15", merchant="Ресторан 'Вкусно'"),
            # ... другие транзакции
        ]
    ),
    # ... другие клиенты
}

# Активные согласия клиентов
consents_db: Dict[str, ConsentRequest] = {}

# Сгенерированные агрегированные данные
aggregated_data_db: Dict[str, AggregatedData] = {}
```

#### Как работает

- client_profiles_db - имитирует реальную базу данных банка

- consents_db - хранит активные согласия в формате {consent_id: ConsentRequest}

- aggregated_data_db - хранит готовые агрегированные данные для компаний

- В продакшене заменяются на PostgreSQL/MongoDB

### 4. Ключевые эндпоинты API

### Эндпоинт управления согласием

```python
@app.post("/consent")
async def manage_consent(consent_request: ConsentRequest):
    # Проверка существования клиента
    if consent_request.client_id not in client_profiles_db:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    
    # Валидация типов данных
    for data_type in consent_request.data_types:
        if data_type not in AVAILABLE_DATA_TYPES:
            raise HTTPException(status_code=400, detail=f"Неверный тип данных: {data_type}")
    
    # Создание уникального ID согласия
    consent_id = f"{consent_request.client_id}_{consent_request.company}"
    
    # Добавление временной метки
    consent_dict = consent_request.dict()
    consent_dict['last_updated'] = datetime.now().isoformat()
    
    # Сохранение согласия
    consents_db[consent_id] = ConsentRequest(**consent_dict)
    
    # Автоматическая генерация данных при активации
    if consent_request.is_active:
        await generate_aggregated_data(consent_request.client_id, consent_request.company)
    
    return {
        "message": "Согласие успешно обновлено", 
        "consent_id": consent_id,
        "consent": consents_db[consent_id]
    }
```

#### Логика работы

- Валидация: Проверяет существование клиента и корректность типов данных

- ID генерация: Создает уникальный ID на основе client_id и company

- Сохранение: Добавляет согласие в словарь consents_db

- Генерация данных: Если согласие активно, запускает процесс агрегации

- Ответ: Возвращает подтверждение и данные согласия

### Функция агрегации данных

```python
async def generate_aggregated_data(client_id: str, company: str):
    if client_id not in client_profiles_db:
        return
    
    client_profile = client_profiles_db[client_id]
    transactions = client_profile.transactions
    
    # Агрегация по категориям трат
    category_spending = {}
    for transaction in transactions:
        category = transaction.category
        if category not in category_spending:
            category_spending[category] = 0
        category_spending[category] += transaction.amount
    
    # Расчет среднего чека
    total_amount = sum(t.amount for t in transactions)
    average_bill = total_amount / len(transactions) if transactions else 0
    
    # Создание агрегированных данных
    data_key = f"{client_id}_{company}"
    
    # Данные по категориям трат
    aggregated_data_db[f"{data_key}_categories"] = AggregatedData(
        company=company,
        data_type="category_spending",
        metrics={
            "spending_by_category": category_spending,
            "top_category": max(category_spending, key=category_spending.get) if category_spending else "Нет данных",
            "total_categories": len(category_spending),
            "total_spent": total_amount
        },
        sample_size=1,
        generated_at=datetime.now().isoformat()
    )
    
    # ... аналогично для других типов данных
```

#### Процесс агрегации

- Извлечение данных: Получает транзакции из профиля клиента

- Группировка по категориям: Суммирует траты по каждой категории

- Статистические расчеты: Вычисляет средний чек, мин/макс значения

- Обезличивание: Сохраняет только статистические метрики без персональных данных

- Сохранение: Сохраняет агрегированные данные в отдельное хранилище

### Эндпоинт получения агрегированных данных

```python
@app.get("/aggregated-data/{company}")
async def get_aggregated_data(company: str):
    if company not in COMPANIES:
        raise HTTPException(status_code=400, detail="Компания не найдена")
    
    # Фильтрация данных по компании
    company_data = []
    for data_id, data in aggregated_data_db.items():
        if data.company == company:
            company_data.append(data)
    
    if not company_data:
        return {"message": "Нет доступных данных для этой компании", "data": []}
    
    return {
        "company": company,
        "total_datasets": len(company_data),
        "data": company_data
    }
```

#### Логика работы

- Проверка компании: Убеждается, что компания существует в white-list

- Фильтрация данных: Ищет все данные, связанные с этой компанией

- Формирование ответа: Возвращает структурированные данные с метаинформацией

## Рабочие процессы

### Процесс 1: Управление клиентским согласием

1. Клиент авторизуется в системе
2. Просматривает текущие согласия через GET /client/{id}/consents
3. Настраивает новое согласие: выбирает компанию и типы данных
4. Система сохраняет согласие через POST /consent
5. Автоматически генерируются агрегированные данные
6. Клиент получает подтверждение

### Процесс 2: Генерация агрегированных данных

- Данные группируются по категориям трат
- Удаляются все идентификаторы клиента
- Сохраняются только статистические метрики
- Исключается возможность обратной идентификации

## Безопасность и соответствие

### Меры безопасности

- Валидация всех входящих запросов
- Проверка прав доступа к данным компании
- Логирование всех операций с данными
- Строгое обезличивание перед передачей

### Соответствие ФЗ-152

- Явное согласие клиента на обработку
- Обезличивание перед передачей
- Право на отзыв согласия в любой момент
- Информирование о целях использования данных

## Установка и запуск

### Требования

- Python 3.8+
- 2 ГБ свободной памяти
- Порты 8000 и 8501 свободны

### Установка

```bash
# Создание виртуального окружения
python -m venv venv
venv\Scripts\activate     # Windows
```

## Установка зависимостей

```bash
pip install -r requirements.txt
```

### Запуск

```bash
# Терминал 1 - Запуск API
uvicorn api:app --reload --host 0.0.0.0 --port 8000

# Терминал 2 - Запуск веб-приложения  
streamlit run app.py
```

### Проверка

API: <http://localhost:8000>

Документация API: <http://localhost:8000/docs>

Веб-приложение: <http://localhost:8501>

Генерация демо-данных: кнопка в сайдбаре приложения
