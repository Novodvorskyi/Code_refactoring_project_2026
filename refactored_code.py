"""
Система управління бібліотекою
================================
Модуль реалізує повноцінну систему обліку книг, користувачів,
операцій позичання/повернення та нарахування штрафів.

Константи штрафів:
    FINE_RATE_FIRST_WEEK    — $0.50 за день (дні 1–7 прострочення)
    FINE_RATE_SECOND_PERIOD — $1.00 за день (дні 8–30 прострочення)
    FINE_RATE_EXTENDED      — $2.00 за день (день 31+ прострочення)
    MAX_FINE_THRESHOLD      — $50.00 максимальний борг до блокування позичання
    DEFAULT_BORROW_DAYS     — 14 днів — стандартний термін позичання
"""

import datetime
import json
from dataclasses import dataclass, field, asdict
from typing import Optional

FINE_RATE_FIRST_WEEK = 0.5       # $ за день, дні 1–7
FINE_RATE_SECOND_PERIOD = 1.0    # $ за день, дні 8–30
FINE_RATE_EXTENDED = 2.0         # $ за день, день 31+
MAX_FINE_THRESHOLD = 50.0        # $ максимальний борг до блокування позичання
DEFAULT_BORROW_DAYS = 14         # стандартний термін позичання у днях


@dataclass
class BookData:
    """
    Об'єкт-значення з параметрами для створення книги.

    Атрибути:
        book_id  (str):   Унікальний ідентифікатор книги.
        title    (str):   Назва книги.
        author   (str):   Автор книги.
        year     (int):   Рік видання.
        genre    (str):   Жанр книги.
        quantity (int):   Загальна кількість примірників у бібліотеці.
        price    (float): Ціна книги.
    """
    book_id: str
    title: str
    author: str
    year: int
    genre: str
    quantity: int
    price: float


@dataclass
class UserData:
    """
    Об'єкт-значення з параметрами для реєстрації користувача.

    Атрибути:
        user_id (str): Унікальний ідентифікатор користувача.
        name    (str): Повне ім'я користувача.
        email   (str): Електронна пошта.
        phone   (str): Номер телефону.
        address (str): Адреса проживання.
    """
    user_id: str
    name: str
    email: str
    phone: str
    address: str


@dataclass
class BorrowRecord:
    """
    Запис про факт позичання однієї книги одним користувачем.

    Атрибути:
        book_id      (str):            Ідентифікатор позиченої книги.
        borrow_date  (str):            Дата видачі (ISO-формат YYYY-MM-DD).
        due_date     (str):            Кінцева дата повернення (ISO-формат).
        returned     (bool):           True, якщо книгу вже повернено.
        return_date  (Optional[str]):  Фактична дата повернення або None.
        fine         (float):          Нарахований штраф за прострочення.
    """
    book_id: str
    borrow_date: str
    due_date: str
    returned: bool = False
    return_date: Optional[str] = None
    fine: float = 0.0


