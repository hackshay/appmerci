from django.db import models
from django import forms
import uuid


class GameSession(models.Model):
    session_key=models.CharField(max_length=255, unique=True, default=uuid.uuid4)
    created_at=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.session_key
    
# Create your models here.
class Question(models.Model):
    text=models.CharField(max_length=150)
    answer=models.CharField(max_length=150)

    def __str__(self):
        return self.text
    
class Choice(models.Model):
    question=models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text=models.CharField(max_length=200)
    is_correct= models.BooleanField(default=False)

    def __str__(self):
        return self.choice_text


    
class Player(models.Model):
    name=models.CharField(max_length=20)
    score=models.IntegerField(default=0)
    game_session=models.ForeignKey(GameSession, related_name='players', on_delete=models.CASCADE, null=True)

    

    def __str__(self):
        return self.name
    
class Animator(models.Model):
    name=models.CharField(max_length=20)
    game_session=models.ForeignKey(GameSession, related_name='animator', on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.name
    
