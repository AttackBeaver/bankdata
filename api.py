from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
import uuid

app = FastAPI(title="Bank Analytics Platform API", version="1.0.0")

# Разрешаем CORS для взаимодействия со Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== МОДЕЛИ PYDANTIC =====

class Transaction(BaseModel):
    """Модель транзакции"""
    id: str
    amount: float
    category: str
    date: str
    merchant: str

class ClientProfile(BaseModel):
    """Модель профиля клиента"""
    client_id: str
    client_name: str
    age_group: str
    city: str
    total_balance: float
    transactions: List[Transaction]

class ConsentRequest(BaseModel):
    """Модель запроса на согласие"""
    client_id: str
    company: str
    data_types: List[str]
    is_active: bool

class AggregatedData(BaseModel):
    """Модель агрегированных данных"""
    company: str
    data_type: str
    metrics: Dict
    sample_size: int
    generated_at: str

# ===== "БАЗА ДАННЫХ" В ПАМЯТИ =====

# Профили клиентов с транзакциями
client_profiles_db: Dict[str, ClientProfile] = {
    "client_1": ClientProfile(
        client_id="client_1",
        client_name="Иван Петров",
        age_group="25-35",
        city="Москва",
        total_balance=150000,
        transactions=[
            Transaction(id="t1", amount=2500, category="Рестораны", date="2024-01-15", merchant="Ресторан 'Вкусно'"),
            Transaction(id="t2", amount=5000, category="Супермаркеты", date="2024-01-14", merchant="Пятерочка"),
            Transaction(id="t3", amount=12000, category="Электроника", date="2024-01-10", merchant="М.Видео"),
            Transaction(id="t4", amount=3500, category="Транспорт", date="2024-01-08", merchant="Яндекс.Такси"),
            Transaction(id="t5", amount=8000, category="Развлечения", date="2024-01-05", merchant="Кинотеатр"),
        ]
    ),
    "client_2": ClientProfile(
        client_id="client_2",
        client_name="Мария Сидорова",
        age_group="35-45",
        city="Санкт-Петербург",
        total_balance=280000,
        transactions=[
            Transaction(id="t6", amount=15000, category="Одежда", date="2024-01-16", merchant="ZARA"),
            Transaction(id="t7", amount=7000, category="Красота", date="2024-01-15", merchant="Л'Этуаль"),
            Transaction(id="t8", amount=4500, category="Кафе", date="2024-01-12", merchant="Starbucks"),
            Transaction(id="t9", amount=20000, category="Путешествия", date="2024-01-05", merchant="Aeroflot"),
            Transaction(id="t10", amount=3000, category="Фитнес", date="2024-01-03", merchant="World Class"),
        ]
    ),
    "client_3": ClientProfile(
        client_id="client_3",
        client_name="Алексей Козлов",
        age_group="18-25",
        city="Новосибирск",
        total_balance=50000,
        transactions=[
            Transaction(id="t11", amount=1500, category="Фастфуд", date="2024-01-17", merchant="McDonald's"),
            Transaction(id="t12", amount=8000, category="Электроника", date="2024-01-15", merchant="DNS"),
            Transaction(id="t13", amount=2000, category="Образование", date="2024-01-10", merchant="Coursera"),
            Transaction(id="t14", amount=1000, category="Транспорт", date="2024-01-08", merchant="Яндекс.Карты"),
            Transaction(id="t15", amount=4000, category="Развлечения", date="2024-01-05", merchant="Steam"),
        ]
    )
}

# База согласий клиентов
consents_db: Dict[str, ConsentRequest] = {}

# База агрегированных данных
aggregated_data_db: Dict[str, AggregatedData] = {}

# Список компаний-партнеров
COMPANIES = [
    "Retail Analytics Pro",
    "FinTech Insights", 
    "Market Research Co",
    "Consumer Trends Lab"
]

# Доступные типы данных для согласия
AVAILABLE_DATA_TYPES = [
    "category_spending",
    "average_bill", 
    "spending_frequency",
    "geography",
    "age_group_stats"
]

