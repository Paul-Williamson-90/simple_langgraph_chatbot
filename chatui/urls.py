from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_page, name='chat_page'),
    path('api/threads/', views.get_threads, name='get_threads'),
    path('api/thread/<str:thread_id>/', views.get_thread_messages, name='get_thread_messages'),
    path('api/send/', views.send_message, name='send_message'),
]
