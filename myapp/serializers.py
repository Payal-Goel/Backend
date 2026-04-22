from rest_framework import serializers
from .models import Book, Borrow


class BookSerializer(serializers.ModelSerializer):
    active_borrower_count = serializers.SerializerMethodField()
    is_borrowed_by_me = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'author', 'price', 'published_date',
            'copies_total', 'copies_available', 'is_available',
            'active_borrower_count', 'is_borrowed_by_me',
        ]
        read_only_fields = ['copies_available', 'is_available']

    def get_active_borrower_count(self, obj):
        return obj.borrows.filter(returned_at__isnull=True).count()

    def get_is_borrowed_by_me(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.borrows.filter(returned_at__isnull=True, user=request.user.username).exists()


class BorrowSerializer(serializers.ModelSerializer):
    book_title = serializers.CharField(source='book.title', read_only=True)
    book_author = serializers.CharField(source='book.author', read_only=True)

    class Meta:
        model = Borrow
        fields = ['id', 'book', 'book_title', 'book_author', 'user', 'borrowed_at', 'returned_at']
