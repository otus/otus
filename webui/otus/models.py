from django.db import models

class Dashboard(models.Model):
    name = models.CharField(max_length = 100)
    graph_name = models.CharField(max_length = 100)
    graph_url = models.URLField()