from django.db import models

class SalesData(models.Model): # Or whatever inspectdb names it
    docdt = models.DateTimeField(db_column='DOCDT', blank=True, null=True)
    itemname = models.CharField(db_column='ITEMNAME', max_length=255, blank=True, null=True)
    itemsize = models.CharField(db_column='ITEMSIZE', max_length=50, blank=True, null=True)
    quantity = models.IntegerField(db_column='QUANTITY', blank=True, null=True)
    totalitemvalue = models.FloatField(db_column='TOTALITEMVALUE', blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'SALEINVOICE' 