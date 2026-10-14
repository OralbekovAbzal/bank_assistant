"""
Заполняет БД тестовыми данными: пользователи, счета, транзакции.

Запуск:  python seed.py

Можно запускать повторно: скрипт удаляет только тестовых пользователей
(по телефонам из списка USERS) и всё, что к ним относится, и создаёт заново.
Твои собственные данные не трогает.
"""

import os
import random
from datetime import datetime, timedelta, timezone

import psycopg
from dotenv import load_dotenv
from pwdlib import PasswordHash

load_dotenv()
random.seed(42)  # одинаковые данные при каждом запуске

TEST_PASSWORD = "test1234"

USERS = [
    ("+77010000001", "Айгерим Сейтказы"),
    ("+77010000002", "Данияр Жумабеков"),
    ("+77010000003", "Мадина Ахметова"),
    ("+77010000004", "Ерлан Касымов"),
    ("+77010000005", "Жанар Нурланова"),
]

# (название, мин. сумма, макс. сумма) в тенге
MERCHANTS = [
    ("Magnum", 3_000, 25_000),
    ("Small", 1_000, 8_000),
    ("Yandex Go", 800, 4_500),
    ("Chocofood", 3_500, 12_000),
    ("Beeline", 2_500, 6_000),
    ("ЖКХ Астана", 15_000, 40_000),
    ("Технодом", 20_000, 150_000),
    ("Аптека Europharma", 1_500, 15_000),
    ("Кинотеатр Kinopark", 2_500, 7_000),
    ("Starbucks", 1_800, 4_500),
]

P2P_DESCRIPTIONS = ["Перевод", "Возврат долга", "За обед", "На подарок", "За такси"]

WITHDRAWAL_FEE = 200

NOW = datetime.now(timezone.utc)
START = NOW - timedelta(days=90)


def rand_time() -> datetime:
    seconds = random.randint(0, int((NOW - START).total_seconds()))
    return START + timedelta(seconds=seconds)


def cleanup(cur, phones: list[str]) -> None:
    """Удаляет тестовых пользователей и всё, что на них ссылается (от детей к родителям)."""
    user_ids = "select id from users where phone = any(%s)"
    account_ids = f"select id from accounts where user_id in ({user_ids})"

    cur.execute(
        f"delete from messages where conversation_id in "
        f"(select id from conversations where user_id in ({user_ids}))",
        (phones,),
    )
    cur.execute(f"delete from conversations where user_id in ({user_ids})", (phones,))
    cur.execute(
        f"delete from transactions where orig_id in ({account_ids}) or dest_id in ({account_ids})",
        (phones, phones),
    )
    cur.execute(f"delete from accounts where user_id in ({user_ids})", (phones,))
    cur.execute("delete from users where phone = any(%s)", (phones,))


def create_users(cur) -> list[int]:
    hasher = PasswordHash.recommended()
    ids = []
    for phone, name in USERS:
        cur.execute(
            "insert into users (phone, name, password_hash, created_at) "
            "values (%s, %s, %s, %s) returning id",
            (phone, name, hasher.hash(TEST_PASSWORD), START - timedelta(days=30)),
        )
        ids.append(cur.fetchone()[0])
    return ids


def create_account(cur, user_id: int) -> int:
    cur.execute(
        "insert into accounts (user_id, created_at) values (%s, %s) returning id",
        (user_id, START - timedelta(days=30)),
    )
    return cur.fetchone()[0]


