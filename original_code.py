import datetime
import json
import os

# Global variables - bad practice
data = []
u = []
t = []
total = 0
d = {}

def load(f):
    global data, u, t, total, d
    try:
        file = open(f, 'r')
        content = file.read()
        file.close()
        parsed = json.loads(content)
        data = parsed.get('books', [])
        u = parsed.get('users', [])
        t = parsed.get('transactions', [])
        d = {}
        for book in data:
            d[book['id']] = book
        total = 0
        for book in data:
            total = total + book.get('quantity', 0)
    except:
        data = []
        u = []
        t = []
        d = {}
        total = 0

def save(f):
    global data, u, t
    try:
        file = open(f, 'w')
        content = json.dumps({'books': data, 'users': u, 'transactions': t}, indent=2)
        file.write(content)
        file.close()
    except Exception as e:
        print('Error saving: ' + str(e))

def add_book(id, title, a, yr, g, qty, p):
    global data, d, total
    # Check if book exists
    flag = False
    for i in range(len(data)):
        if data[i]['id'] == id:
            flag = True
            break
    if flag == True:
        print('Book already exists')
        return False
    if id == None or id == '':
        print('ID cannot be empty')
        return False
    if title == None or title == '':
        print('Title cannot be empty')
        return False
    if a == None or a == '':
        print('Author cannot be empty')
        return False
    if qty < 0:
        print('Quantity cannot be negative')
        return False
    if p < 0:
        print('Price cannot be negative')
        return False
    # Create book object
    book = {}
    book['id'] = id
    book['title'] = title
    book['author'] = a
    book['year'] = yr
    book['genre'] = g
    book['quantity'] = qty
    book['price'] = p
    book['available'] = qty
    book['borrowed_count'] = 0
    data.append(book)
    d[id] = book
    total = total + qty
    print('Book added successfully: ' + title)
    return True

def add_user(id, n, e, ph, addr):
    global u
    # Check if user exists
    flag2 = False
    for i in range(len(u)):
        if u[i]['id'] == id:
            flag2 = True
    if flag2:
        print('User already exists')
        return False
    if id == None or id == '':
        print('ID cannot be empty')
        return False
    if n == None or n == '':
        print('Name cannot be empty')
        return False
    if e == None or e == '':
        print('Email cannot be empty')
        return False
    if '@' not in e:
        print('Invalid email format')
        return False
    # Create user object
    usr = {}
    usr['id'] = id
    usr['name'] = n
    usr['email'] = e
    usr['phone'] = ph
    usr['address'] = addr
    usr['borrowed_books'] = []
    usr['fines'] = 0.0
    usr['registration_date'] = str(datetime.date.today())
    u.append(usr)
    print('User registered: ' + n)
    return True

def borrow(uid, bid, days):
    global data, u, t, d, total
    # Find user
    found_user = None
    for i in range(len(u)):
        if u[i]['id'] == uid:
            found_user = u[i]
            break
    if found_user == None:
        print('User not found')
        return False
    # Find book
    found_book = None
    for i in range(len(data)):
        if data[i]['id'] == bid:
            found_book = data[i]
            break
    if found_book == None:
        print('Book not found')
        return False
    if found_book['available'] <= 0:
        print('Book not available')
        return False
    if found_user['fines'] > 50:
        print('User has too many fines')
        return False
    # Check if user already borrowed this book
    already = False
    for b in found_user['borrowed_books']:
        if b['book_id'] == bid:
            already = True
    if already:
        print('User already borrowed this book')
        return False
    # Process borrow
    found_book['available'] = found_book['available'] - 1
    found_book['borrowed_count'] = found_book['borrowed_count'] + 1
    due = datetime.date.today() + datetime.timedelta(days=days)
    borrow_record = {'book_id': bid, 'borrow_date': str(datetime.date.today()), 'due_date': str(due), 'returned': False}
    found_user['borrowed_books'].append(borrow_record)
    # Transaction
    tx = {'type': 'borrow', 'user_id': uid, 'book_id': bid, 'date': str(datetime.date.today()), 'due_date': str(due)}
    t.append(tx)
    print('Book borrowed successfully')
    return True

