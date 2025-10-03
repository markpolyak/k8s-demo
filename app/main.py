"""
ML API Service для предсказания оттока клиентов
Используется для демонстрации работы Kubernetes
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import redis
import psycopg2
import pickle
import numpy as np
import os
import time
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ML Churn Prediction API", version="1.0.0")

# Конфигурация из переменных окружения
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "mldb")
POSTGRES_USER = os.getenv("POSTGRES_USER", "mluser")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "mlpassword")
MODEL_VERSION = os.getenv("MODEL_VERSION", "1.0.0")

# Глобальные переменные
redis_client = None
db_connection = None
model = None
model_loaded = False

# Время старта приложения (для имитации долгой загрузки модели)
startup_time = time.time()


class CustomerData(BaseModel):
    """Входные данные о клиенте"""
    customer_id: int
    usage_minutes: int
    support_calls: int
    contract_months: int = 12
    monthly_charge: float = 50.0


class PredictionResponse(BaseModel):
    """Ответ с предсказанием"""
    customer_id: int
    churn_probability: float
    churn_prediction: bool
    model_version: str
    cached: bool
    timestamp: str


def get_redis_client():
    """Подключение к Redis с retry логикой"""
    global redis_client
    if redis_client is None:
        max_retries = 5
        for i in range(max_retries):
            try:
                redis_client = redis.Redis(
                    host=REDIS_HOST,
                    port=REDIS_PORT,
                    decode_responses=False,
                    socket_connect_timeout=5
                )
                redis_client.ping()
                logger.info(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
                return redis_client
            except redis.ConnectionError:
                if i < max_retries - 1:
                    logger.warning(f"Redis connection failed, retry {i+1}/{max_retries}")
                    time.sleep(2)
                else:
                    logger.error("Failed to connect to Redis after retries")
                    raise
    return redis_client


def get_db_connection():
    """Подключение к PostgreSQL"""
    global db_connection
    if db_connection is None or db_connection.closed:
        try:
            db_connection = psycopg2.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                database=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD
            )
            logger.info(f"Connected to PostgreSQL at {POSTGRES_HOST}:{POSTGRES_PORT}")
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise
    return db_connection


def load_model():
    """
    Загрузка ML модели
    Имитирует долгую загрузку (10 секунд) для демонстрации startup probes
    """
    global model, model_loaded

    logger.info("Starting model loading... (this takes ~10 seconds)")
    time.sleep(10)  # Имитация долгой загрузки тяжелой модели

    # Простая логистическая регрессия (для демо)
    # В реальности здесь был бы pickle.load() обученной модели
    class DummyModel:
        def predict_proba(self, X):
            # Простая формула для демонстрации
            # Вероятность оттока зависит от количества звонков в поддержку
            # и обратно пропорциональна использованию
            usage = X[0][0]
            support_calls = X[0][1]

            # Чем больше звонков и меньше использование - тем выше вероятность оттока
            churn_prob = min(0.95, 0.1 + (support_calls * 0.15) - (usage / 10000))
            churn_prob = max(0.05, churn_prob)

            return np.array([[1 - churn_prob, churn_prob]])

    model = DummyModel()
    model_loaded = True
    logger.info(f"Model v{MODEL_VERSION} loaded successfully!")


@app.on_event("startup")
async def startup_event():
    """Инициализация при старте приложения"""
    logger.info("=" * 50)
    logger.info(f"Starting ML API Service v{MODEL_VERSION}")
    logger.info("=" * 50)

    # Создаем таблицу в PostgreSQL если её нет
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id SERIAL PRIMARY KEY,
                customer_id INTEGER,
                churn_probability FLOAT,
                churn_prediction BOOLEAN,
                model_version VARCHAR(20),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cursor.close()
        logger.info("Database table initialized")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

    # Загружаем модель
    load_model()


@app.get("/")
async def root():
    """Корневой эндпоинт"""
    return {
        "service": "ML Churn Prediction API",
        "version": MODEL_VERSION,
        "status": "running",
        "model_loaded": model_loaded
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint для Liveness Probe
    Проверяет, что приложение живо и отвечает
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint для Readiness Probe
    Проверяет, что приложение готово принимать запросы
    (модель загружена, подключения к БД и Redis работают)
    """
    if not model_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded yet")

    # Проверяем подключения
    try:
        redis_client = get_redis_client()
        redis_client.ping()
    except:
        raise HTTPException(status_code=503, detail="Redis connection failed")

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
    except:
        raise HTTPException(status_code=503, detail="Database connection failed")

    return {
        "status": "ready",
        "model_version": MODEL_VERSION,
        "uptime_seconds": int(time.time() - startup_time)
    }


