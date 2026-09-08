"""Provided synthetic data. Input order is deliberately NOT the answer order."""
from models import Document

DOCUMENTS = [
    Document(
        tenant_id="firm-a", document_id="z-private", version=1,
        title="Termination notice", text="Termination notice",
        categories=frozenset({"contract"}),
        allowed_users=frozenset({"bob"}), public=False,
    ),
    Document(
        tenant_id="firm-b", document_id="y-foreign", version=1,
        title="Termination notice", text="Termination notice",
        categories=frozenset({"contract"}), public=True,
    ),
    Document(
        tenant_id="firm-a", document_id="c", version=1,
        title="Employment memo", text="Termination notice",
        categories=frozenset({"memo"}), public=True,
    ),
    Document(
        tenant_id="firm-a", document_id="b", version=1,
        title="Termination policy", text="Notice required",
        categories=frozenset({"employment", "contract"}),
        allowed_users=frozenset({"alice"}), public=False,
    ),
    Document(
        tenant_id="firm-a", document_id="a", version=1,
        title="Termination letter", text="Notice period",
        categories=frozenset({"contract"}), public=True,
    ),
    Document(
        tenant_id="firm-a", document_id="d", version=1,
        title="Notices", text="Archived",
        categories=frozenset({"memo"}), public=True,
    ),
]
