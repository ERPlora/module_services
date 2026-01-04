from django.apps import AppConfig


class ServicesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "services"
    verbose_name = "Services"

    def ready(self):
        pass

    @staticmethod
    def do_before_service_book(service, customer) -> dict:
        """Called before booking a service."""
        return {"allow": True}

    @staticmethod
    def do_after_service_complete(service, customer) -> None:
        """Called after service is completed."""
        pass

    @staticmethod
    def filter_services_list(queryset, request):
        """Filter services queryset."""
        return queryset