def build_events(main: dict[int, int], savings: dict[int, int], blocked: int) -> list[tuple]:
    """Событие: (время, тип, orig_id, dest_id, сумма, описание)."""
    events = []
    users = list(main.keys())

    # Зарплата раз в месяц на основной счёт
    for month in range(3):
        payday = START + timedelta(days=5 + 30 * month, hours=4)
        for u in users:
            amount = random.randrange(250_000, 700_001, 1_000)
            events.append((payday, "deposit", None, main[u], amount, "Зарплата"))

            # Часть зарплаты на сберегательный счёт на следующий день
            if u in savings:
                amount = random.randrange(30_000, 100_001, 5_000)
                events.append((payday + timedelta(days=1), "transfer", main[u], savings[u],
                               amount, "Перевод на сберегательный счёт"))

    # Покупки
    for u in users:
        for _ in range(random.randint(15, 25)):
            name, lo, hi = random.choice(MERCHANTS)
            amount = random.randrange(lo, hi, 10)
            events.append((rand_time(), "payment", main[u], None, amount, f"Оплата: {name}"))

    # Снятие наличных (комиссия добавляется при обработке)
    for u in users:
        for _ in range(random.randint(1, 3)):
            amount = random.randrange(10_000, 50_001, 1_000)
            events.append((rand_time(), "withdrawal", main[u], None, amount,
                           "Снятие наличных в банкомате"))

    # Переводы между пользователями
    for _ in range(10):
        a, b = random.sample(users, 2)
        amount = random.randrange(2_000, 60_001, 500)
        events.append((rand_time(), "transfer", main[a], main[b], amount,
                       random.choice(P2P_DESCRIPTIONS)))

    # Возвраты от магазинов
    for _ in range(3):
        u = random.choice(users)
        amount = random.randrange(5_000, 40_001, 100)
        events.append((rand_time(), "refund", None, main[u], amount, "Возврат: Технодом"))

    # Заблокированный счёт: одно пополнение до блокировки
    events.append((START + timedelta(days=2), "deposit", None, blocked, 15_000, "Пополнение"))

    events.sort(key=lambda e: e[0])
    return events


def apply_events(events: list[tuple], balances: dict[int, int]) -> list[tuple]:
    """Проходит события по времени и отбрасывает списания, на которые не хватает денег."""
    rows = []
    for t, typ, orig, dest, amount, desc in events:
        if orig is not None and balances[orig] < amount:
            continue
        if orig is not None:
            balances[orig] -= amount
        if dest is not None:
            balances[dest] += amount
        rows.append((orig, dest, typ, amount, desc, t))

        if typ == "withdrawal" and balances[orig] >= WITHDRAWAL_FEE:
            balances[orig] -= WITHDRAWAL_FEE
            rows.append((orig, None, "fee", WITHDRAWAL_FEE,
                         "Комиссия за снятие наличных", t + timedelta(seconds=5)))
    return rows


def main() -> None:
    conn = psycopg.connect(
        dbname="bank_assistant", host="localhost", user="admin",
        password=os.getenv("DB_PASSWORD"), port="5433", autocommit=True,
    )

    with conn.transaction():
        with conn.cursor() as cur:
            cleanup(cur, [phone for phone, _ in USERS])
            user_ids = create_users(cur)

            # У каждого основной счёт, у двоих ещё сберегательный, у последнего — заблокированный
            main_acc = {u: create_account(cur, u) for u in user_ids}
            savings_acc = {u: create_account(cur, u) for u in user_ids[0::2][:2]}
            blocked_acc = create_account(cur, user_ids[-1])

            all_accounts = [*main_acc.values(), *savings_acc.values(), blocked_acc]
            balances = {acc: 0 for acc in all_accounts}

            events = build_events(main_acc, savings_acc, blocked_acc)
            rows = apply_events(events, balances)

            cur.executemany(
                "insert into transactions (orig_id, dest_id, type, amount, description, created_at) "
                "values (%s, %s, %s, %s, %s, %s)",
                rows,
            )
            for acc, balance in balances.items():
                cur.execute("update accounts set balance = %s where id = %s", (balance, acc))
            cur.execute("update accounts set status = 'blocked' where id = %s", (blocked_acc,))

    conn.close()

    print(f"Готово: {len(USERS)} пользователей, {len(all_accounts)} счетов, {len(rows)} транзакций.")
    print(f"Пароль у всех: {TEST_PASSWORD}")
    for phone, name in USERS:
        print(f"  {phone}  {name}")


if __name__ == "__main__":
    main()