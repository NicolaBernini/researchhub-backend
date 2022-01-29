from django.db import models

from researchhub_document.related_models.constants.rsc_exchange_currency \
    import (RSC_EXCHANGE_CURRENCY)
from utils.models import DefaultModel


class RscExchangeRate(DefaultModel):
    rate = models.FloatField(
        blank=False,
        help_text="""
            RSC to target currency rate.
            For example, rate of 3 to USD represents 3 dollars per RSC.
            This is may not reflect the market fully for internal purposes.
            We may adjust the rate for different purposes.
        """,
        null=False,
    )
    target_currency = models.CharField(
        blank=False,
        choices=RSC_EXCHANGE_CURRENCY,
        db_index=True,
        max_length=255,
        null=False,
    )