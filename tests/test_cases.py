"""
Unit Tests for Library Management System
Covers both original_code.py and refactored_code.py

Run:
    python -m pytest tests/test_cases.py -v
    # or
    python tests/test_cases.py
"""

import datetime
import sys
import os
import unittest

# Allow imports from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# ── Refactored imports ────────────────────────────────────────────────────────
from refactored_code import (
    Library, Book, User, BookData, UserData, FineCalculator,
    FINE_RATE_FIRST_WEEK, FINE_RATE_SECOND_PERIOD, FINE_RATE_EXTENDED,
    MAX_FINE_THRESHOLD,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_library() -> Library:
    """Return a fresh Library instance with one book and one user pre-loaded."""
    lib = Library()
    lib.add_book(BookData('B001', 'Clean Code', 'Robert Martin', 2008, 'Programming', 5, 29.99))
    lib.add_book(BookData('B002', 'The Pragmatic Programmer', 'Hunt & Thomas', 1999, 'Programming', 3, 34.99))
    lib.add_user(UserData('U001', 'Alice Smith', 'alice@example.com', '555-0101', '1 Main St'))
    lib.add_user(UserData('U002', 'Bob Jones', 'bob@example.com', '555-0102', '2 Oak Ave'))
    return lib


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Book Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestBookCreation(unittest.TestCase):

    def test_add_book_success(self):
        lib = Library()
        result = lib.add_book(BookData('B001', 'Test Book', 'Author', 2020, 'Fiction', 10, 15.0))
        self.assertTrue(result)
        self.assertIsNotNone(lib.get_book('B001'))

    def test_add_book_sets_available_equal_to_quantity(self):
        lib = Library()
        lib.add_book(BookData('B001', 'Test', 'Auth', 2020, 'F', 7, 10.0))
        self.assertEqual(lib.get_book('B001').available, 7)

    def test_add_duplicate_book_raises(self):
        lib = Library()
        lib.add_book(BookData('B001', 'Test', 'Auth', 2020, 'F', 1, 10.0))
        with self.assertRaises(ValueError):
            lib.add_book(BookData('B001', 'Other', 'Auth2', 2021, 'F', 1, 5.0))

    def test_add_book_empty_id_raises(self):
        lib = Library()
        with self.assertRaises(ValueError):
            lib.add_book(BookData('', 'Title', 'Author', 2020, 'Genre', 1, 10.0))

    def test_add_book_empty_title_raises(self):
        lib = Library()
        with self.assertRaises(ValueError):
            lib.add_book(BookData('B001', '', 'Author', 2020, 'Genre', 1, 10.0))

    def test_add_book_negative_quantity_raises(self):
        lib = Library()
        with self.assertRaises(ValueError):
            lib.add_book(BookData('B001', 'Title', 'Auth', 2020, 'G', -1, 10.0))

    def test_add_book_negative_price_raises(self):
        lib = Library()
        with self.assertRaises(ValueError):
            lib.add_book(BookData('B001', 'Title', 'Auth', 2020, 'G', 1, -5.0))

    def test_remove_book_success(self):
        lib = make_library()
        lib.remove_book('B001')
        self.assertIsNone(lib.get_book('B001'))

    def test_remove_nonexistent_book_raises(self):
        lib = Library()
        with self.assertRaises(ValueError):
            lib.remove_book('GHOST')

    def test_update_book_title(self):
        lib = make_library()
        lib.update_book('B001', title='New Title')
        self.assertEqual(lib.get_book('B001').title, 'New Title')

    def test_update_book_quantity_adjusts_available(self):
        lib = make_library()
        lib.update_book('B001', quantity=10)
        self.assertEqual(lib.get_book('B001').quantity, 10)
        self.assertEqual(lib.get_book('B001').available, 10)


# ═══════════════════════════════════════════════════════════════════════════════
# 2. User Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestUserRegistration(unittest.TestCase):

    def test_add_user_success(self):
        lib = Library()
        result = lib.add_user(UserData('U001', 'Alice', 'alice@x.com', '555', 'Addr'))
        self.assertTrue(result)
        self.assertIsNotNone(lib.get_user('U001'))

    def test_add_duplicate_user_raises(self):
        lib = Library()
        lib.add_user(UserData('U001', 'Alice', 'alice@x.com', '555', 'Addr'))
        with self.assertRaises(ValueError):
            lib.add_user(UserData('U001', 'Bob', 'bob@x.com', '999', 'Other'))

    def test_add_user_invalid_email_raises(self):
        lib = Library()
        with self.assertRaises(ValueError):
            lib.add_user(UserData('U001', 'Alice', 'not-an-email', '555', 'Addr'))

    def test_add_user_empty_name_raises(self):
        lib = Library()
        with self.assertRaises(ValueError):
            lib.add_user(UserData('U001', '', 'alice@x.com', '555', 'Addr'))

    def test_new_user_has_zero_fines(self):
        lib = Library()
        lib.add_user(UserData('U001', 'Alice', 'alice@x.com', '555', 'Addr'))
        self.assertEqual(lib.get_user('U001').fines, 0.0)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Borrow Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestBorrowing(unittest.TestCase):

    def test_borrow_success(self):
        lib = make_library()
        result = lib.borrow_book('U001', 'B001')
        self.assertTrue(result)

    def test_borrow_decrements_available(self):
        lib = make_library()
        before = lib.get_book('B001').available
        lib.borrow_book('U001', 'B001')
        self.assertEqual(lib.get_book('B001').available, before - 1)

    def test_borrow_increments_borrowed_count(self):
        lib = make_library()
        lib.borrow_book('U001', 'B001')
        self.assertEqual(lib.get_book('B001').borrowed_count, 1)

    def test_borrow_nonexistent_book_raises(self):
        lib = make_library()
        with self.assertRaises(ValueError):
            lib.borrow_book('U001', 'GHOST')

    def test_borrow_nonexistent_user_raises(self):
        lib = make_library()
        with self.assertRaises(ValueError):
            lib.borrow_book('GHOST', 'B001')

    def test_borrow_unavailable_book_raises(self):
        lib = Library()
        lib.add_book(BookData('B001', 'Rare', 'Auth', 2020, 'G', 1, 10.0))
        lib.add_user(UserData('U001', 'Alice', 'alice@x.com', '555', 'Addr'))
        lib.add_user(UserData('U002', 'Bob', 'bob@x.com', '555', 'Addr'))
        lib.borrow_book('U001', 'B001')
        with self.assertRaises(ValueError):
            lib.borrow_book('U002', 'B001')

    def test_borrow_same_book_twice_raises(self):
        lib = make_library()
        lib.borrow_book('U001', 'B001')
        with self.assertRaises(ValueError):
            lib.borrow_book('U001', 'B001')

    def test_borrow_blocked_by_high_fines(self):
        lib = make_library()
        lib.get_user('U001').fines = MAX_FINE_THRESHOLD + 1
        with self.assertRaises(ValueError):
            lib.borrow_book('U001', 'B001')


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Return Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestReturning(unittest.TestCase):

    def test_return_success(self):
        lib = make_library()
        lib.borrow_book('U001', 'B001')
        fine = lib.return_book('U001', 'B001')
        self.assertIsInstance(fine, float)

    def test_return_increments_available(self):
        lib = make_library()
        lib.borrow_book('U001', 'B001')
        before = lib.get_book('B001').available
        lib.return_book('U001', 'B001')
        self.assertEqual(lib.get_book('B001').available, before + 1)

    def test_return_without_borrow_raises(self):
        lib = make_library()
        with self.assertRaises(ValueError):
            lib.return_book('U001', 'B001')

    def test_return_on_time_no_fine(self):
        lib = make_library()
        lib.borrow_book('U001', 'B001', borrow_days=14)
        fine = lib.return_book('U001', 'B001')
        self.assertEqual(fine, 0.0)


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Fine Calculator Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestFineCalculator(unittest.TestCase):

    def _due(self, days_ago: int) -> str:
        return str(datetime.date.today() - datetime.timedelta(days=days_ago))

    def test_no_fine_when_on_time(self):
        future = str(datetime.date.today() + datetime.timedelta(days=3))
        self.assertEqual(FineCalculator.calculate(future), 0.0)

    def test_fine_first_week(self):
        fine = FineCalculator.calculate(self._due(5))
        self.assertAlmostEqual(fine, 5 * FINE_RATE_FIRST_WEEK, places=5)

    def test_fine_boundary_7_days(self):
        fine = FineCalculator.calculate(self._due(7))
        self.assertAlmostEqual(fine, 7 * FINE_RATE_FIRST_WEEK, places=5)

    def test_fine_second_period(self):
        fine = FineCalculator.calculate(self._due(14))
        expected = 7 * FINE_RATE_FIRST_WEEK + 7 * FINE_RATE_SECOND_PERIOD
        self.assertAlmostEqual(fine, expected, places=5)

    def test_fine_extended_period(self):
        fine = FineCalculator.calculate(self._due(35))
        expected = (7 * FINE_RATE_FIRST_WEEK
                    + 23 * FINE_RATE_SECOND_PERIOD
                    + 5 * FINE_RATE_EXTENDED)
        self.assertAlmostEqual(fine, expected, places=5)

    def test_fine_due_today_no_fine(self):
        today = str(datetime.date.today())
        self.assertEqual(FineCalculator.calculate(today), 0.0)


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Search Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestSearch(unittest.TestCase):

    def test_search_by_title(self):
        lib = make_library()
        results = lib.search_books('clean', 'title')
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, 'Clean Code')

    def test_search_by_author(self):
        lib = make_library()
        results = lib.search_books('martin', 'author')
        self.assertEqual(len(results), 1)

    def test_search_by_genre(self):
        lib = make_library()
        results = lib.search_books('programming', 'genre')
        self.assertEqual(len(results), 2)

    def test_search_by_id(self):
        lib = make_library()
        results = lib.search_books('B002', 'id')
        self.assertEqual(len(results), 1)

    def test_search_no_results(self):
        lib = make_library()
        results = lib.search_books('zzznotfound', 'title')
        self.assertEqual(results, [])

    def test_search_invalid_field_raises(self):
        lib = make_library()
        with self.assertRaises(ValueError):
            lib.search_books('test', 'invalid_field')


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Statistics & Reporting Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestStatistics(unittest.TestCase):

    def test_stats_total_catalog(self):
        lib = make_library()
        stats = lib.get_stats()
        self.assertEqual(stats['total_books_in_catalog'], 2)

    def test_stats_total_copies(self):
        lib = make_library()
        stats = lib.get_stats()
        self.assertEqual(stats['total_book_copies'], 8)  # 5 + 3

    def test_stats_after_borrow(self):
        lib = make_library()
        lib.borrow_book('U001', 'B001')
        stats = lib.get_stats()
        self.assertEqual(stats['borrowed_copies'], 1)
        self.assertEqual(stats['borrow_transactions'], 1)

    def test_get_popular_books(self):
        lib = make_library()
        lib.borrow_book('U001', 'B001')
        lib.borrow_book('U001', 'B002')
        lib.borrow_book('U002', 'B001')
        lib.return_book('U001', 'B001')
        lib.return_book('U002', 'B001')
        popular = lib.get_popular_books(1)
        self.assertEqual(popular[0].book_id, 'B001')

    def test_get_overdue_empty_when_no_borrows(self):
        lib = make_library()
        self.assertEqual(lib.get_overdue_books(), [])

    def test_pay_fine_success(self):
        lib = make_library()
        lib.get_user('U001').fines = 20.0
        lib.pay_fine('U001', 10.0)
        self.assertAlmostEqual(lib.get_user('U001').fines, 10.0)

    def test_pay_fine_exceeds_balance_raises(self):
        lib = make_library()
        lib.get_user('U001').fines = 5.0
        with self.assertRaises(ValueError):
            lib.pay_fine('U001', 100.0)

    def test_pay_fine_zero_raises(self):
        lib = make_library()
        lib.get_user('U001').fines = 10.0
        with self.assertRaises(ValueError):
            lib.pay_fine('U001', 0.0)


if __name__ == '__main__':
    unittest.main(verbosity=2)