# ===== БАЗОВЫЕ ЭНДПОИНТЫ =====

@app.get("/health")
async def health_check():
    """Проверка работоспособности API"""
    return {"status": "OK", "message": "Bank Analytics Platform API is running"}

@app.get("/clients")
async def get_available_clients():
    """Получить список доступных клиентов (для демо)"""
    return list(client_profiles_db.keys())

@app.get("/companies")
async def get_available_companies():
    """Получить список компаний-партнеров"""
    return COMPANIES

@app.get("/data-types")
async def get_available_data_types():
    """Получить доступные типы данных"""
    return AVAILABLE_DATA_TYPES

# ===== КЛЮЧЕВЫЕ ФУНКЦИОНАЛЬНЫЕ ЭНДПОИНТЫ =====

@app.get("/client/{client_id}")
async def get_client_profile(client_id: str):
    """Получить профиль клиента (для демо-показа)"""
    if client_id not in client_profiles_db:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    return client_profiles_db[client_id]

@app.get("/client/{client_id}/consents")
async def get_client_consents(client_id: str):
    """Получить все согласия конкретного клиента"""
    client_consents = []
    for consent_id, consent in consents_db.items():
        if consent.client_id == client_id:
            client_consents.append({
                "consent_id": consent_id,
                "company": consent.company,
                "data_types": consent.data_types,
                "is_active": consent.is_active,
                "last_updated": getattr(consent, 'last_updated', None)
            })
    return client_consents

@app.post("/consent")
async def manage_consent(consent_request: ConsentRequest):
    """Управление согласием клиента (дать/отозвать/изменить)"""
    
    # Проверяем существование клиента
    if consent_request.client_id not in client_profiles_db:
        raise HTTPException(status_code=404, detail="Клиент не найден")
    
    # Проверяем валидность типов данных
    for data_type in consent_request.data_types:
        if data_type not in AVAILABLE_DATA_TYPES:
            raise HTTPException(status_code=400, detail=f"Неверный тип данных: {data_type}")
    
    # Создаем уникальный ID для согласия
    consent_id = f"{consent_request.client_id}_{consent_request.company}"
    
    # Добавляем временную метку
    consent_dict = consent_request.dict()
    consent_dict['last_updated'] = datetime.now().isoformat()
    
    # Сохраняем или обновляем согласие
    consents_db[consent_id] = ConsentRequest(**consent_dict)
    
    # Автоматически генерируем агрегированные данные при активации согласия
    if consent_request.is_active:
        await generate_aggregated_data(consent_request.client_id, consent_request.company)
    
    return {
        "message": "Согласие успешно обновлено", 
        "consent_id": consent_id,
        "consent": consents_db[consent_id]
    }

@app.delete("/consent/{consent_id}")
async def revoke_consent(consent_id: str):
    """Полностью отозвать согласие"""
    if consent_id in consents_db:
        del consents_db[consent_id]
        
        # Удаляем соответствующие агрегированные данные
        company = consent_id.split('_')[-1]
        data_key = f"{consent_id}_aggregated"
        if data_key in aggregated_data_db:
            del aggregated_data_db[data_key]
            
        return {"message": "Согласие полностью отозвано"}
    else:
        raise HTTPException(status_code=404, detail="Согласие не найдено")

@app.get("/aggregated-data/{company}")
async def get_aggregated_data(company: str):
    """Получить агрегированные данные для компании"""
    if company not in COMPANIES:
        raise HTTPException(status_code=400, detail="Компания не найдена")
    
    # Фильтруем данные по компании
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

# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====

