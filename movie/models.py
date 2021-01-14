from django.db import models

# Create your models here.
from django.db.models import Avg
from django.contrib.auth.models import User

class Movie(models.Model):
    title = models.CharField(max_length=200)

    def average_rating(self):
        return self.review_set.aggregate(Avg('rating'))['rating__avg']

    def __str__(self):
        return self.title

class Review(models.Model):
    RATING_CHOICES = (
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (5, '5'),

    )
    movie = models.ForeignKey('movie', on_delete=models.DO_NOTHING)
    pub_date = models.DateTimeField('date published')
    user_id = models.ForeignKey(User, default=None, null=True, blank=True, on_delete=models.CASCADE)
    user_name = models.CharField(max_length=100, default='user')
    comment = models.CharField(max_length=200)
    rating = models.FloatField(choices=RATING_CHOICES, default=None, null=True, blank=True)