class Book:
    """
    Представляє книгу бібліотечного фонду разом зі станом інвентарю.

    Атрибути екземпляра:
        book_id       (str):   Унікальний ідентифікатор.
        title         (str):   Назва.
        author        (str):   Автор.
        year          (int):   Рік видання.
        genre         (str):   Жанр.
        quantity      (int):   Загальна кількість примірників.
        price         (float): Ціна.
        available     (int):   Кількість доступних примірників.
        borrowed_count(int):   Загальна кількість видач (накопичувально).
    """

    def __init__(self, data: BookData) -> None:
        """
        Ініціалізує книгу з переданого об'єкта BookData.

        Аргументи:
            data (BookData): Параметри нової книги.
        """
        self.book_id = data.book_id
        self.title = data.title
        self.author = data.author
        self.year = data.year
        self.genre = data.genre
        self.quantity = data.quantity
        self.price = data.price
        self.available = data.quantity
        self.borrowed_count = 0

    @property
    def is_available(self) -> bool:
        """True, якщо є хоча б один доступний примірник."""
        return self.available > 0

    def checkout(self) -> None:
        """Зменшує лічильник доступних примірників і збільшує лічильник видач."""
        self.available -= 1
        self.borrowed_count += 1

    def checkin(self) -> None:
        """Збільшує лічильник доступних примірників при поверненні."""
        self.available += 1

    def update_quantity(self, new_quantity: int) -> None:
        """
        Оновлює загальну кількість примірників і коригує кількість доступних.

        Аргументи:
            new_quantity (int): Нова загальна кількість примірників.
        """
        difference = new_quantity - self.quantity
        self.quantity = new_quantity
        self.available += difference

    def to_dict(self) -> dict:
        """Серіалізує книгу у словник для збереження в JSON."""
        return {
            'id': self.book_id,
            'title': self.title,
            'author': self.author,
            'year': self.year,
            'genre': self.genre,
            'quantity': self.quantity,
            'price': self.price,
            'available': self.available,
            'borrowed_count': self.borrowed_count,
        }

    @classmethod
    def from_dict(cls, raw: dict) -> 'Book':
        """
        Відновлює об'єкт Book із словника (десеріалізація з JSON).

        Аргументи:
            raw (dict): Словник з атрибутами книги.

        Повертає:
            Book: Відновлений екземпляр книги.
        """
        data = BookData(
            book_id=raw['id'], title=raw['title'], author=raw['author'],
            year=raw['year'], genre=raw['genre'],
            quantity=raw['quantity'], price=raw['price'],
        )
        book = cls(data)
        book.available = raw.get('available', raw['quantity'])
        book.borrowed_count = raw.get('borrowed_count', 0)
        return book


class User:
    """
    Представляє члена бібліотеки (читача).

    Атрибути екземпляра:
        user_id           (str):              Унікальний ідентифікатор.
        name              (str):              Повне ім'я.
        email             (str):              Електронна пошта.
        phone             (str):              Номер телефону.
        address           (str):              Адреса.
        borrowed_books    (list[BorrowRecord]): Список записів про позичання.
        fines             (float):            Поточна сума незакритих штрафів.
        registration_date (str):              Дата реєстрації (ISO-формат).
    """

    def __init__(self, data: UserData) -> None:
        """
        Ініціалізує нового користувача з переданого об'єкта UserData.

        Аргументи:
            data (UserData): Параметри нового користувача.
        """
        self.user_id = data.user_id
        self.name = data.name
        self.email = data.email
        self.phone = data.phone
        self.address = data.address
        self.borrowed_books: list[BorrowRecord] = []
        self.fines: float = 0.0
        self.registration_date: str = str(datetime.date.today())

    @property
    def has_excessive_fines(self) -> bool:
        """True, якщо штраф перевищує MAX_FINE_THRESHOLD та позичання заблоковано."""
        return self.fines > MAX_FINE_THRESHOLD

    def active_borrow_for(self, book_id: str) -> Optional[BorrowRecord]:
        """
        Повертає активний (не повернений) запис позичання для вказаної книги.

        Аргументи:
            book_id (str): Ідентифікатор книги.

        Повертає:
            BorrowRecord або None, якщо активного запису немає.
        """
        return next(
            (rec for rec in self.borrowed_books
             if rec.book_id == book_id and not rec.returned),
            None
        )

    def active_borrow_index_for(self, book_id: str) -> int:
        """
        Повертає індекс активного запису позичання або -1, якщо не знайдено.

        Аргументи:
            book_id (str): Ідентифікатор книги.

        Повертає:
            int: Індекс у списку borrowed_books або -1.
        """
        for i, rec in enumerate(self.borrowed_books):
            if rec.book_id == book_id and not rec.returned:
                return i
        return -1

    def to_dict(self) -> dict:
        """Серіалізує користувача у словник для збереження в JSON."""
        return {
            'id': self.user_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'borrowed_books': [asdict(rec) for rec in self.borrowed_books],
            'fines': self.fines,
            'registration_date': self.registration_date,
        }

    @classmethod
    def from_dict(cls, raw: dict) -> 'User':
        """
        Відновлює об'єкт User із словника (десеріалізація з JSON).

        Аргументи:
            raw (dict): Словник з атрибутами користувача.

        Повертає:
            User: Відновлений екземпляр користувача.
        """
        data = UserData(
            user_id=raw['id'], name=raw['name'], email=raw['email'],
            phone=raw['phone'], address=raw['address'],
        )
        user = cls(data)
        user.borrowed_books = [BorrowRecord(**rec) for rec in raw.get('borrowed_books', [])]
        user.fines = raw.get('fines', 0.0)
        user.registration_date = raw.get('registration_date', str(datetime.date.today()))
        return user


