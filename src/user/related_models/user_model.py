import uuid

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import AbstractUser, UserManager
from django.db.models import DecimalField, Sum
from django.db.models.functions import Cast
from django.db import models
from django.utils import timezone

from hub.models import Hub
from mailing_list.models import EmailRecipient
from researchhub_access_group.constants import EDITOR
from reputation.models import PaidStatusModelMixin, Withdrawal
from user.tasks import handle_spam_user_task
from user.tasks import update_elastic_registry
from utils.message import send_email_message
from utils.siftscience import decisions_api
from utils.throttles import UserSustainedRateThrottle


class UserManager(UserManager):
    def editors(self):
        editors = self.filter(
            permissions__isnull=False,
            permissions__access_type=EDITOR,
            permissions__content_type=ContentType.objects.get_for_model(Hub)
        ).distinct()
        return editors


"""
User objects have the following fields by default:
    https://docs.djangoproject.com/en/2.2/ref/contrib/auth/#django.contrib.auth.models.User
"""


class User(AbstractUser):
    country_code = models.CharField(max_length=4, null=True, blank=True)
    reputation = models.IntegerField(default=100)
    upload_tutorial_complete = models.BooleanField(default=False)
    has_seen_first_coin_modal = models.BooleanField(default=False)
    has_seen_orcid_connect_modal = models.BooleanField(default=False)
    has_seen_stripe_modal = models.BooleanField(default=False)
    agreed_to_terms = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    bookmarks = models.ManyToManyField(
        'paper.Paper',
        related_name='users_who_bookmarked'
    )
    moderator = models.BooleanField(default=False)
    is_suspended = models.BooleanField(default=False)
    probable_spammer = models.BooleanField(default=False)
    suspended_updated_date = models.DateTimeField(null=True)
    spam_updated_date = models.DateTimeField(null=True)
    referral_code = models.CharField(
        max_length=36,
        default=uuid.uuid4,
        unique=True
    )
    invited_by = models.ForeignKey(
        'self',
        related_name='invitee',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    sift_risk_score = models.FloatField(null=True, blank=True)

    objects = UserManager()

    def full_name(self):
        return self.first_name + ' ' + self.last_name

    def __str__(self):
        return '{} / {}'.format(
            self.email,
            self.first_name + ' ' + self.last_name
        )

    class Meta:
        ordering = ['-created_date']

    def save(self, *args, **kwargs):
        # A unique constraint is enforced on the username on the database
        # level. This line is used to ensure usernames are not empty without
        # requiring the client to enter a value in this field. It also forces
        # emails to be unique.
        #
        # If we want to allow client specified usernames, simply remove the
        # set username line.

        if (self.email is not None) and (self.email != ''):
            self.username = self.email

        user_to_save = super(User, self).save(*args, **kwargs)

        # Keep Email Recipient up to date with email
        if (self.email is not None) and (self.email != ''):
            if hasattr(self, 'emailrecipient') and (
                self.emailrecipient is not None
            ):
                if self.emailrecipient.email != self.email:
                    er = self.emailrecipient
                    er.email = self.email
                    er.save()
            else:
                EmailRecipient.objects.create(user=self, email=self.email)

        # Update the Elastic Search index
        try:
            update_elastic_registry.apply_async([self.id])
        except Exception as e:
            pass

        return user_to_save

    def set_has_seen_first_coin_modal(self, has_seen):
        self.has_seen_first_coin_modal = has_seen
        self.save()

    def set_has_seen_orcid_connect_modal(self, has_seen):
        self.has_seen_orcid_connect_modal = has_seen
        self.save()

    def set_has_seen_stripe_modal(self, has_seen):
        self.has_seen_stripe_modal = has_seen
        self.save()

    def set_probable_spammer(self, probable_spammer=True):
        if self.probable_spammer != probable_spammer:
            capcha_throttle = UserSustainedRateThrottle()
            capcha_throttle.lock(self, "probably_spam")

            self.probable_spammer = probable_spammer
            self.spam_updated_date = timezone.now()
            self.save(update_fields=['probable_spammer', 'spam_updated_date'])

        if probable_spammer:
            handle_spam_user_task.apply_async((self.id,), priority=3)

    def set_suspended(self, is_suspended=True, is_manual=True):
        if self.is_suspended != is_suspended:
            self.is_suspended = is_suspended
            self.suspended_updated_date = timezone.now()
            self.save(update_fields=['is_suspended', 'suspended_updated_date'])

        if is_suspended:
            source = 'MANUAL_REVIEW' if is_manual else 'AUTOMATED_RULE'
            decisions_api.apply_bad_user_decision(self, source)

    def get_balance(self):
        user_balance = self.balances.all()
        if not user_balance:
            return 0

        failed_withdrawals = self.withdrawals.filter(
            paid_status=PaidStatusModelMixin.FAILED
        ).values_list('id')
        balance = self.balances.exclude(
            content_type=ContentType.objects.get_for_model(Withdrawal),
            object_id__in=failed_withdrawals
        ).aggregate(
            total_balance=Sum(
                Cast(
                    'amount',
                    DecimalField(max_digits=255, decimal_places=128)
                )
            )
        )
        total_balance = balance.get('total_balance', 0)

        return total_balance

    def notify_inactivity(self):
        recipient = [self.email]
        subject = '[Editor] Weekly Inactivity'
        email_context = {
            'name': f'{self.first_name} {self.last_name}'
        }
        send_email_message(
            recipient,
            'editor_inactivity.txt',
            subject,
            email_context,
            'editor_inactivity.html',
        )

    def is_hub_editor_of(self, hubs):
        hub_content_type = ContentType.objects.get_for_model(Hub)
        return self.permissions.filter(
            access_type=EDITOR,
            content_type=hub_content_type,
            object_id__in=hubs.values_list('id', flat=True),
        ).exists()
