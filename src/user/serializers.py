import logging
from django.contrib.contenttypes.models import ContentType

from rest_framework.serializers import (
    CharField,
    IntegerField,
    ModelSerializer,
    PrimaryKeyRelatedField,
    SerializerMethodField,
)
import dj_rest_auth.registration.serializers as rest_auth_serializers

from bullet_point.models import BulletPoint
from bullet_point.models import Vote as BulletVote
from discussion.lib import check_is_discussion_item
from discussion.models import Comment, Reply, Thread, Vote as DiscussionVote
from hub.models import Hub
from hub.serializers import HubSerializer, SimpleHubSerializer
from hypothesis.models import Hypothesis
from paper.models import Vote as PaperVote, Paper
from purchase.models import Purchase
from reputation.models import Contribution
from researchhub_access_group.constants import EDITOR
from researchhub_access_group.serializers import DynamicPermissionSerializer
from researchhub_document.models import ResearchhubPost
from researchhub.serializers import DynamicModelFieldSerializer
from summary.models import Summary, Vote as SummaryVote
from user.related_models.gatekeeper_model import Gatekeeper
from user.models import (
    Action,
    Author,
    Major,
    Organization,
    University,
    User,
    Verification,
)

from utils import sentry


class VerificationSerializer(ModelSerializer):
    class Meta:
        model = Verification
        fields = '__all__'


class UniversitySerializer(ModelSerializer):
    class Meta:
        model = University
        fields = '__all__'


class MajorSerializer(ModelSerializer):
    class Meta:
        model = Major
        fields = '__all__'


class GatekeeperSerializer(ModelSerializer):
    class Meta:
        model = Gatekeeper
        fields = '__all__'
        read_only_fields = [field.name for field in Gatekeeper._meta.fields]


class AuthorSerializer(ModelSerializer):
    added_as_editor_date = SerializerMethodField()
    is_hub_editor_of = SerializerMethodField()
    num_posts = SerializerMethodField()
    orcid_id = SerializerMethodField()
    reputation = SerializerMethodField()
    sift_link = SerializerMethodField()
    total_score = SerializerMethodField()
    university = UniversitySerializer(required=False)
    wallet = SerializerMethodField()

    class Meta:
        model = Author
        fields = [field.name for field in Author._meta.fields] + [
            'added_as_editor_date',
            'claimed_by_user_author_id',
            'is_claimed',
            'is_hub_editor_of',
            'num_posts',
            'orcid_id',
            'reputation',
            'sift_link',
            'total_score',
            'university',
            'wallet',
        ]
        read_only_fields = [
            'added_as_editor_date',
            'claimed_by_user_author_id',
            'is_claimed',
            'is_hub_editor_of',
            'num_posts',
            'merged_with',
        ]

    def get_reputation(self, obj):
        if obj.user is None:
            return 0
        return obj.user.reputation

    def get_orcid_id(self, author):
        return author.orcid_id

    def get_total_score(self, author):
        if author.author_score > 0:
            return author.author_score
        # else:
        #     raw_score = Paper.objects.filter(
        #         raw_authors__contains=[
        #             {
        #                 'first_name': author.first_name,
        #                 'last_name': author.last_name
        #             }
        #         ]
        #     ).aggregate(
        #         Sum('score')
        #     ).get('score__sum', 0) or 0
            
        #     authored_score = author.authored_papers.aggregate(Sum('score')).get('score__sum', 0) or 0
        #     total = raw_score + authored_score

        #     if total > 0:
        #         author.author_score = total
        #         author.save()
        #     return total

    def get_wallet(self, obj):
        from purchase.serializers import WalletSerializer
        if not self.context.get('include_wallet', False):
            return

        try:
            return WalletSerializer(obj.wallet).data
        except Exception as error:
            # sentry.log_error(error)
            pass

    def get_sift_link(self, author):
        user = author.user
        if user:
            user_id = user.id
            sift_link = f'https://console.sift.com/users/{user_id}?abuse_type=content_abuse'
            return sift_link
        return None

    def get_num_posts(self, author):
        user = author.user
        if user:
            return ResearchhubPost.objects.filter(created_by=user).count()
        return 0

    def get_added_as_editor_date(self, author):
        user = author.user
        if user is None:
            return None

        hub_content_type = ContentType.objects.get_for_model(Hub)
        editor_permissions = user.permissions.filter(
            access_type=EDITOR,
            content_type=hub_content_type
        ).order_by('created_date')

        if editor_permissions.exists():
            editor = editor_permissions.first()
            return editor.created_date

        return None

    def get_is_hub_editor_of(self, author):
        user = author.user
        if user is None:
            return []

        hub_content_type = ContentType.objects.get_for_model(Hub)
        target_permissions = user.permissions.filter(
            access_type=EDITOR,
            content_type=hub_content_type
        )
        target_hub_ids = []
        for permission in target_permissions:
            target_hub_ids.append(permission.object_id)
        return SimpleHubSerializer(
            Hub.objects.filter(id__in=target_hub_ids),
            many=True
        ).data


