from django.urls import path
from . import views

urlpatterns=[
    path('', views.start_session, name='start_session'),
    path('home/', views.home, name='home'),
    path('quizz/', views.show_question, name='quizz'),
    path('ajax/random-question/', views.get_random_question, name='ajax_random_question'),
    path('delete_player/', views.delete_player, name='delete_player'),
    path('update_score/', views.update_score, name='update_score'),
    path('end_quiz/', views.end_quiz, name='end_quiz'),
]