def ret(uid, bid):
    global data, u, t, d
    # Find user
    found_user = None
    for i in range(len(u)):
        if u[i]['id'] == uid:
            found_user = u[i]
            break
    if found_user == None:
        print('User not found')
        return False
    # Find book
    found_book = None
    for i in range(len(data)):
        if data[i]['id'] == bid:
            found_book = data[i]
            break
    if found_book == None:
        print('Book not found')
        return False
    # Find borrow record
    rec = None
    idx = -1
    for i in range(len(found_user['borrowed_books'])):
        if found_user['borrowed_books'][i]['book_id'] == bid and not found_user['borrowed_books'][i]['returned']:
            rec = found_user['borrowed_books'][i]
            idx = i
            break
    if rec == None:
        print('No active borrow record found')
        return False
    # Calculate fine
    fine = 0.0
    due = datetime.date.fromisoformat(rec['due_date'])
    today = datetime.date.today()
    if today > due:
        days_late = (today - due).days
        if days_late <= 7:
            fine = days_late * 0.5
        elif days_late <= 30:
            fine = 7 * 0.5 + (days_late - 7) * 1.0
        else:
            fine = 7 * 0.5 + 23 * 1.0 + (days_late - 30) * 2.0
    # Update records
    found_user['borrowed_books'][idx]['returned'] = True
    found_user['borrowed_books'][idx]['return_date'] = str(today)
    found_user['borrowed_books'][idx]['fine'] = fine
    found_user['fines'] = found_user['fines'] + fine
    found_book['available'] = found_book['available'] + 1
    tx = {'type': 'return', 'user_id': uid, 'book_id': bid, 'date': str(today), 'fine': fine}
    t.append(tx)
    if fine > 0:
        print('Book returned. Fine: $' + str(round(fine, 2)))
    else:
        print('Book returned successfully. No fine.')
    return True

def search(q, by):
    global data
    res = []
    q_low = q.lower()
    for book in data:
        if by == 'title':
            if q_low in book['title'].lower():
                res.append(book)
        elif by == 'author':
            if q_low in book['author'].lower():
                res.append(book)
        elif by == 'genre':
            if q_low in book['genre'].lower():
                res.append(book)
        elif by == 'id':
            if q_low in book['id'].lower():
                res.append(book)
    return res

def get_stats():
    global data, u, t, total
    # Count various things - duplicated logic
    total_books = 0
    total_available = 0
    total_borrowed = 0
    for book in data:
        total_books = total_books + book['quantity']
        total_available = total_available + book['available']
        total_borrowed = total_borrowed + (book['quantity'] - book['available'])
    # Count users
    total_users = len(u)
    active_users = 0
    for user in u:
        if len(user['borrowed_books']) > 0:
            active_users = active_users + 1
    # Count transactions
    total_tx = len(t)
    borrow_tx = 0
    return_tx = 0
    for tx in t:
        if tx['type'] == 'borrow':
            borrow_tx = borrow_tx + 1
        elif tx['type'] == 'return':
            return_tx = return_tx + 1
    # Calculate total fines
    total_fines = 0.0
    for user in u:
        total_fines = total_fines + user['fines']
    stats = {
        'total_books_in_catalog': len(data),
        'total_book_copies': total_books,
        'available_copies': total_available,
        'borrowed_copies': total_borrowed,
        'total_users': total_users,
        'active_users': active_users,
        'total_transactions': total_tx,
        'borrow_transactions': borrow_tx,
        'return_transactions': return_tx,
        'total_fines_collected': round(total_fines, 2)
    }
    return stats

