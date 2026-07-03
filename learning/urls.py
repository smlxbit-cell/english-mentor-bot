from django.urls import path

from . import views


app_name = 'learning'

urlpatterns = [
    path('', views.word_list, name='word_list'),
    path('add/', views.word_create, name='word_create'),
    path('training/', views.word_training, name='word_training'),
]
