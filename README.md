# Bank Assistant

Чат-ассистент для клиентов банка на базе Gemini. Клиент регистрируется, входит в систему и общается с ассистентом, который помнит историю диалога.

## Стек

- **Python**, **FastAPI** — REST API
- **PostgreSQL** (psycopg) — пользователи, счета, диалоги, история сообщений
- **Gemini API** (Interactions API) — ответы ассистента
- **JWT** (PyJWT) — авторизация
- **pwdlib** (Argon2) — хеширование паролей

## Что умеет

- [x] Регистрация пользователя (пароль хранится только в виде хеша)
- [x] Вход по телефону и паролю, выдача JWT-токена
- [x] Защита эндпоинтов через Bearer-токен
- [ ] Чат с ассистентом с сохранением истории в Postgres (в работе)
- [ ] Доступ ассистента к данным клиента (баланс, транзакции) через function calling

## Как запустить

1. Клонировать репозиторий и создать виртуальное окружение:
   ```
   git clone https://github.com/OralbekovAbzal/bank_assistant.git
   cd bank_assistant
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Скопировать `.env.example` в `.env` и заполнить значения:
   ```
   GEMINI_API_KEY=
   DB_PASSWORD=
   JWT_SECRET=
   ```

3. Поднять PostgreSQL (порт 5433, база `bank_assistant`) и создать таблицы.

4. Запустить сервер:
   ```
   uvicorn api:app --reload
   ```
   Документация API: http://127.0.0.1:8000/docs

## API

| Метод | Путь | Описание | Авторизация |
|---|---|---|---|
| POST | `/registration` | Регистрация: `phone`, `name`, `password` | нет |
| POST | `/login` | Вход: `phone`, `password` → JWT-токен | нет |
| POST | `/chat` | Сообщение ассистенту: `conv_id` (необязательно), `message` | Bearer-токен |
