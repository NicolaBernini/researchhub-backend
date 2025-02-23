from hypothesis.related_models.hypothesis import Hypothesis
from paper.models import Paper
from researchhub_document.related_models.constants.document_type import (
    DISCUSSION,
    HYPOTHESIS,
)
from researchhub_document.models import (
    ResearchhubPost
)
from researchhub_document.related_models.researchhub_unified_document_model \
    import ResearchhubUnifiedDocument
from utils.permissions import AuthorizationBasedPermission


class HasDocumentCensorPermission(AuthorizationBasedPermission):
    message = 'Need to be author or moderator to delete'

    def is_authorized(self, request, view, obj):
        if request.user.is_authenticated is False:
            return False

        doc = None
        if (isinstance(obj, ResearchhubUnifiedDocument)):
            uni_doc_model = get_uni_doc_related_model(obj)
            doc = uni_doc_model.objects.get(unified_document_id=obj.id) \
                if uni_doc_model is not None else None
        elif (isinstance(obj, Paper)):
            doc = Paper.objects.get(id=obj.id)
        else:
            return False

        if (doc is None):
            return False

        requestor = request.user
        is_requestor_appropriate_editor = requestor.is_hub_editor_of(
            doc.hubs,
        )
        if (
            requestor.moderator or  # moderators serve as site admin
            is_requestor_appropriate_editor or
            doc.created_by_id == requestor.id
        ):
            return True

        return False


class HasDocumentEditingPermission(AuthorizationBasedPermission):
    message = 'Need to be author or moderator to edit'

    def has_permission(self, request, view):
        if view.action == 'create' or view.action == 'update' or view.action == 'upsert':
            if request.data.get('post_id') is not None:
                post = ResearchhubPost.objects.get(id=request.data.get('post_id'))
                if post.created_by_id == request.user.id or request.user.moderator:
                    return True
                else:
                    return False
            elif request.data.get('hypothesis_id') is not None:
                hypothesis = Hypothesis.objects.get(id=request.data.get('hypothesis_id'))
                if hypothesis.created_by_id == request.user.id or request.user.moderator:
                    return True
                else:
                    return False

        return True


def get_uni_doc_related_model(unified_document):
    if (not isinstance(unified_document, ResearchhubUnifiedDocument)):
        return None
    doc_type = unified_document.document_type
    if doc_type == DISCUSSION:
        return ResearchhubPost
    elif doc_type == HYPOTHESIS:
        return Hypothesis
    else:
        return None
