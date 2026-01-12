from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReceiptViewSet, ProductViewSet, SettlementViewSet, ReceiptAnalyzeView, OCRResultView, AddGuestUserView

router = DefaultRouter()
router.register(r'receipts', ReceiptViewSet, basename='receipt')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'settlements', SettlementViewSet, basename='settlement')


urlpatterns = [
    path('', include(router.urls)),
    path('ocr/analyze/', ReceiptAnalyzeView.as_view(), name='ocr-analyze'),
    path('ocr/result/<str:task_id>/', OCRResultView.as_view(), name='ocr-result'),
    path('settlements/<uuid:pk>/add-guest/', AddGuestUserView.as_view(), name='add-guest-user'),
]