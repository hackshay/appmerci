from django.db import models
from django import forms
import uuid

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

    

    def __str__(self):
        return self.name
    
class Animator(models.Model):
    name=models.CharField(max_length=20)

    def __str__(self):
        return self.name
    
