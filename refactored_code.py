import datetime
import json
from dataclasses import dataclass, field, asdict
from typing import Optional

FINE_RATE_FIRST_WEEK = 0.5       # $ per day, days 1–7
FINE_RATE_SECOND_PERIOD = 1.0    # $ per day, days 8–30
FINE_RATE_EXTENDED = 2.0         # $ per day, day 31+
MAX_FINE_THRESHOLD = 50.0        # $ max outstanding fines before borrow blocked
DEFAULT_BORROW_DAYS = 14

@dataclass
class BookData:
    """Value object carrying book creation parameters."""
    book_id: str
    title: str
    author: str
    year: int
    genre: str
    quantity: int
    price: float


@dataclass
class UserData:
    """Value object carrying user registration parameters."""
    user_id: str
    name: str
    email: str
    phone: str
    address: str


@dataclass
class BorrowRecord:
    book_id: str
    borrow_date: str
    due_date: str
    returned: bool = False
    return_date: Optional[str] = None
    fine: float = 0.0

class Book:
    """Represents a library book with its inventory state."""

    def __init__(self, data: BookData) -> None:
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
        return self.available > 0

    def checkout(self) -> None:
        """Decrement available count and increment borrow counter."""
        self.available -= 1
        self.borrowed_count += 1

    def checkin(self) -> None:
        """Increment available count on return."""
        self.available += 1

    def update_quantity(self, new_quantity: int) -> None:
        """Adjust quantity and available count by the difference."""
        difference = new_quantity - self.quantity
        self.quantity = new_quantity
        self.available += difference

    def to_dict(self) -> dict:
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
    """Represents a library member."""

    def __init__(self, data: UserData) -> None:
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
        return self.fines > MAX_FINE_THRESHOLD

    def active_borrow_for(self, book_id: str) -> Optional[BorrowRecord]:
        """Return the active (unreturned) borrow record for a given book, or None."""
        return next(
            (rec for rec in self.borrowed_books
             if rec.book_id == book_id and not rec.returned),
            None
        )

    def active_borrow_index_for(self, book_id: str) -> int:
        """Return index of active borrow record, or -1 if not found."""
        for i, rec in enumerate(self.borrowed_books):
            if rec.book_id == book_id and not rec.returned:
                return i
        return -1

    def to_dict(self) -> dict:
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
    """Encapsulates the tiered fine calculation logic."""

    @staticmethod
    def calculate(due_date_str: str) -> float:
        due_date = datetime.date.fromisoformat(due_date_str)
        today = datetime.date.today()
        if today <= due_date:
            return 0.0
        days_late = (today - due_date).days
        return FineCalculator._tiered_fine(days_late)

    @staticmethod
    def _tiered_fine(days_late: int) -> float:
        """Apply tiered daily rates based on how many days overdue."""
        first_week = min(days_late, 7)
        second_period = max(0, min(days_late - 7, 23))   # days 8–30
        extended = max(0, days_late - 30)                 # day 31+

        return (
            first_week * FINE_RATE_FIRST_WEEK
            + second_period * FINE_RATE_SECOND_PERIOD
            + extended * FINE_RATE_EXTENDED
        )

class Validator:

    @staticmethod
    def require_non_empty(value: str, field_name: str) -> None:
        if not value:
            raise ValueError(f'{field_name} cannot be empty.')

    @staticmethod
    def require_non_negative(value: float, field_name: str) -> None:
        if value < 0:
            raise ValueError(f'{field_name} cannot be negative.')

    @staticmethod
    def require_valid_email(email: str) -> None:
        if '@' not in email:
            raise ValueError('Invalid email format.')

