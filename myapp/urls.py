from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BookViewSet, BorrowViewSet, RegisterView, LoginView, home

router = DefaultRouter()
router.register('books', BookViewSet)
router.register('borrows', BorrowViewSet)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('', include(router.urls)),
    path('home/', home, name='home'),
]