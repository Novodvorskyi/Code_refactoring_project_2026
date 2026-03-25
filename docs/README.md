# Рефакторинг коду: Система управління бібліотекою

## Опис проєкту

Навчальний проєкт з рефакторингу. Предмет — повнофункціональна система управління бібліотекою: каталог книг, реєстрація читачів, видача/повернення, нарахування штрафів, статистика.

Оригінальний код (`original_code.py`) — процедурний, ~311 рядків, 6 глобальних змінних, 12 виявлених запахів коду.  
Рефакторований код (`refactored_code.py`) — об'єктно-орієнтований, ~398 рядків, 6 класів, 0 глобальних змінних.

---

## Структура файлів

```
project-root/
├── original_code.py        # Вихідний код з code smells
├── refactored_code.py      # Рефакторований код
├── tests/
│   └── test_cases.py       # 48 юніт-тестів
├── docs/
│   └── refactoring_report.md  # Детальний звіт
└── README.md
```

---

## Запуск тестів

```bash
# Встановити pytest (якщо не встановлено)
pip install pytest

# Запустити всі тести
python -m pytest tests/test_cases.py -v

# Або без pytest
python tests/test_cases.py
```

Очікуваний результат: **48 passed**.

---

## Застосовані техніки рефакторингу (12 технік)

| # | Техніка | Ефект |
|---|---|---|
| 1 | Replace Global Variables with Encapsulation | Клас `Library` замість 6 глобальних змінних |
| 2 | Extract Class | `Book`, `User`, `FineCalculator`, `Validator` |
| 3 | Rename Variables / Methods | `a`→`author`, `u`→`users`, `ph`→`phone` тощо |
| 4 | Introduce Parameter Object | `BookData`, `UserData` dataclass замість 7-аргументних функцій |
| 5 | Extract Method | `_get_book_or_raise`, `_get_user_or_raise` замість 9 дубльованих блоків |
| 6 | Replace Magic Numbers with Constants | `FINE_RATE_FIRST_WEEK`, `MAX_FINE_THRESHOLD` тощо |
| 7 | Single Responsibility (Extract Class) | `FineCalculator` відокремлений від логіки повернення |
| 8 | Decompose Conditional | Тернарна математика штрафів замість if/elif/else |
| 9 | Replace Algorithm | `sorted()` (Timsort O(n log n)) замість bubble sort O(n²) |
| 10 | Replace Nested Conditionals with Guard Clauses | Плоска структура `borrow_book` |
| 11 | Consolidate Duplicate Conditional Fragments | Словник `field_map` у `search_books` |
| 12 | Replace Bare Except | `with open(...)` + специфічні виключення |

---

## Ключові покращення

- Рівень вкладеності: **4 → 1** (−75%)
- Середня довжина методу: **22 → 9 рядків** (−59%)
- Глобальні змінні: **6 → 0**
- Дублювання блоків пошуку: **9 → 0**
- Тестове покриття: **48 тестів, 100% pass**
