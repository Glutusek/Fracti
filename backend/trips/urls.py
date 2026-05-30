from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TripViewSet, SimpleCalculatorView

router = DefaultRouter()
router.register(r'', TripViewSet, basename='trip')

urlpatterns = [
    path('calculator/simple/', SimpleCalculatorView.as_view(), name='trip-simple-calculator'),
    path('', include(router.urls)),
]