@app.get("/startup")
async def startup_check():
    """
    Startup check endpoint для Startup Probe
    Проверяет, что приложение полностью стартовало
    """
    if not model_loaded:
        raise HTTPException(status_code=503, detail="Still loading model...")

    return {
        "status": "started",
        "model_version": MODEL_VERSION
    }


@app.post("/predict", response_model=PredictionResponse)
async def predict_churn(data: CustomerData):
    """
    Предсказание оттока клиента

    - Сначала проверяет кэш в Redis
    - Если нет в кэше - делает предсказание с помощью модели
    - Сохраняет результат в PostgreSQL
    - Кэширует в Redis
    """
    if not model_loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")

    cache_key = f"prediction:{data.customer_id}"
    cached = False

    # Проверяем кэш в Redis
    try:
        redis_client = get_redis_client()
        cached_result = redis_client.get(cache_key)

        if cached_result:
            result = pickle.loads(cached_result)
            result["cached"] = True
            logger.info(f"Cache HIT for customer {data.customer_id}")
            return result
    except Exception as e:
        logger.warning(f"Redis error: {e}, proceeding without cache")

    # Делаем предсказание моделью
    try:
        features = np.array([[
            data.usage_minutes,
            data.support_calls,
            data.contract_months,
            data.monthly_charge
        ]])

        # Получаем вероятность оттока
        probabilities = model.predict_proba(features)
        churn_probability = float(probabilities[0][1])
        churn_prediction = churn_probability > 0.5

        result = {
            "customer_id": data.customer_id,
            "churn_probability": round(churn_probability, 4),
            "churn_prediction": churn_prediction,
            "model_version": MODEL_VERSION,
            "cached": False,
            "timestamp": datetime.now().isoformat()
        }

        # Сохраняем в PostgreSQL
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO predictions
                (customer_id, churn_probability, churn_prediction, model_version)
                VALUES (%s, %s, %s, %s)
            """, (
                data.customer_id,
                churn_probability,
                churn_prediction,
                MODEL_VERSION
            ))
            conn.commit()
            cursor.close()
            logger.info(f"Prediction saved to database for customer {data.customer_id}")
        except Exception as e:
            logger.error(f"Database error: {e}")

        # Кэшируем в Redis (на 5 минут)
        try:
            redis_client.setex(
                cache_key,
                300,  # TTL 5 минут
                pickle.dumps(result)
            )
            logger.info(f"Prediction cached for customer {data.customer_id}")
        except Exception as e:
            logger.warning(f"Cache error: {e}")

        logger.info(f"Prediction made for customer {data.customer_id}: {churn_probability:.2%}")
        return result

    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
async def get_statistics():
    """
    Получение статистики по предсказаниям
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total_predictions,
                AVG(churn_probability) as avg_churn_prob,
                SUM(CASE WHEN churn_prediction THEN 1 ELSE 0 END) as predicted_churns
            FROM predictions
        """)

        result = cursor.fetchone()
        cursor.close()

        return {
            "total_predictions": result[0] or 0,
            "average_churn_probability": round(float(result[1] or 0), 4),
            "predicted_churns": result[2] or 0,
            "model_version": MODEL_VERSION
        }
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