class FineCalculator:
    """
    Інкапсулює логіку ступінчастого розрахунку штрафів за прострочення.

    Ставки штрафів:
        Дні 1–7:   $0.50 / день
        Дні 8–30:  $1.00 / день
        День 31+:  $2.00 / день
    """

    @staticmethod
    def calculate(due_date_str: str) -> float:
        """
        Обчислює суму штрафу відносно сьогоднішньої дати.

        Аргументи:
            due_date_str (str): Кінцева дата повернення у форматі ISO (YYYY-MM-DD).

        Повертає:
            float: Сума штрафу в доларах (0.0, якщо книга не прострочена).
        """
        due_date = datetime.date.fromisoformat(due_date_str)
        today = datetime.date.today()
        if today <= due_date:
            return 0.0
        days_late = (today - due_date).days
        return FineCalculator._tiered_fine(days_late)

    @staticmethod
    def _tiered_fine(days_late: int) -> float:
        """
        Застосовує ступінчасті добові ставки залежно від кількості днів прострочення.

        Аргументи:
            days_late (int): Кількість днів прострочення.

        Повертає:
            float: Загальна сума штрафу.
        """
        first_week = min(days_late, 7)
        second_period = max(0, min(days_late - 7, 23))   # дні 8–30
        extended = max(0, days_late - 30)                 # день 31+

        return (
            first_week * FINE_RATE_FIRST_WEEK
            + second_period * FINE_RATE_SECOND_PERIOD
            + extended * FINE_RATE_EXTENDED
        )


class Validator:
    """
    Набір статичних методів для перевірки вхідних даних.

    Усі методи генерують ValueError при порушенні обмежень.
    """

    @staticmethod
    def require_non_empty(value: str, field_name: str) -> None:
        """
        Перевіряє, що рядок не є порожнім.

        Аргументи:
            value      (str): Значення для перевірки.
            field_name (str): Назва поля (для повідомлення про помилку).

        Генерує:
            ValueError: Якщо значення порожнє.
        """
        if not value:
            raise ValueError(f'{field_name} cannot be empty.')

    @staticmethod
    def require_non_negative(value: float, field_name: str) -> None:
        """
        Перевіряє, що числове значення не від'ємне.

        Аргументи:
            value      (float): Значення для перевірки.
            field_name (str):   Назва поля (для повідомлення про помилку).

        Генерує:
            ValueError: Якщо значення від'ємне.
        """
        if value < 0:
            raise ValueError(f'{field_name} cannot be negative.')

    @staticmethod
    def require_valid_email(email: str) -> None:
        """
        Виконує базову перевірку формату електронної пошти (наявність символу '@').

        Аргументи:
            email (str): Адреса для перевірки.

        Генерує:
            ValueError: Якщо адреса не містить '@'.
        """
        if '@' not in email:
            raise ValueError('Invalid email format.')


