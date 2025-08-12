import asyncio
import aiomysql
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = '8401056423:AAGNna64zVZlN7HArlLgdbWv4eSBhtdy8B4'
bot = Bot(token=TOKEN)
dp = Dispatcher()

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3306,
    "user": "user41287",
    "password": "f5b8ZY5wo02W",
    "db": "user41287",
}

class Database:
    _pool = None

    @classmethod
    async def get_pool(cls):
        if not cls._pool:
            try:
                cls._pool = await aiomysql.create_pool(
                    **DB_CONFIG,
                    minsize=1,
                    maxsize=3,
                    connect_timeout=5,
                    pool_recycle=300
                )
                logger.info("Успешное подключение к БД")
            except Exception as e:
                logger.error(f"Ошибка подключения: {e}")
                raise RuntimeError("Не удалось подключиться к базе данных")
        return cls._pool

    @classmethod
    async def close_pool(cls):
        if cls._pool:
            cls._pool.close()
            await cls._pool.wait_closed()
            logger.info("Пул соединений закрыт")

@dp.message(Command('start'))
async def start(message: types.Message):
    await message.answer(
        "Для регистрации введите:\n"
        "/test Имя Фамилия Возраст\n"
        "Пример: /test Иван Иванов 25"
    )

@dp.message(Command('test'))
async def register_user(message: types.Message):
    try:
        parts = message.text.split()
        if len(parts) != 4:
            return await message.answer("Неверный формат. Пример: /test Иван Иванов 25")

        _, name, surname, age = parts
        
        try:
            age = int(age)
            if age <= 0 or age > 120:
                return await message.answer("Возраст должен быть от 1 до 120 лет")
        except ValueError:
            return await message.answer("Возраст должен быть числом")

        try:
            pool = await Database.get_pool()
            async with pool.acquire() as conn:
                async with conn.cursor() as cursor
                    await cursor.execute("""
                        CREATE TABLE IF NOT EXISTS users (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            name VARCHAR(50) NOT NULL,
                            surname VARCHAR(50) NOT NULL,
                            age INT NOT NULL,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    await conn.commit()
                    
                   
                    await cursor.execute(
                        "INSERT INTO users (name, surname, age) VALUES (%s, %s, %s)",
                        (name, surname, age)
                    )
                    await conn.commit()
            
            await message.answer(f"Данные сохранены:\nИмя: {name}\nФамилия: {surname}\nВозраст: {age}")
            
        except aiomysql.OperationalError as e:
            logger.error(f"Ошибка БД: {e}")
            await message.answer("Ошибка подключения к базе данных. Попробуйте позже.")
        except Exception as e:
            logger.error(f"Ошибка при сохранении: {e}")
            await message.answer("Ошибка при сохранении данных")

    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        await message.answer("Gроизошла непредвиденная ошибка")

async def main():
    try:
        await dp.start_polling(bot)
    finally:
        await Database.close_pool()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as e:
        logger.critical(f"Критическая ошибка: {e}")
    except Exception as e:
        logger.critical(f"Необработанная ошибка: {e}")
