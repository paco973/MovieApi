from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator

class Movie(models.Model):
    title = models.CharField(max_length = 32)
    description = models.TextField(max_length=433)

    def no_of_comments(self):
        comments = Comment.objects.filter(movie=self)
        return len(comments)


class Comment(models.Model):
    movie = models.ForeignKey(Movie,on_delete = models.CASCADE )
    user = models.ForeignKey(User, on_delete= models.CASCADE )
    text = models.models.TextField()

    class Meta:
        unique_together = (('user', 'movie'),)
        index_together = (('user', 'movie'),)