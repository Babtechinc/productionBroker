from django.db import models

# Create your models here.
class ProductionLineModel(models.Model):
    Code = models.CharField(blank=True,max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
class ProductionLineNodeModel(models.Model):
    Code = models.CharField(blank=True,max_length=255)
    NodeID = models.CharField(blank=True,max_length=255)
    ProductLine = models.CharField(blank=True,max_length=255)
    NodeType = models.CharField(blank=True,max_length=255)
    created_at = models.DateTimeField(auto_now_add=True,)
    updated_at = models.DateTimeField(auto_now=True)

    # class Meta:
    #     abstract = True