def get_overdue():
    global u, data
    overdue_list = []
    today = datetime.date.today()
    for user in u:
        for borrow_rec in user['borrowed_books']:
            if not borrow_rec['returned']:
                due = datetime.date.fromisoformat(borrow_rec['due_date'])
                if today > due:
                    days_late = (today - due).days
                    # Find book title
                    book_title = 'Unknown'
                    for book in data:
                        if book['id'] == borrow_rec['book_id']:
                            book_title = book['title']
                            break
                    overdue_list.append({
                        'user_id': user['id'],
                        'user_name': user['name'],
                        'book_id': borrow_rec['book_id'],
                        'book_title': book_title,
                        'due_date': borrow_rec['due_date'],
                        'days_overdue': days_late
                    })
    return overdue_list

def pay_fine(uid, amount):
    global u
    found_user = None
    for i in range(len(u)):
        if u[i]['id'] == uid:
            found_user = u[i]
            break
    if found_user == None:
        print('User not found')
        return False
    if amount <= 0:
        print('Amount must be positive')
        return False
    if amount > found_user['fines']:
        print('Amount exceeds outstanding fines')
        return False
    found_user['fines'] = found_user['fines'] - amount
    print('Fine payment processed: $' + str(round(amount, 2)))
    return True

def print_book(bid):
    global d
    if bid not in d:
        print('Book not found')
        return
    book = d[bid]
    print('=== Book Details ===')
    print('ID: ' + book['id'])
    print('Title: ' + book['title'])
    print('Author: ' + book['author'])
    print('Year: ' + str(book['year']))
    print('Genre: ' + book['genre'])
    print('Total copies: ' + str(book['quantity']))
    print('Available: ' + str(book['available']))
    print('Times borrowed: ' + str(book['borrowed_count']))
    print('Price: $' + str(book['price']))

def print_user(uid):
    global u
    found_user = None
    for user in u:
        if user['id'] == uid:
            found_user = user
            break
    if found_user == None:
        print('User not found')
        return
    print('=== User Details ===')
    print('ID: ' + found_user['id'])
    print('Name: ' + found_user['name'])
    print('Email: ' + found_user['email'])
    print('Phone: ' + found_user['phone'])
    print('Fines: $' + str(round(found_user['fines'], 2)))
    print('Books borrowed: ' + str(len(found_user['borrowed_books'])))
    print('Registration date: ' + found_user['registration_date'])

def remove_book(bid):
    global data, d, total
    idx = -1
    for i in range(len(data)):
        if data[i]['id'] == bid:
            idx = i
            break
    if idx == -1:
        print('Book not found')
        return False
    qty = data[idx]['quantity']
    data.pop(idx)
    if bid in d:
        del d[bid]
    total = total - qty
    print('Book removed')
    return True

def get_popular(n):
    global data
    # Sort books by borrowed_count
    sorted_books = []
    for book in data:
        sorted_books.append(book)
    # Bubble sort (inefficient)
    for i in range(len(sorted_books)):
        for j in range(len(sorted_books) - 1 - i):
            if sorted_books[j]['borrowed_count'] < sorted_books[j+1]['borrowed_count']:
                temp = sorted_books[j]
                sorted_books[j] = sorted_books[j+1]
                sorted_books[j+1] = temp
    return sorted_books[:n]

def update_book(bid, title=None, a=None, yr=None, g=None, qty=None, p=None):
    global data, d, total
    found = None
    for book in data:
        if book['id'] == bid:
            found = book
            break
    if found == None:
        print('Book not found')
        return False
    if title != None:
        found['title'] = title
    if a != None:
        found['author'] = a
    if yr != None:
        found['year'] = yr
    if g != None:
        found['genre'] = g
    if qty != None:
        if qty < 0:
            print('Quantity cannot be negative')
            return False
        old_qty = found['quantity']
        diff = qty - old_qty
        found['quantity'] = qty
        found['available'] = found['available'] + diff
        total = total + diff
    if p != None:
        if p < 0:
            print('Price cannot be negative')
            return False
        found['price'] = p
    print('Book updated')
    return True