class DynamicAuthorSerializer(DynamicModelFieldSerializer):
    class Meta:
        model = Author
        fields = '__all__'


class AuthorEditableSerializer(ModelSerializer):
    university = PrimaryKeyRelatedField(
        queryset=University.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = Author
        fields = [field.name for field in Author._meta.fields] + ['university']
        read_only_fields = [
            'academic_verification',
            'author_score',
            'created_date',
            'claimed',
            'id',
            'merged_with',
            'orcid',
            'orcid_account',
            'user',
        ]


class EditorContributionSerializer(ModelSerializer):
    author_profile = AuthorSerializer(read_only=True)
    comment_count = IntegerField(read_only=True)
    latest_comment_date = SerializerMethodField(read_only=True)
    latest_submission_date = SerializerMethodField(read_only=True)
    submission_count = IntegerField(read_only=True)
    support_count = IntegerField(read_only=True)
    total_contribution_count = IntegerField(read_only=True)

    class Meta:
        model = User
        fields = [
            'author_profile',
            'comment_count',
            'latest_comment_date',
            'latest_submission_date',
            'id',
            'submission_count',
            'support_count',
            'total_contribution_count',
        ]
        read_only_fields = [
            'author_profile',
            'comment_count',
            'id',
            'submission_count',
            'support_count',
            'total_contribution_count',
        ]

    def get_latest_comment_date(self, user):
        contribution_qs = user.contributions.filter(
            contribution_type=Contribution.COMMENTER,
        )
        target_hub_id = self.context.get('target_hub_id')
        if (target_hub_id is not None):
            contribution_qs = contribution_qs.filter(
                unified_document__hubs__in=[target_hub_id]
            )
        try:
            return contribution_qs.latest('created_date').created_date
        except Exception:
            return None

    def get_latest_submission_date(self, user):
        contribution_qs = user.contributions.filter(
            contribution_type=Contribution.SUBMITTER,
        )
        target_hub_id = self.context.get('target_hub_id')
        if (target_hub_id is not None):
            contribution_qs = contribution_qs.filter(
                unified_document__hubs__in=[target_hub_id]
            )
        try:
            return contribution_qs.latest('created_date').created_date
        except Exception:
            return None

class UserSerializer(ModelSerializer):
    author_profile = AuthorSerializer(read_only=True)
    balance = SerializerMethodField(read_only=True)
    subscribed = SerializerMethodField(
        read_only=True
    )
    hub_rep = SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'author_profile',
            'balance',
            'bookmarks',
            'created_date',
            'has_seen_first_coin_modal',
            'has_seen_orcid_connect_modal',
            'is_suspended',
            'moderator',
            'reputation',
            'subscribed',
            'updated_date',
            'upload_tutorial_complete',
            'hub_rep',
            'probable_spammer',
        ]
        read_only_fields = [
            'id',
            'author_profile',
            'bookmarks',
            'created_date',
            'has_seen_first_coin_modal',
            'has_seen_orcid_connect_modal',
            'is_suspended',
            'moderator',
            'reputation',
            'subscribed',
            'updated_date',
            'upload_tutorial_complete',
            'hub_rep',
        ]

    def get_balance(self, obj):
        if not self.read_only and self.context.get('user') and self.context['user'].id == obj.id:
            return obj.get_balance()

    def get_subscribed(self, obj):
        if self.context.get('get_subscribed'):
            subscribed_query = obj.subscribed_hubs.all()
            return HubSerializer(subscribed_query, many=True).data

    def get_hub_rep(self, obj):
        try:
            return obj.hub_rep
        except Exception:
            return None


