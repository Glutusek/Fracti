from django.urls import path
from .views import ContactCreateView, ContactListView, ContactDetailView

urlpatterns = [
    path('', ContactCreateView.as_view(), name='contact-create'),
    path('messages/', ContactListView.as_view(), name='contact-list'),
    path('messages/<int:pk>/', ContactDetailView.as_view(), name='contact-detail'),
]
