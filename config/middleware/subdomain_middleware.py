# middleware.py
from django.http import Http404, HttpResponseRedirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from vendors.models import Vendor


class SubdomainVendorMiddleware(MiddlewareMixin):
    """
    Detects vendor subdomains like:
        crescent.lvh.me:8000 → vendor.slug = 'crescent'
    Sets:
        request.vendor
        request.is_vendor_subdomain
    Auto-redirects "/" → vendor store
    """

    def process_request(self, request):
        host = request.get_host().split(":")[0]  # remove port
        parts = host.split(".")

        # lvh.me or localhost
        if len(parts) > 2 and parts[-2:] == ['lvh', 'me']:
            slug = parts[0].lower()

            try:
                vendor = Vendor.objects.get(slug=slug)
                request.vendor = vendor
                request.is_vendor_subdomain = True

                # Auto-route root "/" to vendor store
                if request.path == "/" or request.path == "":
                    return HttpResponseRedirect(
                        reverse('vendors:vendor_store', kwargs={'vendor_slug': vendor.slug})
                    )

            except Vendor.DoesNotExist:
                raise Http404("Vendor not found")

        else:
            request.vendor = None
            request.is_vendor_subdomain = False

        return None