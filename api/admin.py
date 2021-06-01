from django.contrib import admin
from .models import Comment, Movie

admin.site.register(Movie)
admin.site.register(Comment)
