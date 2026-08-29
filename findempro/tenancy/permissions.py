from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import OrganizationMembership
from .services import get_request_organization, membership_for


class OrganizationWritePermission(BasePermission):
    """Every member may read; OWNER/ADMIN/MEMBER may mutate."""

    def has_permission(self, request, view):
        organization = get_request_organization(request)
        membership = membership_for(request.user, organization)
        if not membership:
            return False
        if request.method in SAFE_METHODS:
            return True
        return membership.role in {
            OrganizationMembership.Role.OWNER,
            OrganizationMembership.Role.ADMIN,
            OrganizationMembership.Role.MEMBER,
        }
