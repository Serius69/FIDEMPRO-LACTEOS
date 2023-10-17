from django.db import models

class Question(models.Model):
    text = models.TextField()
    is_active = models.BooleanField(default=True)  # Add the is_active field
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.text

class QuestionCategory(models.Model):
    name = models.CharField(max_length=100)
    questions = models.ManyToManyField(Question, related_name='categories')
    # You can add more fields or methods as needed

    def __str__(self):
        return self.name
