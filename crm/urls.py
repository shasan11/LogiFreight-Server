from rest_framework_bulk.routes import BulkRouter as DefaultRouter

from crm.views import (
    LeadViewSet,
    LeadActivityViewSet,
    LeadFollowUpViewSet,
    QuotationViewSet,
    QuotationDocumentViewSet,
    QuotationNoteViewSet,
    QuotationPackageViewSet,
    QuotationChargeLineViewSet,
    QuotationCostLineViewSet,
)

router = DefaultRouter()
router.register(r"leads", LeadViewSet, basename="leads")
router.register(r"lead-activities", LeadActivityViewSet, basename="lead-activities")
router.register(r"lead-followups", LeadFollowUpViewSet, basename="lead-followups")
router.register(r"quotations", QuotationViewSet, basename="quotations")
router.register(r"quotation-documents", QuotationDocumentViewSet, basename="quotation-documents")
router.register(r"quotation-notes", QuotationNoteViewSet, basename="quotation-notes")
router.register(r"quotation-packages", QuotationPackageViewSet, basename="quotation-packages")
router.register(r"quotation-charge-lines", QuotationChargeLineViewSet, basename="quotation-charge-lines")
router.register(r"quotation-cost-lines", QuotationCostLineViewSet, basename="quotation-cost-lines")

urlpatterns = router.urls
