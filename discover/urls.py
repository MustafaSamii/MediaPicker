from django.urls import path
from .views import chat
from . import views

app_name = 'discover'

urlpatterns = [
    # Root (“/”) → search view
    path('', views.search, name='search'),
    # /search/ → same view (optional)
    path('search/', views.search, name='search'),
    path('watched/', views.watched, name='watched'),
    path('toggle-watched/<int:movie_id>/',views.toggle_watched, name='toggle_watched'),
        

]