class MinimalUserSerializer(ModelSerializer):
    author_profile = SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'author_profile',
        ]

    def get_author_profile(self, obj):
        serializer = AuthorSerializer(
            obj.author_profile,
            read_only=True,
            context=self.context
        )
        return serializer.data


class DynamicMinimalUserSerializer(DynamicModelFieldSerializer):
    author_profile = SerializerMethodField()

    class Meta:
        model = User
        fields = "__all__"

    def get_author_profile(self, obj):
        _context_fields = self.context.get('usr_dmus_get_author_profile', {})
        serializer = DynamicAuthorSerializer(
            obj.author_profile,
            context=self.context,
            **_context_fields
        )
        return serializer.data


class UserEditableSerializer(ModelSerializer):
    author_profile = AuthorSerializer()
    balance = SerializerMethodField()
    organization_slug = SerializerMethodField()
    subscribed = SerializerMethodField()

    class Meta:
        model = User
        exclude = [
            'email',
            'password',
            'groups',
            'is_superuser',
            'is_staff',
            'user_permissions',
        ]
        read_only_fields = [
            'moderator',
        ]

    def get_balance(self, user):
        context = self.context
        request_user = context.get('user', None)

        if request_user and request_user == user:
            return user.get_balance()
        return None

    def get_organization_slug(self, user):
        try:
            return user.organization.slug
        except Exception as e:
            sentry.log_error(e)
            return None

    def get_subscribed(self, user):
        if self.context.get('get_subscribed'):
            subscribed_query = user.subscribed_hubs.filter(is_removed=False)
            return HubSerializer(subscribed_query, many=True).data


class RegisterSerializer(rest_auth_serializers.RegisterSerializer):
    username = CharField(
        max_length=rest_auth_serializers.get_username_max_length(),
        min_length=rest_auth_serializers.allauth_settings.USERNAME_MIN_LENGTH,
        required=False,
        allow_blank=True
    )

    def validate_username(self, username):
        if username:
            username = rest_auth_serializers.get_adapter().clean_username(
                username
            )
        return username

    def save(self, request):
        return super().save(request)


class DynamicUserSerializer(DynamicModelFieldSerializer):
    author_profile = SerializerMethodField()

    class Meta:
        model = User
        exclude = ('password',)

    def get_author_profile(self, user):
        context = self.context
        _context_fields = context.get('usr_dus_get_author_profile', {})
        try:
            serializer = DynamicAuthorSerializer(
                user.author_profile,
                context=context,
                **_context_fields
            )
            return serializer.data
        except Exception as e:
            sentry.log_error(e)
            return {}


