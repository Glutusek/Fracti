from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReceiptViewSet, ProductViewSet, SettlementViewSet

router = DefaultRouter()
router.register(r'receipts', ReceiptViewSet, basename='receipt')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'settlements', SettlementViewSet, basename='settlement')

urlpatterns = [
    path('', include(router.urls)),
]