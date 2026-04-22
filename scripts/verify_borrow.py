import os
import django

# Setup Django before importing models or rest_framework
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")
django.setup()

from rest_framework.test import APIClient
from myapp.models import Book, Borrow

client = APIClient()

# 1. Create a book
book = Book.objects.create(
    title="Test Book", 
    author="Test", 
    price=10.0, 
    published_date="2026-04-15"
)
print(f"Created book: {book.id}, available: {book.is_available}")

# 2. Borrow it via the new action
response = client.post(f'/api/books/{book.id}/borrow/', {'user': 'Tester'}, format='json')
print(f"Borrow response: {response.status_code}")
if response.status_code != 200:
    print(f"Error: {response.data}")

# 3. Check book status
book.refresh_from_db()
print(f"Book available after borrow: {book.is_available}")

# 4. Attempt to borrow again
response2 = client.post(f'/api/books/{book.id}/borrow/', {'user': 'Tester2'}, format='json')
print(f"Second borrow response: {response2.status_code}")
print(f"Error detail if any: {response2.data}")

# 5. Return the book
response3 = client.post(f'/api/books/{book.id}/return/', format='json')
print(f"Return response: {response3.status_code}")
book.refresh_from_db()
print(f"Book available after return: {book.is_available}")

if not book.is_available == False and response2.status_code == 400 and book.is_available == True:
    # Actually the logic is: after second borrow it remains False, then after return it becomes True
    pass

if response.status_code == 200 and response2.status_code == 400 and book.is_available == True:
    print("SUCCESS: Borrow and Return features verified.")
else:
    print("FAILURE: Borrow/Return feature logic failed.")
