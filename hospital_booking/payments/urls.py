from django.urls import path
from . import views

urlpatterns = [
    path('pay/<int:billing_id>/', views.create_payment, name='create_payment'),
    path('vnpay-return/', views.vnpay_return, name='vnpay_return'),
    path('history/', views.payment_history, name='payment_history'),
]
