# Generated manually

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('caisse', '0003_initial'),
        ('credits', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='caissetypemvt',
            name='credit',
            field=models.ForeignKey(blank=True, help_text='Crédit lié (optionnel)', null=True, on_delete=django.db.models.deletion.CASCADE, related_name='caissetype_mouvements', to='credits.credit'),
        ),
    ]