class UserActions:
    def __init__(self, data=None, user=None, **kwargs):
        assert (data is not None) or (user is not None), f'Arguments data'
        f' and user_id can not both be None'

        if not hasattr(UserActions, 'flag_serializer'):
            from discussion.reaction_serializers import FlagSerializer
            UserActions.flag_serializer = FlagSerializer

            from paper.serializers import FlagSerializer as PaperFlagSerializer
            UserActions.paper_flag_serializer = PaperFlagSerializer

        self.user = None
        if user and user.is_authenticated:
            self.user = user

        self.all = data
        if data is None:
            self.all = self.get_actions()

        self.serialized = []
        self._group_and_serialize_actions()

    def get_actions(self):
        if self.user:
            return self.user.actions.all()
        else:
            return Action.objects.all()

    def _group_and_serialize_actions(self):
        # TODO: Refactor to clean this up
        from researchhub_document.serializers import (
          ResearchhubUnifiedDocumentSerializer
        )

        for action in self.all:
            item = action.item
            if not item:
                continue

            creator = self._get_serialized_creator(item)

            data = {
                'created_by': creator,
                'content_type': str(action.content_type),
                'created_date': str(action.created_date),
            }

            if (
                isinstance(item, Comment)
                or isinstance(item, Thread)
                or isinstance(item, Reply)
                or isinstance(item, Summary)
                or isinstance(item, Paper)
            ):
                pass
            elif isinstance(item, BulletPoint):
                data['content_type'] = 'bullet_point'
            elif isinstance(item, DiscussionVote):
                item = item.item
                if isinstance(item, Comment):
                    data['content_type'] += '_comment'
                elif isinstance(item, Reply):
                    data['content_type'] += '_reply'
                elif isinstance(item, Thread):
                    data['content_type'] += '_thread'
            elif isinstance(item, PaperVote):
                data['content_type'] += '_paper'
            elif isinstance(item, Purchase):
                recipient = action.user
                data['amount'] = item.amount
                data['recipient'] = {
                    'name': recipient.full_name(),
                    'author_id': recipient.author_profile.id
                }
                data['sender'] = item.user.full_name()
                data['support_type'] = item.content_type.model
            elif isinstance(item, ResearchhubPost):
                data['post_title'] = item.title
            elif isinstance(item, BulletVote):
                item = item.bulletpoint
            elif isinstance(item, SummaryVote):
                item = item.summary
            else:
                raise TypeError(
                    f'Instance of type {type(item)} is not supported'
                )

            is_removed = False
            paper = None
            post = None
            discussion = None
            if isinstance(item, Paper):
                paper = item
            else:
                try:
                    if isinstance(item, Purchase):
                        purchase_item = item.item
                        if isinstance(purchase_item, Paper):
                            paper = purchase_item
                        elif isinstance(purchase_item, ResearchhubPost):
                            post = purchase_item
                        elif (
                            isinstance(purchase_item, Thread)
                            or isinstance(purchase_item, Comment)
                            or isinstance(purchase_item, Reply)
                        ):
                            discussion = purchase_item
                        else:
                            paper = purchase_item.paper
                    else:
                        paper = item.paper
                except Exception as e:
                    logging.warning(str(e))

            if paper:
                data['paper_id'] = paper.id
                data['paper_title'] = paper.title
                data['paper_official_title'] = paper.paper_title
                data['slug'] = paper.slug

                if paper.is_removed:
                    is_removed = True

            if post:
                data['post_id'] = post.id
                data['post_title'] = post.title
                data['slug'] = post.slug

            if discussion:
                data['plain_text'] = discussion.plain_text
                paper = discussion.paper
                post = discussion.post
                if paper:
                    data['parent_content_type'] = 'paper'
                    data['paper_id'] = paper.id
                    data['paper_title'] = paper.title
                    data['paper_official_title'] = paper.paper_title
                    data['slug'] = paper.slug
                elif post:
                    data['parent_content_type'] = 'post'
                    data['post_id'] = post.id
                    data['post_title'] = post.title
                    data['slug'] = post.slug

            if isinstance(item, Thread):
                thread = item
                data['thread_id'] = thread.id
                data['thread_title'] = thread.title
                data['thread_plain_text'] = thread.plain_text
                data['tip'] = item.plain_text
                thread_paper = thread.paper
                thread_post = thread.post
                if thread_paper:
                    data['parent_content_type'] = 'paper'
                    data['paper_title'] = thread_paper.title
                    data['paper_id'] = thread_paper.id
                elif thread_post:
                    data['parent_content_type'] = 'post'
                    data['paper_title'] = thread_post.title  # paper_title instead of post_title for symmetry on the FE
                    data['paper_id'] = thread_post.id  # paper_id instead of post_id to temporarily reduce refactoring on FE

            elif isinstance(item, Paper):
                data['tip'] = item.tagline
            elif check_is_discussion_item(item):
                try:
                    thread = item.thread
                    data['thread_id'] = thread.id
                    data['thread_title'] = thread.title
                    data['thread_plain_text'] = thread.plain_text
                except Exception as e:
                    print(e)
                    pass
                data['tip'] = item.plain_text
            elif isinstance(item, BulletPoint):
                data['tip'] = item.plain_text

            if not isinstance(item, Summary) and not isinstance(item, Purchase):
                data['user_flag'] = None
                if self.user:
                    user_flag = item.flags.filter(created_by=self.user).first()
                    if user_flag:
                        if isinstance(item, Paper):
                            data['user_flag'] = UserActions.paper_flag_serializer(user_flag).data  # noqa: E501
                        else:
                            data['user_flag'] = UserActions.flag_serializer(user_flag).data  # noqa: E501

            if isinstance(item, BulletPoint) or check_is_discussion_item(item):
                data['is_removed'] = item.is_removed

            if isinstance(item, Comment):
                data['comment_id'] = item.id
            elif isinstance(item, Reply):
                comment = item.get_comment_of_reply()
                if comment is not None:
                    data['comment_id'] = comment.id
                data['reply_id'] = item.id

            if hasattr(item, 'unified_document'):
                unified_document = item.unified_document
                data['unified_document'] = ResearchhubUnifiedDocumentSerializer(
                    unified_document
                ).data

            if not is_removed:
                self.serialized.append(data)

    def _get_serialized_creator(self, item):
        if isinstance(item, Summary):
            creator = item.proposed_by
        elif isinstance(item, Paper):
            creator = item.uploaded_by
        elif isinstance(item, User):
            creator = item
        elif isinstance(item, Purchase):
            creator = item.user
        else:
            creator = item.created_by
        if creator is not None:
            return UserSerializer(creator).data
        return None


