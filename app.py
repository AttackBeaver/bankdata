import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

st.set_page_config(
    page_title="Платформа аналитики Банка",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# URL API
API_BASE = "http://localhost:8000"

@st.cache_data(ttl=60)  # Кэш на 60 секунд
def check_api_health():
    """Проверка подключения к API"""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

@st.cache_data(ttl=120)
def get_clients():
    """Получить список клиентов"""
    try:
        response = requests.get(f"{API_BASE}/clients", timeout=5)
        return response.json() if response.status_code == 200 else []
    except:
        return []

@st.cache_data(ttl=120)
def get_companies():
    """Получить список компаний"""
    try:
        response = requests.get(f"{API_BASE}/companies", timeout=5)
        return response.json() if response.status_code == 200 else []
    except:
        return []

@st.cache_data(ttl=120)
def get_data_types():
    """Получить типы данных"""
    try:
        response = requests.get(f"{API_BASE}/data-types", timeout=5)
        return response.json() if response.status_code == 200 else []
    except:
        return []

@st.cache_data(ttl=30)
def get_client_consents(client_id):
    """Получить согласия клиента"""
    try:
        response = requests.get(f"{API_BASE}/client/{client_id}/consents", timeout=5)
        return response.json() if response.status_code == 200 else []
    except:
        return []

@st.cache_data(ttl=30)
def get_client_profile(client_id):
    """Получить профиль клиента"""
    try:
        response = requests.get(f"{API_BASE}/client/{client_id}", timeout=5)
        return response.json() if response.status_code == 200 else None
    except:
        return None

@st.cache_data(ttl=30)
def get_aggregated_data(company):
    """Получить агрегированные данные для компании"""
    try:
        response = requests.get(f"{API_BASE}/aggregated-data/{company}", timeout=5)
        return response.json() if response.status_code == 200 else {"data": []}
    except:
        return {"data": []}

def update_consent(client_id, company, data_types, is_active):
    """Обновить согласие"""
    try:
        consent_data = {
            "client_id": client_id,
            "company": company,
            "data_types": data_types,
            "is_active": is_active
        }
        response = requests.post(f"{API_BASE}/consent", json=consent_data, timeout=5)

        st.cache_data.clear()
        return response.status_code == 200
    except Exception as e:
        st.error(f"Ошибка при обновлении согласия: {e}")
        return False

def revoke_consent(consent_id):
    """Отозвать согласие"""
    try:
        response = requests.delete(f"{API_BASE}/consent/{consent_id}", timeout=5)

        st.cache_data.clear()
        return response.status_code == 200
    except Exception as e:
        st.error(f"Ошибка при отзыве согласия: {e}")
        return False

def generate_demo_data():
    """Сгенерировать демо-данные"""
    try:
        response = requests.get(f"{API_BASE}/demo-data", timeout=10)
        if response.status_code == 200:
            st.cache_data.clear()
            return True
        return False
    except Exception as e:
        st.error(f"Ошибка при генерации демо-данных: {e}")
        return False

st.title("Платформа для аналитики и прогнозирования")
st.markdown("---")

st.sidebar.header("Выбор роли")
role = st.sidebar.selectbox(
    "Кто вы?",
    ["Клиент Банка", "B2B-Партнер"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.subheader("Статус системы")
api_healthy = check_api_health()

if api_healthy:
    st.sidebar.success("API подключено")
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Быстрый старт")
    if st.sidebar.button("Сгенерировать демо-данные", help="Создает тестовые согласия и данные"):
        with st.spinner("Генерация демо-данных..."):
            if generate_demo_data():
                st.sidebar.success("✅ Демо-данные созданы!")
                st.rerun()
            else:
                st.sidebar.error("❌ Ошибка создания демо-данных")
else:
    st.sidebar.error("❌ API недоступно")
    st.error("""
    ⚠️ Сервер API недоступен. 
    
    **Для запуска выполните в отдельном терминале:**
    ```bash
    uvicorn api:app --reload --host 0.0.0.0 --port 8000
    ```
    """)
    st.stop()

def with_loading(message="Загрузка..."):
    def decorator(func):
        def wrapper(*args, **kwargs):
            with st.spinner(message):
                time.sleep(0.5)
                return func(*args, **kwargs)
        return wrapper
    return decorator

if role == "Клиент Банка":
    st.header("Личный кабинет клиента")
    
    clients = get_clients()
    if not clients:
        st.error("Не удалось загрузить данные клиентов")
        st.stop()
    
    selected_client = st.selectbox("Выберите ваш профиль:", clients)
    
    if selected_client:
        tab1, tab2, tab3 = st.tabs(["Мои данные", "Управление согласием", "О платформе"])
        
        with tab1:
            st.subheader("Ваши финансовые данные")
            
            client_profile = get_client_profile(selected_client)
            if client_profile:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Общий баланс", f"{client_profile['total_balance']:,.0f} ₽")
                
                with col2:
                    st.metric("Всего транзакций", len(client_profile['transactions']))
                
                with col3:
                    total_spent = sum(t['amount'] for t in client_profile['transactions'])
                    st.metric("Общие расходы", f"{total_spent:,.0f} ₽")
                
                st.subheader("Визуализация ваших трат")
                
                df_transactions = pd.DataFrame(client_profile['transactions'])
                df_transactions['date'] = pd.to_datetime(df_transactions['date'])
                
                col1, col2 = st.columns(2)
                
                with col1:
                    category_spending = df_transactions.groupby('category')['amount'].sum().reset_index()
                    fig_pie = px.pie(category_spending, values='amount', names='category', 
                                   title="Распределение трат по категориям")
                    st.plotly_chart(fig_pie, use_container_width=True)
                
                with col2:
                    daily_spending = df_transactions.groupby('date')['amount'].sum().reset_index()
                    fig_line = px.line(daily_spending, x='date', y='amount', 
                                     title="Динамика трат по дням")
                    st.plotly_chart(fig_line, use_container_width=True)
                
                st.subheader("История транзакций")
                display_df = df_transactions[['date', 'category', 'merchant', 'amount']].copy()
                display_df['amount'] = display_df['amount'].apply(lambda x: f"{x:,.0f} ₽")
                display_df = display_df.sort_values('date', ascending=False)
                st.dataframe(display_df, use_container_width=True)
                
            else:
                st.error("Не удалось загрузить данные профиля")
        
        with tab2:
            st.subheader("Управление согласием на использование данных")
            st.info("""
            Здесь вы можете контролировать, какие обезличенные данные и каким компаниям передавать.
            **Ваши данные всегда остаются анонимными и агрегированными.**
            """)
            
            companies = get_companies()
            data_types = get_data_types()
            
            if companies and data_types:
                # Текущие согласия
                st.subheader("Текущие согласия")
                consents = get_client_consents(selected_client)
                
                if consents:
                    for consent in consents:
                        col1, col2, col3 = st.columns([3, 2, 1])
                        
                        with col1:
                            st.write(f"**Компания:** {consent['company']}")
                            st.write(f"**Типы данных:** {', '.join(consent['data_types'])}")
                        
                        with col2:
                            status = "✅ Активно" if consent['is_active'] else "❌ Неактивно"
                            st.write(f"**Статус:** {status}")
                        
                        with col3:
                            if st.button("Отозвать", key=f"revoke_{consent['consent_id']}"):
                                if revoke_consent(consent['consent_id']):
                                    st.success("Согласие отозвано!")
                                    st.rerun()
                                else:
                                    st.error("Ошибка при отзыве согласия")
                else:
                    st.info("У вас пока нет активных согласий")
                
                st.subheader("Новое согласие")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    selected_company = st.selectbox("Выберите компанию:", companies)
                
                with col2:
                    selected_data_types = st.multiselect(
                        "Выберите типы данных для передачи:",
                        data_types,
                        default=["category_spending", "average_bill"]
                    )
                
                consent_active = st.checkbox("Активировать согласие", value=True)
                
                if st.button("Сохранить согласие", type="primary"):
                    if not selected_company:
                        st.error("Выберите компанию")
                    elif not selected_data_types:
                        st.error("Выберите хотя бы один тип данных")
                    else:
                        if update_consent(selected_client, selected_company, selected_data_types, consent_active):
                            st.success("✅ Согласие успешно сохранено!")
                            st.rerun()
                        else:
                            st.error("❌ Ошибка при сохранении согласия")
            
            else:
                st.error("Не удалось загрузить список компаний или типов данных")
        
        with tab3:
            st.subheader("О платформе")
            
            st.info("""
            ### Как это работает?
            
            **Платформа аналитики Банка** позволяет вам безопасно делиться обезличенными данными 
            с проверенными компаниями-партнерами для улучшения их продуктов и услуг.
            
            ### Ваша безопасность - наш приоритет
            
            - **Только обезличенные данные** - личная информация никогда не передается
            - **Полный контроль** - вы решаете, кому и какие данные передавать
            - **Прозрачность** - вы всегда видите, какие данные переданы
            - **Мгновенный отзыв** - можете отозвать согласие в любой момент
            
            ### Что получаете вы?
            
            - Помогаете бизнесу создавать более релевантные предложения
            - Участвуете в развитии экономики данных
            - Получаете более персонализированный сервис в будущем
            """)
            
            st.success("""
            **Присоединяйтесь к движению!** 
            Ваши данные помогают создавать продукты будущего, оставаясь в полной безопасности.
            """)

else:  # B2B
    st.header("Панель B2B-Партнера")
    st.info("Доступ к агрегированным и обезличенным данным клиентов")
    
    companies = get_companies()
    if not companies:
        st.error("Не удалось загрузить список компаний")
        st.stop()
    
    selected_company = st.selectbox("Выберите вашу компанию:", companies)
    
    if selected_company:
        try:
            response = requests.get(f"{API_BASE}/aggregated-data/{selected_company}")
            if response.status_code == 200:
                company_data = response.json()
            else:
                company_data = {"data": []}
        except:
            company_data = {"data": []}
        
        tab1, tab2, tab3 = st.tabs(["Аналитика", "Сегменты", "Настройки"])
        
        with tab1:
            st.subheader("Обзор агрегированных данных")
            
            if company_data["data"]:
                st.subheader("Ключевые показатели")
                
                col1, col2, col3, col4 = st.columns(4)
                
                total_datasets = company_data["total_datasets"]
                total_samples = sum(data.get("sample_size", 0) for data in company_data["data"])
                data_types = len(set(data["data_type"] for data in company_data["data"]))
                
                with col1:
                    st.metric("Всего наборов данных", total_datasets)
                with col2:
                    st.metric("Общий размер выборки", total_samples)
                with col3:
                    st.metric("Типов данных", data_types)
                with col4:
                    st.metric("Статус", "✅ Активно")
                
                st.subheader("Визуализация данных")
                
                data_by_type = {}
                for dataset in company_data["data"]:
                    data_type = dataset["data_type"]
                    if data_type not in data_by_type:
                        data_by_type[data_type] = []
                    data_by_type[data_type].append(dataset)
                
                for data_type, datasets in data_by_type.items():
                    st.markdown(f"**{data_type.replace('_', ' ').title()}**")
                    
                    if data_type == "category_spending":
                        all_categories = {}
                        for dataset in datasets:
                            categories = dataset["metrics"].get("spending_by_category", {})
                            for category, amount in categories.items():
                                if category not in all_categories:
                                    all_categories[category] = 0
                                all_categories[category] += amount
                        
                        if all_categories:
                            df_categories = pd.DataFrame({
                                'Category': list(all_categories.keys()),
                                'Amount': list(all_categories.values())
                            }).sort_values('Amount', ascending=False)
                            
                            fig_bar = px.bar(df_categories.head(10), 
                                           x='Category', y='Amount',
                                           title="Топ-10 категорий трат",
                                           color='Amount')
                            st.plotly_chart(fig_bar, use_container_width=True)
                    
                    elif data_type == "average_bill":
                        avg_bills = [d["metrics"].get("average_transaction_amount", 0) for d in datasets]
                        min_bills = [d["metrics"].get("min_amount", 0) for d in datasets]
                        max_bills = [d["metrics"].get("max_amount", 0) for d in datasets]
                        
                        if avg_bills:
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Средний чек", f"{sum(avg_bills)/len(avg_bills):.2f} ₽")
                            with col2:
                                st.metric("Минимальный чек", f"{min(min_bills):.2f} ₽")
                            with col3:
                                st.metric("Максимальный чек", f"{max(max_bills):.2f} ₽")
                    
                    elif data_type == "age_group_stats":
                        age_groups = {}
                        cities = {}
                        balances = []
                        
                        for dataset in datasets:
                            age_group = dataset["metrics"].get("age_group", "")
                            city = dataset["metrics"].get("city", "")
                            balance = dataset["metrics"].get("average_balance", 0)
                            
                            if age_group:
                                if age_group not in age_groups:
                                    age_groups[age_group] = 0
                                age_groups[age_group] += 1
                            
                            if city:
                                if city not in cities:
                                    cities[city] = 0
                                cities[city] += 1
                            
                            balances.append(balance)
                        
                        if age_groups:
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                df_ages = pd.DataFrame({
                                    'Age Group': list(age_groups.keys()),
                                    'Count': list(age_groups.values())
                                })
                                fig_ages = px.pie(df_ages, values='Count', names='Age Group',
                                                title="Распределение по возрастным группам")
                                st.plotly_chart(fig_ages, use_container_width=True)
                            
                            with col2:
                                if cities:
                                    df_cities = pd.DataFrame({
                                        'City': list(cities.keys()),
                                        'Count': list(cities.values())
                                    }).sort_values('Count', ascending=False)
                                    fig_cities = px.bar(df_cities.head(5), 
                                                      x='City', y='Count',
                                                      title="Топ-5 городов")
                                    st.plotly_chart(fig_cities, use_container_width=True)
                        
                        if balances:
                            avg_balance = sum(balances) / len(balances)
                            st.metric("Средний баланс клиентов", f"{avg_balance:,.0f} ₽")
                    
                    st.markdown("---")
                
                st.subheader("Детализация данных")
                with st.expander("Просмотреть все наборы данных"):
                    for i, dataset in enumerate(company_data["data"]):
                        st.write(f"**Набор {i+1}:** {dataset['data_type']}")
                        st.json(dataset["metrics"])
                        st.markdown("---")
            
            else:
                st.warning("""
                Нет доступных данных для вашей компании.
                
                **Возможные причины:**
                - Клиенты еще не предоставили согласие на передачу данных
                - Данные находятся в процессе агрегации
                - Технические работы на платформе                
                """)
        
        with tab2:
            st.subheader("Сегментация данных")
            
            if company_data["data"]:
                st.info("Настройте параметры выборки для получения целевых данных")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    age_filter = st.multiselect(
                        "Возрастные группы:",
                        ["18-25", "25-35", "35-45", "45-55", "55+"],
                        default=["25-35", "35-45"]
                    )
                    
                    min_balance = st.number_input("Минимальный баланс (₽):", 
                                                value=0, step=1000)
                
                with col2:
                    city_filter = st.multiselect(
                        "Города:",
                        ["Москва", "Санкт-Петербург", "Новосибирск", "Екатеринбург", "Казань"],
                        default=["Москва", "Санкт-Петербург"]
                    )
                    
                    spending_categories = st.multiselect(
                        "Категории трат:",
                        ["Рестораны", "Супермаркеты", "Электроника", "Транспорт", 
                         "Развлечения", "Одежда", "Красота", "Путешествия", "Фитнес"],
                        default=["Рестораны", "Развлечения", "Одежда"]
                    )
                
                if st.button("Применить фильтры", type="primary"):
                    st.success(f"""
                    Сформирована выборка по параметрам:
                    - **Возраст:** {', '.join(age_filter) if age_filter else 'Все'}
                    - **Города:** {', '.join(city_filter) if city_filter else 'Все'}
                    - **Категории:** {', '.join(spending_categories) if spending_categories else 'Все'}
                    - **Минимальный баланс:** {min_balance:,} ₽
                    """)
                    
                    st.info("В реальной системе здесь происходила бы фильтрация данных и формирование новой выборки")
            
            else:
                st.warning("Для настройки сегментации необходимы доступные данные")
        
        with tab3:
            st.subheader("Настройки интеграции")
            
            st.info("Управление доступом к данным и настройками API")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Текущие настройки:**")
                st.write("API ключ: `••••••••••••••••`")
                st.write("Endpoint: `/api/v1/aggregated-data`")
                st.write("Формат данных: JSON")
                st.write("Частота обновления: Ежедневно")
            
            with col2:
                st.write("**Действия:**")
                if st.button("Обновить API ключ"):
                    st.success("API ключ успешно обновлен!")
                
                if st.button("Экспорт метаданных"):
                    st.success("Метаданные экспортированы в формате JSON")
                
                if st.button("Показать документацию"):
                    st.info("Документация API доступна по ссылке: http://localhost:8000/docs")
                    
st.markdown("---")
st.caption("""
Платформа аналитики Банка | 
Все данные обезличены и агрегированы
""")