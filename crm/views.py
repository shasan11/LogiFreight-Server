from __future__ import annotations

from typing import Iterable

from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework_bulk import BulkModelViewSet
from core.utils.BaseModelViewSet import BaseModelViewSet

from crm.filters import (
    LeadFilter,
    LeadActivityFilter,
    LeadFollowUpFilter,
    QuotationFilter,
    QuotationPackageFilter,
    QuotationNoteFilter,
    QuotationDocumentFilter,
    QuotationChargeLineFilter,
    QuotationCostLineFilter,
)
from crm.serializers import (
    LeadSerializer,
    LeadActivitySerializer,
    LeadFollowUpSerializer,
    QuotationSerializer,
    QuotationDocumentSerializer,
    QuotationNoteSerializer,
    QuotationPackageSerializer,
    QuotationChargeLineSerializer,
    QuotationCostLineSerializer,
)
from crm.utils import recompute_quotations
from crm.models import (
    Lead,
    LeadActivity,
    LeadFollowUp,
    Quotation,
    QuotationDocument,
    QuotationNote,
    QuotationPackage,
    QuotationChargeLine,
    QuotationCostLine,
)


class BranchScopedMixin:
    def get_queryset(self):
        qs = super().get_queryset()
        if hasattr(qs.model, "branch_id") and hasattr(self.request.user, "branch_id"):
            if getattr(self.request.user, "branch_id", None):
                return qs.filter(branch_id=self.request.user.branch_id)
        return qs


class LeadViewSet(BaseModelViewSet):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = LeadFilter
    search_fields = ["lead_no", "title", "company_name", "contact_name", "phone", "email", "origin_port", "destination_port"]
    ordering_fields = ["created", "updated", "lead_no", "status"]
    ordering = ["-created"]


class LeadActivityViewSet(BaseModelViewSet):
    queryset = LeadActivity.objects.all()
    serializer_class = LeadActivitySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = LeadActivityFilter
    search_fields = ["subject", "details"]
    ordering_fields = ["activity_at", "created"]
    ordering = ["-activity_at"]


class LeadFollowUpViewSet(BaseModelViewSet):
    queryset = LeadFollowUp.objects.all()
    serializer_class = LeadFollowUpSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = LeadFollowUpFilter
    search_fields = ["agenda", "notes", "channel"]
    ordering_fields = ["due_at", "created", "status"]
    ordering = ["due_at"]


class QuotationViewSet(BaseModelViewSet):
    queryset = Quotation.objects.all()
    serializer_class = QuotationSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = QuotationFilter
    search_fields = ["quote_no", "doc_ref_no", "port_of_departure", "port_of_arrival", "carrier"]
    ordering_fields = ["issued_date", "expiry_date", "created", "updated", "quote_no", "status"]
    ordering = ["-created"]


class QuotationDocumentViewSet(BaseModelViewSet):
    queryset = QuotationDocument.objects.all()
    serializer_class = QuotationDocumentSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = QuotationDocumentFilter
    ordering_fields = ["created"]
    ordering = ["-created"]


class QuotationNoteViewSet(BaseModelViewSet):
    queryset = QuotationNote.objects.all()
    serializer_class = QuotationNoteSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = QuotationNoteFilter
    search_fields = ["title", "description"]
    ordering_fields = ["created"]
    ordering = ["-created"]


class QuotationPackageViewSet(BaseModelViewSet):
    queryset = QuotationPackage.objects.all()
    serializer_class = QuotationPackageSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = QuotationPackageFilter
    search_fields = ["good_desc", "hs_code", "country_of_origin", "remarks"]
    ordering_fields = ["created"]
    ordering = ["-created"]


class _QuotationTotalsHookMixin:
    def _extract_quote_ids_from_instances(self, instances) -> set[int]:
        ids: set[int] = set()
        if instances is None:
            return ids
        if isinstance(instances, (list, tuple)):
            for obj in instances:
                if getattr(obj, "quotation_id", None):
                    ids.add(int(obj.quotation_id))
            return ids
        if getattr(instances, "quotation_id", None):
            ids.add(int(instances.quotation_id))
        return ids

    def _recompute_from_instances(self, instances):
        recompute_quotations(self._extract_quote_ids_from_instances(instances))

    def perform_create(self, serializer):
        with transaction.atomic():
            instances = serializer.save()
        self._recompute_from_instances(instances)

    def perform_update(self, serializer):
        with transaction.atomic():
            instances = serializer.save()
        self._recompute_from_instances(instances)

    def perform_destroy(self, instance):
        qid = getattr(instance, "quotation_id", None)
        with transaction.atomic():
            instance.delete()
        recompute_quotations([qid])


class QuotationChargeLineViewSet(BaseModelViewSet, _QuotationTotalsHookMixin):
    queryset = QuotationChargeLine.objects.all()
    serializer_class = QuotationChargeLineSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = QuotationChargeLineFilter
    search_fields = ["charge_name", "remarks", "reference_no"]
    ordering_fields = ["id", "created"]
    ordering = ["-id"]


class QuotationCostLineViewSet(BaseModelViewSet, _QuotationTotalsHookMixin):
    queryset = QuotationCostLine.objects.all()
    serializer_class = QuotationCostLineSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = QuotationCostLineFilter
    search_fields = ["charge_name", "remarks", "reference_no"]
    ordering_fields = ["id", "created"]
    ordering = ["-id"]
