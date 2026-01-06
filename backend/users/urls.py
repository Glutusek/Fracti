from django.urls import path
from .views import RegisterView, MeView
from rest_framework_simplejwt.views import (TokenObtainPairView, TokenRefreshView,)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),

    # Przenieśmy tu też logowanie, bo to pasuje do apki "users"!
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', MeView.as_view(), name='me'),
]