class Library:
    """
    Central repository and service layer for the library system.

    All state is instance-level; no module globals are used.
    """

    def __init__(self) -> None:
        self._books: dict[str, Book] = {}
        self._users: dict[str, User] = {}
        self._transactions: list[dict] = []

    def load(self, filepath: str) -> None:
        """Load library state from a JSON file."""
        with open(filepath, 'r', encoding='utf-8') as fh:
            payload = json.load(fh)
        self._books = {b['id']: Book.from_dict(b) for b in payload.get('books', [])}
        self._users = {u['id']: User.from_dict(u) for u in payload.get('users', [])}
        self._transactions = payload.get('transactions', [])

    def save(self, filepath: str) -> None:
        """Persist library state to a JSON file."""
        payload = {
            'books': [b.to_dict() for b in self._books.values()],
            'users': [u.to_dict() for u in self._users.values()],
            'transactions': self._transactions,
        }
        with open(filepath, 'w', encoding='utf-8') as fh:
            json.dump(payload, fh, indent=2)

    def add_book(self, book_data: BookData) -> bool:
        """Register a new book in the catalog."""
        self._validate_book_data(book_data)
        if book_data.book_id in self._books:
            raise ValueError(f'Book with ID "{book_data.book_id}" already exists.')
        self._books[book_data.book_id] = Book(book_data)
        return True

    def remove_book(self, book_id: str) -> bool:
        """Remove a book from the catalog."""
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
        """Update one or more fields on an existing book."""
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
        return self._books.get(book_id)

    def search_books(self, query: str, search_by: str) -> list[Book]:
        """Search the catalog by title, author, genre, or id."""
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
        """Return the top N most-borrowed books (Refactoring #9: better algorithm)."""
        return sorted(self._books.values(), key=lambda b: b.borrowed_count, reverse=True)[:top_n]

    def add_user(self, user_data: UserData) -> bool:
        """Register a new library member."""
        self._validate_user_data(user_data)
        if user_data.user_id in self._users:
            raise ValueError(f'User with ID "{user_data.user_id}" already exists.')
        self._users[user_data.user_id] = User(user_data)
        return True

    def get_user(self, user_id: str) -> Optional[User]:
        return self._users.get(user_id)

    def borrow_book(self, user_id: str, book_id: str, borrow_days: int = DEFAULT_BORROW_DAYS) -> bool:
        """Check out a book to a user."""
        user = self._get_user_or_raise(user_id)
        book = self._get_book_or_raise(book_id)

        # Guard clauses (Refactoring #10: Replace Nested Conditionals)
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
        """Check in a returned book and calculate any fine. Returns fine amount."""
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
        """Apply a fine payment for a user."""
        user = self._get_user_or_raise(user_id)
        Validator.require_non_negative(amount, 'Payment amount')
        if amount == 0:
            raise ValueError('Payment amount must be positive.')
        if amount > user.fines:
            raise ValueError('Payment exceeds outstanding fine balance.')
        user.fines -= amount
        return True

    def get_stats(self) -> dict:
        """Aggregate catalog and circulation statistics."""
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
        """Return a list of all currently overdue borrow records."""
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

    def _get_book_or_raise(self, book_id: str) -> Book:
        book = self._books.get(book_id)
        if book is None:
            raise ValueError(f'Book "{book_id}" not found.')
        return book

    def _get_user_or_raise(self, user_id: str) -> User:
        user = self._users.get(user_id)
        if user is None:
            raise ValueError(f'User "{user_id}" not found.')
        return user

    @staticmethod
    def _validate_book_data(data: BookData) -> None:
        Validator.require_non_empty(data.book_id, 'Book ID')
        Validator.require_non_empty(data.title, 'Title')
        Validator.require_non_empty(data.author, 'Author')
        Validator.require_non_negative(data.quantity, 'Quantity')
        Validator.require_non_negative(data.price, 'Price')

    @staticmethod
    def _validate_user_data(data: UserData) -> None:
        Validator.require_non_empty(data.user_id, 'User ID')
        Validator.require_non_empty(data.name, 'Name')
        Validator.require_non_empty(data.email, 'Email')
        Validator.require_valid_email(data.email)

    def _apply_return(self, user: User, index: int, book: Book, fine: float) -> None:
        """Update user record and book availability on return."""
        record = user.borrowed_books[index]
        record.returned = True
        record.return_date = str(datetime.date.today())
        record.fine = fine
        user.fines += fine
        book.checkin()

    def _record_transaction(self, tx_type: str, user_id: str, book_id: str, **kwargs) -> None:
        """Append a transaction entry to the ledger."""
        entry = {
            'type': tx_type,
            'user_id': user_id,
            'book_id': book_id,
            'date': str(datetime.date.today()),
            **kwargs,
        }
        self._transactions.append(entry)