async def generate_aggregated_data(client_id: str, company: str):
    """Генерация агрегированных данных на основе профиля клиента"""
    
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
    
    # Частота трат (по дням)
    unique_dates = len(set(t.date for t in transactions))
    
    # Создаем агрегированные данные
    data_key = f"{client_id}_{company}_aggregated"
    
    # Данные по категориям трат
    aggregated_data_db[f"{data_key}_categories"] = AggregatedData(
        company=company,
        data_type="category_spending",
        metrics={
            "spending_by_category": category_spending,
            "top_category": max(category_spending, key=category_spending.get) if category_spending else "Нет данных",
            "total_categories": len(category_spending)
        },
        sample_size=1,  # В демо - 1 клиент, в реальности - N клиентов
        generated_at=datetime.now().isoformat()
    )
    
    # Данные по среднему чеку
    aggregated_data_db[f"{data_key}_average"] = AggregatedData(
        company=company,
        data_type="average_bill",
        metrics={
            "average_transaction_amount": round(average_bill, 2),
            "min_amount": min(t.amount for t in transactions) if transactions else 0,
            "max_amount": max(t.amount for t in transactions) if transactions else 0,
            "total_transactions": len(transactions)
        },
        sample_size=1,
        generated_at=datetime.now().isoformat()
    )
    
    # Демографические данные (обезличенные)
    aggregated_data_db[f"{data_key}_demographics"] = AggregatedData(
        company=company,
        data_type="age_group_stats",
        metrics={
            "age_group": client_profile.age_group,
            "city": client_profile.city,
            "average_balance": client_profile.total_balance
        },
        sample_size=1,
        generated_at=datetime.now().isoformat()
    )

@app.get("/debug/consents")
async def debug_consents():
    """Отладочный эндпоинт для просмотра всех согласий"""
    return consents_db

@app.get("/debug/aggregated")
async def debug_aggregated():
    """Отладочный эндпоинт для просмотра агрегированных данных"""
    return aggregated_data_db

@app.get("/demo-data")
async def get_demo_data():
    """Генерация демо-данных для быстрого тестирования"""
    # Создаем несколько согласий для демонстрации
    demo_consents = [
        {
            "client_id": "client_1",
            "company": "Retail Analytics Pro",
            "data_types": ["category_spending", "average_bill", "age_group_stats"],
            "is_active": True
        },
        {
            "client_id": "client_2", 
            "company": "Retail Analytics Pro",
            "data_types": ["category_spending", "age_group_stats"],
            "is_active": True
        },
        {
            "client_id": "client_3",
            "company": "FinTech Insights",
            "data_types": ["category_spending", "average_bill"],
            "is_active": True
        }
    ]
    
    for consent_data in demo_consents:
        consent_id = f"{consent_data['client_id']}_{consent_data['company']}"
        consent_data['last_updated'] = datetime.now().isoformat()
        consents_db[consent_id] = ConsentRequest(**consent_data)
        await generate_aggregated_data(consent_data['client_id'], consent_data['company'])
    
    return {"message": "Демо-данные успешно созданы", "consents_created": len(demo_consents)}

# Улучшим функцию агрегации для работы с несколькими клиентами
async def generate_aggregated_data(client_id: str, company: str):
    """Генерация агрегированных данных на основе профиля клиента"""
    
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
    
    # Создаем агрегированные данные
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
    
    # Данные по среднему чеку
    aggregated_data_db[f"{data_key}_average"] = AggregatedData(
        company=company,
        data_type="average_bill", 
        metrics={
            "average_transaction_amount": round(average_bill, 2),
            "min_amount": min(t.amount for t in transactions) if transactions else 0,
            "max_amount": max(t.amount for t in transactions) if transactions else 0,
            "total_transactions": len(transactions),
            "total_amount": total_amount
        },
        sample_size=1,
        generated_at=datetime.now().isoformat()
    )
    
    # Демографические данные (обезличенные)
    aggregated_data_db[f"{data_key}_demographics"] = AggregatedData(
        company=company,
        data_type="age_group_stats",
        metrics={
            "age_group": client_profile.age_group,
            "city": client_profile.city,
            "average_balance": client_profile.total_balance,
            "client_count": 1
        },
        sample_size=1,
        generated_at=datetime.now().isoformat()
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    
