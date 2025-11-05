from django.http import Http404
from vendors.models import Vendor

class SubdomainVendorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0]
        parts = host.split('.')
        request.vendor = None
        request.is_vendor_subdomain = False

        # vendor.domain.tld => treat first part as vendor slug
        if len(parts) >= 3:
            subdomain = parts[0]
            try:
                vendor = Vendor.objects.get(slug=subdomain)
            except Vendor.DoesNotExist:
                raise Http404('Vendor not found')
            request.vendor = vendor
            request.is_vendor_subdomain = True

        return self.get_response(request)
