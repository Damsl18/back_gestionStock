from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='total_amount',
            field=models.DecimalField(
                max_digits=10,
                decimal_places=2,
                default=0,
                help_text='Montant total de la facture'
            ),
        ),
        migrations.AlterField(
            model_name='activitylog',
            name='worker',
            field=models.ForeignKey(
                blank=True,
                null=True,
                help_text="Utilisateur qui a effectué l'action",
                on_delete=django.db.models.deletion.CASCADE,
                related_name='activity_logs',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name='discount',
            name='product',
            field=models.ForeignKey(
                blank=True,
                null=True,
                help_text='Produit affecté (null = tous les produits)',
                on_delete=django.db.models.deletion.CASCADE,
                related_name='discounts',
                to='sales.product',
            ),
        ),
    ]