class DynamicActionSerializer(DynamicModelFieldSerializer):
    item = SerializerMethodField()
    content_type = SerializerMethodField()
    created_by = SerializerMethodField()

    class Meta:
        model = Action
        fields = '__all__'

    def get_item(self, action):
        context = self.context
        _context_fields = context.get('usr_das_get_item', {})
        item = action.item
        ignored_items = [
            BulletPoint,
            BulletVote,
            Summary,
            SummaryVote
        ]
        if type(item) in ignored_items:
            return None

        if isinstance(item, Paper):
            from paper.serializers import DynamicPaperSerializer
            serializer = DynamicPaperSerializer
        elif isinstance(item, ResearchhubPost):
            from researchhub_document.serializers import DynamicPostSerializer
            serializer = DynamicPostSerializer
        elif isinstance(item, Hypothesis):
            from hypothesis.serializers import DynamicHypothesisSerializer
            serializer = DynamicHypothesisSerializer
        elif isinstance(item, Purchase):
            from purchase.serializers import DynamicPurchaseSerializer
            serializer = DynamicPurchaseSerializer
        elif isinstance(item, Thread):
            from discussion.serializers import DynamicThreadSerializer
            serializer = DynamicThreadSerializer
        elif isinstance(item, Comment):
            from discussion.serializers import DynamicCommentSerializer
            serializer = DynamicCommentSerializer
        elif isinstance(item, Reply):
            from discussion.serializers import DynamicReplySerializer
            serializer = DynamicReplySerializer
        else:
            return None

        data = serializer(
            item,
            context=context,
            **_context_fields
        ).data
        return data

    def get_created_by(self, action):
        context = self.context
        _context_fields = context.get('usr_das_get_created_by', {})
        serializer = DynamicUserSerializer(
            action.user,
            context=context,
            **_context_fields
        )
        return serializer.data

    def get_content_type(self, action):
        return action.content_type.model


class OrganizationSerializer(ModelSerializer):
    member_count = SerializerMethodField()
    user_permission = SerializerMethodField()

    class Meta:
        model = Organization
        fields = '__all__'
        read_only_fields = ['id', 'slug']

    def get_member_count(self, organization):
        permissions = organization.permissions
        users = permissions.filter(user__isnull=False)
        return users.count()

    def get_user_permission(self, organization):
        context = self.context

        if 'request' in context:
            request = context.get('request')
            user = request.user
        else:
            return None

        if not user.is_anonymous:
            permission = organization.permissions.filter(user=user)
            if permission.exists():
                permission = permission.first()
            else:
                return None
            access_type = permission.access_type
            return {'access_type': access_type}
        return None


class DynamicOrganizationSerializer(DynamicModelFieldSerializer):
    member_count = SerializerMethodField()
    user = SerializerMethodField()
    user_permission = SerializerMethodField()

    class Meta:
        model = Organization
        fields = '__all__'

    def get_member_count(self, organization):
        permissions = organization.permissions
        users = permissions.filter(user__isnull=False)
        return users.count()

    def get_user(self, organization):
        context = self.context
        _context_fields = context.get('usr_dos_get_user', {})

        serializer = DynamicUserSerializer(
            organization.user,
            context=context,
            **_context_fields
        )
        return serializer.data

    def get_user_permission(self, organization):
        context = self.context
        _context_fields = context.get('usr_dos_get_user_permissions', {})
        user = context.get('user')

        permission = organization.permissions.filter(user=user)
        if permission.exists():
            permission = permission.first()
        else:
            return None

        serializer = DynamicPermissionSerializer(
            permission,
            context=context,
            **_context_fields
        )
        return serializer.data
