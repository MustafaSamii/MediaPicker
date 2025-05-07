from django.urls import path
from .views import chat
from . import views

app_name = 'discover'

urlpatterns = [
    # Root (“/”) → search view
    path('', views.search, name='search'),
    # /search/ → same view (optional)
    path('search/', views.search, name='search'),
    path('chat/', chat, name='chat'),

]
