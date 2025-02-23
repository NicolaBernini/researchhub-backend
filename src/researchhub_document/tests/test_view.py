from django.contrib.contenttypes.models import ContentType
from hub.models import Hub
from researchhub_access_group.constants import EDITOR
from researchhub_access_group.models import Permission
from user.tests.helpers import create_random_default_user
from paper.tests.helpers import create_paper

from rest_framework.test import APITestCase
from hub.tests.helpers import create_hub
from researchhub_document.models import (
    ResearchhubUnifiedDocument,
)


class ViewTests(APITestCase):
    def test_author_can_delete_doc(self):
        author = create_random_default_user('author')
        hub = create_hub()

        self.client.force_authenticate(author)

        doc_response = self.client.post("/api/researchhub_posts/",{
          "document_type": "DISCUSSION",
          "created_by": author.id,
          "full_src": "body",
          "is_public": True,
          "renderable_text": "body",
          "title": "title",
          "hubs": [hub.id],
        })

        response = self.client.delete(f"/api/researchhub_unified_documents/{doc_response.data['unified_document_id']}/censor/")
        doc = ResearchhubUnifiedDocument.objects.get(id=doc_response.data['unified_document_id'])
        self.assertEqual(doc.is_removed, True)

    def test_author_can_restore_doc(self):
        author = create_random_default_user('author')
        hub = create_hub()

        self.client.force_authenticate(author)

        doc_response = self.client.post("/api/researchhub_posts/",{
          "document_type": "DISCUSSION",
          "created_by": author.id,
          "full_src": "body",
          "is_public": True,
          "renderable_text": "body",
          "title": "title",
          "hubs": [hub.id],
        })

        delete_response = self.client.delete(f"/api/researchhub_unified_documents/{doc_response.data['unified_document_id']}/censor/")
        restore_response = self.client.patch(f"/api/researchhub_unified_documents/{doc_response.data['unified_document_id']}/restore/")
        self.assertEqual(restore_response.data['is_removed'], False)

    def test_moderator_can_restore_doc(self):
        author = create_random_default_user('author')
        mod = create_random_default_user('mod', moderator=True)
        hub = create_hub()

        self.client.force_authenticate(author)

        doc_response = self.client.post("/api/researchhub_posts/",{
          "document_type": "DISCUSSION",
          "created_by": author.id,
          "full_src": "body",
          "is_public": True,
          "renderable_text": "body",
          "title": "title",
          "hubs": [hub.id],
        })

        delete_response = self.client.delete(f"/api/researchhub_unified_documents/{doc_response.data['unified_document_id']}/censor/")

        self.client.force_authenticate(mod)
        restore_response = self.client.patch(f"/api/researchhub_unified_documents/{doc_response.data['unified_document_id']}/restore/")
        self.assertEqual(restore_response.data['is_removed'], False)

    def test_non_author_cannot_delete_doc(self):
        author = create_random_default_user('author')
        non_author = create_random_default_user('non_author')
        hub = create_hub()

        self.client.force_authenticate(author)

        doc_response = self.client.post(f"/api/researchhub_posts/", {
          "document_type": "DISCUSSION",
          "created_by": author.id,
          "full_src": "body",
          "is_public": True,
          "renderable_text": "body",
          "title": "title",
          "hubs": [hub.id],
        })

        self.client.force_authenticate(non_author)

        response = self.client.delete(f"/api/researchhub_unified_documents/{doc_response.data['unified_document_id']}/censor/")
        doc = ResearchhubUnifiedDocument.objects.get(id=doc_response.data['unified_document_id'])
        self.assertEqual(doc.is_removed, False)

    def test_moderator_can_delete_doc(self):
        author = create_random_default_user('author')
        moderator = create_random_default_user('moderator', moderator=True)
        hub = create_hub()

        self.client.force_authenticate(author)

        doc_response = self.client.post("/api/researchhub_posts/", {
          "document_type": "DISCUSSION",
          "created_by": author.id,
          "full_src": "body",
          "is_public": True,
          "renderable_text": "body",
          "title": "title",
          "hubs": [hub.id],
        })

        self.client.force_authenticate(moderator)

        response = self.client.delete(f"/api/researchhub_unified_documents/{doc_response.data['unified_document_id']}/censor/")
        doc = ResearchhubUnifiedDocument.objects.get(id=doc_response.data['unified_document_id'])
        self.assertEqual(doc.is_removed, True)

    def author_can_create_post(self):
        author = create_random_default_user('author')
        hub = create_hub()

        self.client.force_authenticate(author)

        doc_response = self.client.post("/api/researchhub_posts/", {
          "document_type": "DISCUSSION",
          "created_by": author.id,
          "full_src": "body",
          "is_public": True,
          "renderable_text": "body",
          "title": "title",
          "hubs": [hub.id],
        })

        self.assertEqual(doc_response.status_code, 200)

    def author_can_update_post(self):
        author = create_random_default_user('author')
        hub = create_hub()

        self.client.force_authenticate(author)

        doc_response = self.client.post("/api/researchhub_posts/", {
          "document_type": "DISCUSSION",
          "created_by": author.id,
          "full_src": "body",
          "is_public": True,
          "renderable_text": "body",
          "title": "title",
          "hubs": [hub.id],
        })

        updated_response = self.client.post("/api/researchhub_posts/", {
          "post_id": doc_response.data["id"],
          "title": "updated title",
          "document_type": "DISCUSSION",
          "created_by": author.id,
          "full_src": "body",
          "is_public": True,
          "renderable_text": "body",
          "hubs": [hub.id],
        })

        self.assertEqual(updated_response.data['title'], 'updated title')

    def author_can_create_hypothesis(self):
        author = create_random_default_user('author')
        hub = create_hub()

        self.client.force_authenticate(author)

        doc_response = self.client.post("/api/hypothesis/", {
          "document_type": "HYPOTHESIS",
          "created_by": author.id,
          "full_src": "body",
          "is_public": True,
          "renderable_text": "body",
          "title": "hypothesis",
          "hubs": [hub.id],
        })

        self.assertEqual(doc_response.status_code, 200)

    def author_can_update_hypothesis(self):
        author = create_random_default_user('author')
        hub = create_hub()

        self.client.force_authenticate(author)

        doc_response = self.client.post("/api/hypothesis/", {
          "document_type": "HYPOTHESIS",
          "created_by": author.id,
          "full_src": "body",
          "is_public": True,
          "renderable_text": "body",
          "title": "title",
          "hubs": [hub.id],
        })

        updated_response = self.client.post(f"/api/hypothesis/{doc_response.data['id']}/upsert/", {
          "hypothesis_id": doc_response.data["id"],
          "title": "updated title",
          "document_type": "HYPOTHESIS",
          "full_src": "updated body",
          "renderable_text": "body",
        })

        self.assertEqual(updated_response.data['full_src'], 'updated body')

    def test_non_author_cannot_edit_hypothesis(self):
        author = create_random_default_user('author')
        non_author = create_random_default_user('non_author')
        hub = create_hub()

        self.client.force_authenticate(author)

        doc_response = self.client.post("/api/hypothesis/", {
          "document_type": "HYPOTHESIS",
          "created_by": author.id,
          "full_src": "body",
          "is_public": True,
          "renderable_text": "body",
          "title": "title",
          "hubs": [hub.id],
        })

        self.client.force_authenticate(non_author)

        updated_response = self.client.post(f"/api/hypothesis/{doc_response.data['id']}/upsert/", {
          "hypothesis_id": doc_response.data["id"],
          "title": "updated title",
          "document_type": "HYPOTHESIS",
          "full_src": "updated body",
          "renderable_text": "body",
        })
        self.assertEqual(updated_response.status_code, 403)

    def test_hub_editors_can_censor_papers(self):
        hub = create_hub()
        user_editor = create_random_default_user('user_editor')
        Permission.objects.create(
            access_type=EDITOR,
            content_type=ContentType.objects.get_for_model(Hub),
            object_id=hub.id,
            user=user_editor,
        )
        user_uploader = create_random_default_user('user_uploader')
        test_paper = create_paper(uploaded_by=user_uploader)
        test_paper.hubs.add(hub)
        test_paper.save()

        self.client.force_authenticate(user_editor)
        response = self.client.put(
          f"/api/paper/{test_paper.id}/censor_paper/",
          {"id": test_paper.id}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['is_removed'], True)

    def test_hub_editors_can_restore_papers(self):
        hub = create_hub()
        user_editor = create_random_default_user('user_editor')
        Permission.objects.create(
            access_type=EDITOR,
            content_type=ContentType.objects.get_for_model(Hub),
            object_id=hub.id,
            user=user_editor,
        )
        user_uploader = create_random_default_user('user_uploader')
        test_paper = create_paper(uploaded_by=user_uploader)
        test_paper.hubs.add(hub)
        test_paper.is_removed = True
        test_paper.save()

        self.client.force_authenticate(user_editor)
        response = self.client.put(
          f"/api/paper/{test_paper.id}/restore_paper/",
          {"id": test_paper.id}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['is_removed'], False)
