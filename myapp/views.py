import logging

from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import viewsets, serializers, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.models import Token
from .models import Book, Borrow
from .serializers import BookSerializer, BorrowSerializer

logger = logging.getLogger(__name__)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        name = request.data.get('name', '')

        if not email or not password:
            logger.warning("Register attempt with missing fields")
            return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=email).exists():
            logger.warning("Register attempt for existing user: %s", email)
            return Response({"error": "User already exists"}, status=status.HTTP_400_BAD_REQUEST)

        User.objects.create_user(username=email, email=email, password=password, first_name=name)
        logger.info("New user registered: %s", email)
        return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        user = authenticate(username=email, password=password)
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            logger.info("User logged in: %s", email)
            return Response({"token": token.key, "is_staff": user.is_staff}, status=status.HTTP_200_OK)

        logger.warning("Failed login attempt for: %s", email)
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

    def perform_create(self, serializer):
        copies_total = serializer.validated_data.get('copies_total', 1)
        serializer.save(copies_available=copies_total, is_available=copies_total > 0)

    @action(detail=True, methods=['post'])
    def borrow(self, request, pk=None):
        book = self.get_object()

        if book.copies_available <= 0:
            logger.warning("User %s tried to borrow unavailable book: %s", request.user.username, book.title)
            return Response({"detail": "No copies available."}, status=status.HTTP_400_BAD_REQUEST)

        if Borrow.objects.filter(book=book, user=request.user.username, returned_at__isnull=True).exists():
            return Response({"detail": "You already have this book borrowed."}, status=status.HTTP_400_BAD_REQUEST)

        Borrow.objects.create(book=book, user=request.user.username)
        book.copies_available -= 1
        book.is_available = book.copies_available > 0
        book.save()

        logger.info("User %s borrowed book: %s (%d copies left)", request.user.username, book.title, book.copies_available)
        return Response({"detail": f"Book '{book.title}' borrowed successfully."})

    @action(detail=True, methods=['post'], url_path='return')
    def return_book(self, request, pk=None):
        book = self.get_object()

        active_borrow = Borrow.objects.filter(
            book=book, user=request.user.username, returned_at__isnull=True
        ).first()

        if not active_borrow:
            return Response({"detail": "You have not borrowed this book."}, status=status.HTTP_400_BAD_REQUEST)

        active_borrow.returned_at = timezone.now()
        active_borrow.save()

        book.copies_available += 1
        book.is_available = True
        book.save()

        logger.info("User %s returned book: %s (%d copies now available)", request.user.username, book.title, book.copies_available)
        return Response({"detail": f"Book '{book.title}' returned successfully."})


class BorrowViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Borrow.objects.select_related('book').order_by('-borrowed_at')
    serializer_class = BorrowSerializer
