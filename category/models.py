
# Create your models here.
from django.db import models
from django.urls import reverse
class Category(models.Model):  # Note the corrected capitalization of `models.Model`
    category_name = models.CharField(max_length=50, unique=True)  # Note the corrected capitalization of `CharField`
    slug = models.SlugField(max_length=100, unique=True)  # Note the corrected capitalization of `CharField`
    description = models.TextField(max_length=255, blank=True)  # Note the corrected capitalization of `TextField`
    cat_image = models.ImageField(upload_to='photos/categories', blank=True)  # Note the corrected attribute name `upload_to` instead of `upload`

    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'

    def get_url(self):
        return reverse('products_by_category',args=[self.slug])
    def __str__(self):
        return self.category_name