class Library:
    """
    Центральний репозиторій і сервісний шар системи бібліотеки.

    Зберігає весь стан на рівні екземпляра — глобальні змінні модуля не використовуються.

    Внутрішні сховища:
        _books        (dict[str, Book]):  Каталог книг, ключ — book_id.
        _users        (dict[str, User]):  Реєстр користувачів, ключ — user_id.
        _transactions (list[dict]):       Журнал усіх транзакцій.
    """

    def __init__(self) -> None:
        """Ініціалізує порожню бібліотеку (без книг, користувачів та транзакцій)."""
        self._books: dict[str, Book] = {}
        self._users: dict[str, User] = {}
        self._transactions: list[dict] = []

    # Збереження / завантаження стану

    def load(self, filepath: str) -> None:
        """
        Завантажує стан бібліотеки з JSON-файлу.

        Аргументи:
            filepath (str): Шлях до файлу збереження.
        """
        with open(filepath, 'r', encoding='utf-8') as fh:
            payload = json.load(fh)
        self._books = {b['id']: Book.from_dict(b) for b in payload.get('books', [])}
        self._users = {u['id']: User.from_dict(u) for u in payload.get('users', [])}
        self._transactions = payload.get('transactions', [])

    def save(self, filepath: str) -> None:
        """
        Зберігає поточний стан бібліотеки у JSON-файл.

        Аргументи:
            filepath (str): Шлях до файлу збереження.
        """
        payload = {
            'books': [b.to_dict() for b in self._books.values()],
            'users': [u.to_dict() for u in self._users.values()],
            'transactions': self._transactions,
        }
        with open(filepath, 'w', encoding='utf-8') as fh:
            json.dump(payload, fh, indent=2)

    # Управління книгами

    def add_book(self, book_data: BookData) -> bool:
        """
        Реєструє нову книгу в каталозі.

        Аргументи:
            book_data (BookData): Параметри нової книги.

        Повертає:
            bool: True при успішному додаванні.

        Генерує:
            ValueError: Якщо книга з таким ID вже існує або дані невалідні.
        """
        self._validate_book_data(book_data)
        if book_data.book_id in self._books:
            raise ValueError(f'Book with ID "{book_data.book_id}" already exists.')
        self._books[book_data.book_id] = Book(book_data)
        return True

    def remove_book(self, book_id: str) -> bool:
        """
        Видаляє книгу з каталогу.

        Аргументи:
            book_id (str): Ідентифікатор книги для видалення.

        Повертає:
            bool: True при успішному видаленні.

        Генерує:
            ValueError: Якщо книга не знайдена.
        """
        book = self._get_book_or_raise(book_id)
        del self._books[book_id]
        return True

    def update_book(
        self,
        book_id: str,
        title: Optional[str] = None,
        author: Optional[str] = None,
        year: Optional[int] = None,
        genre: Optional[str] = None,
        quantity: Optional[int] = None,
        price: Optional[float] = None,
    ) -> bool:
        """
        Оновлює одне або кілька полів існуючої книги.

        Аргументи:
            book_id  (str):            Ідентифікатор книги.
            title    (Optional[str]):  Нова назва (None — без змін).
            author   (Optional[str]):  Новий автор (None — без змін).
            year     (Optional[int]):  Новий рік видання (None — без змін).
            genre    (Optional[str]):  Новий жанр (None — без змін).
            quantity (Optional[int]):  Нова загальна кількість (None — без змін).
            price    (Optional[float]):Нова ціна (None — без змін).

        Повертає:
            bool: True при успішному оновленні.

        Генерує:
            ValueError: Якщо книга не знайдена або дані невалідні.
        """
        book = self._get_book_or_raise(book_id)
        if title is not None:
            book.title = title
        if author is not None:
            book.author = author
        if year is not None:
            book.year = year
        if genre is not None:
            book.genre = genre
        if quantity is not None:
            Validator.require_non_negative(quantity, 'Quantity')
            book.update_quantity(quantity)
        if price is not None:
            Validator.require_non_negative(price, 'Price')
            book.price = price
        return True

    def get_book(self, book_id: str) -> Optional[Book]:
        """
        Повертає книгу за ідентифікатором або None, якщо не знайдена.

        Аргументи:
            book_id (str): Ідентифікатор книги.

        Повертає:
            Optional[Book]: Об'єкт книги або None.
        """
        return self._books.get(book_id)

    def search_books(self, query: str, search_by: str) -> list[Book]:
        """
        Виконує пошук книг за вказаним полем (без урахування регістру).

        Аргументи:
            query     (str): Пошуковий запит.
            search_by (str): Поле для пошуку: 'title', 'author', 'genre' або 'id'.

        Повертає:
            list[Book]: Список книг, що відповідають запиту.

        Генерує:
            ValueError: Якщо вказано невідоме поле пошуку.
        """
        query_lower = query.lower()
        field_map = {
            'title': lambda b: b.title,
            'author': lambda b: b.author,
            'genre': lambda b: b.genre,
            'id': lambda b: b.book_id,
        }
        if search_by not in field_map:
            raise ValueError(f'Invalid search field: {search_by}')
        extract = field_map[search_by]
        return [b for b in self._books.values() if query_lower in extract(b).lower()]

    def get_popular_books(self, top_n: int) -> list[Book]:
        """
        Повертає топ-N найбільш затребуваних книг за кількістю видач.

        Аргументи:
            top_n (int): Кількість книг у результаті.

        Повертає:
            list[Book]: Список книг, відсортованих за borrowed_count (спадання).
        """
        return sorted(self._books.values(), key=lambda b: b.borrowed_count, reverse=True)[:top_n]

    # Управління користувачами

    def add_user(self, user_data: UserData) -> bool:
        """
        Реєструє нового члена бібліотеки.

        Аргументи:
            user_data (UserData): Параметри нового користувача.

        Повертає:
            bool: True при успішній реєстрації.

        Генерує:
            ValueError: Якщо користувач з таким ID вже існує або дані невалідні.
        """
        self._validate_user_data(user_data)
        if user_data.user_id in self._users:
            raise ValueError(f'User with ID "{user_data.user_id}" already exists.')
        self._users[user_data.user_id] = User(user_data)
        return True

    def get_user(self, user_id: str) -> Optional[User]:
        """
        Повертає користувача за ідентифікатором або None, якщо не знайдений.

        Аргументи:
            user_id (str): Ідентифікатор користувача.

        Повертає:
            Optional[User]: Об'єкт користувача або None.
        """
        return self._users.get(user_id)

    # Операції позичання / повернення

    def borrow_book(self, user_id: str, book_id: str, borrow_days: int = DEFAULT_BORROW_DAYS) -> bool:
        """
        Видає книгу користувачу (операція позичання).

        Перевіряє:
            - Наявність вільного примірника.
            - Відсутність надмірного боргу у користувача (> MAX_FINE_THRESHOLD).
            - Відсутність вже активного запису позичання цієї книги.

        Аргументи:
            user_id     (str): Ідентифікатор користувача.
            book_id     (str): Ідентифікатор книги.
            borrow_days (int): Термін позичання у днях (за замовчуванням 14).

        Повертає:
            bool: True при успішній видачі.

        Генерує:
            ValueError: При порушенні будь-якої з умов видачі.
        """
        user = self._get_user_or_raise(user_id)
        book = self._get_book_or_raise(book_id)

        # Захисні умови (Replace Nested Conditionals)
        if not book.is_available:
            raise ValueError('Book is not currently available.')
        if user.has_excessive_fines:
            raise ValueError(f'User has outstanding fines above ${MAX_FINE_THRESHOLD}.')
        if user.active_borrow_for(book_id) is not None:
            raise ValueError('User already has this book checked out.')

        due_date = datetime.date.today() + datetime.timedelta(days=borrow_days)
        record = BorrowRecord(
            book_id=book_id,
            borrow_date=str(datetime.date.today()),
            due_date=str(due_date),
        )
        user.borrowed_books.append(record)
        book.checkout()
        self._record_transaction('borrow', user_id, book_id, due_date=str(due_date))
        return True

    def return_book(self, user_id: str, book_id: str) -> float:
        """
        Приймає книгу від користувача та нараховує штраф (якщо є прострочення).

        Аргументи:
            user_id (str): Ідентифікатор користувача.
            book_id (str): Ідентифікатор книги.

        Повертає:
            float: Сума нарахованого штрафу (0.0 якщо повернення вчасне).

        Генерує:
            ValueError: Якщо активний запис позичання не знайдений.
        """
        user = self._get_user_or_raise(user_id)
        book = self._get_book_or_raise(book_id)

        record_index = user.active_borrow_index_for(book_id)
        if record_index == -1:
            raise ValueError('No active borrow record found for this book.')

        record = user.borrowed_books[record_index]
        fine = FineCalculator.calculate(record.due_date)

        self._apply_return(user, record_index, book, fine)
        self._record_transaction('return', user_id, book_id, fine=fine)
        return fine

    def pay_fine(self, user_id: str, amount: float) -> bool:
        """
        Застосовує платіж за штраф для вказаного користувача.

        Аргументи:
            user_id (str):   Ідентифікатор користувача.
            amount  (float): Сума платежу.

        Повертає:
            bool: True при успішному зарахуванні платежу.

        Генерує:
            ValueError: Якщо сума нульова, від'ємна або перевищує поточний борг.
        """
        user = self._get_user_or_raise(user_id)
        Validator.require_non_negative(amount, 'Payment amount')
        if amount == 0:
            raise ValueError('Payment amount must be positive.')
        if amount > user.fines:
            raise ValueError('Payment exceeds outstanding fine balance.')
        user.fines -= amount
        return True

    # Аналітика та звіти

    def get_stats(self) -> dict:
        """
        Збирає зведену статистику каталогу та обігу книг.

        Повертає:
            dict: Словник з такими ключами:
                - total_books_in_catalog  — кількість унікальних назв у каталозі
                - total_book_copies       — загальна кількість примірників
                - available_copies        — кількість доступних примірників
                - borrowed_copies         — кількість виданих примірників
                - total_users             — кількість зареєстрованих користувачів
                - active_users            — користувачі з активними позиченнями
                - total_transactions      — усього транзакцій у журналі
                - borrow_transactions     — кількість операцій видачі
                - return_transactions     — кількість операцій повернення
                - total_fines_collected   — загальна сума незакритих штрафів
        """
        total_copies = sum(b.quantity for b in self._books.values())
        available_copies = sum(b.available for b in self._books.values())
        active_users = sum(1 for u in self._users.values() if u.borrowed_books)
        borrow_count = sum(1 for tx in self._transactions if tx['type'] == 'borrow')
        return_count = sum(1 for tx in self._transactions if tx['type'] == 'return')
        total_fines = sum(u.fines for u in self._users.values())

        return {
            'total_books_in_catalog': len(self._books),
            'total_book_copies': total_copies,
            'available_copies': available_copies,
            'borrowed_copies': total_copies - available_copies,
            'total_users': len(self._users),
            'active_users': active_users,
            'total_transactions': len(self._transactions),
            'borrow_transactions': borrow_count,
            'return_transactions': return_count,
            'total_fines_collected': round(total_fines, 2),
        }

    def get_overdue_books(self) -> list[dict]:
        """
        Повертає список усіх поточних прострочених записів позичання.

        Повертає:
            list[dict]: Кожен елемент містить:
                - user_id      — ідентифікатор користувача
                - user_name    — ім'я користувача
                - book_id      — ідентифікатор книги
                - book_title   — назва книги
                - due_date     — кінцева дата повернення
                - days_overdue — кількість днів прострочення
        """
        today = datetime.date.today()
        overdue = []
        for user in self._users.values():
            for record in user.borrowed_books:
                if record.returned:
                    continue
                due_date = datetime.date.fromisoformat(record.due_date)
                if today <= due_date:
                    continue
                days_overdue = (today - due_date).days
                book = self._books.get(record.book_id)
                overdue.append({
                    'user_id': user.user_id,
                    'user_name': user.name,
                    'book_id': record.book_id,
                    'book_title': book.title if book else 'Unknown',
                    'due_date': record.due_date,
                    'days_overdue': days_overdue,
                })
        return overdue

    # Внутрішні допоміжні методи

    def _get_book_or_raise(self, book_id: str) -> Book:
        """
        Повертає книгу або генерує ValueError, якщо вона не знайдена.

        Аргументи:
            book_id (str): Ідентифікатор книги.

        Повертає:
            Book: Знайдений об'єкт книги.

        Генерує:
            ValueError: Якщо книга відсутня в каталозі.
        """
        book = self._books.get(book_id)
        if book is None:
            raise ValueError(f'Book "{book_id}" not found.')
        return book

    def _get_user_or_raise(self, user_id: str) -> User:
        """
        Повертає користувача або генерує ValueError, якщо він не знайдений.

        Аргументи:
            user_id (str): Ідентифікатор користувача.

        Повертає:
            User: Знайдений об'єкт користувача.

        Генерує:
            ValueError: Якщо користувач відсутній у реєстрі.
        """
        user = self._users.get(user_id)
        if user is None:
            raise ValueError(f'User "{user_id}" not found.')
        return user

    @staticmethod
    def _validate_book_data(data: BookData) -> None:
        """
        Перевіряє коректність даних книги перед додаванням.

        Аргументи:
            data (BookData): Дані для перевірки.

        Генерує:
            ValueError: Якщо book_id, title або author порожні,
                        або якщо quantity чи price від'ємні.
        """
        Validator.require_non_empty(data.book_id, 'Book ID')
        Validator.require_non_empty(data.title, 'Title')
        Validator.require_non_empty(data.author, 'Author')
        Validator.require_non_negative(data.quantity, 'Quantity')
        Validator.require_non_negative(data.price, 'Price')

    @staticmethod
    def _validate_user_data(data: UserData) -> None:
        """
        Перевіряє коректність даних користувача перед реєстрацією.

        Аргументи:
            data (UserData): Дані для перевірки.

        Генерує:
            ValueError: Якщо user_id, name або email порожні,
                        або якщо email має невірний формат.
        """
        Validator.require_non_empty(data.user_id, 'User ID')
        Validator.require_non_empty(data.name, 'Name')
        Validator.require_non_empty(data.email, 'Email')
        Validator.require_valid_email(data.email)

    def _apply_return(self, user: User, index: int, book: Book, fine: float) -> None:
        """
        Оновлює запис користувача та доступність книги при поверненні.

        Аргументи:
            user  (User):  Об'єкт користувача.
            index (int):   Індекс запису позичання у списку borrowed_books.
            book  (Book):  Об'єкт книги, що повертається.
            fine  (float): Нарахована сума штрафу.
        """
        record = user.borrowed_books[index]
        record.returned = True
        record.return_date = str(datetime.date.today())
        record.fine = fine
        user.fines += fine
        book.checkin()

    def _record_transaction(self, tx_type: str, user_id: str, book_id: str, **kwargs) -> None:
        """
        Додає запис транзакції до журналу.

        Аргументи:
            tx_type  (str): Тип транзакції: 'borrow' або 'return'.
            user_id  (str): Ідентифікатор користувача.
            book_id  (str): Ідентифікатор книги.
            **kwargs:       Додаткові поля (наприклад, due_date або fine).
        """
        entry = {
            'type': tx_type,
            'user_id': user_id,
            'book_id': book_id,
            'date': str(datetime.date.today()),
            **kwargs,
        }
        self._transactions.append(entry)