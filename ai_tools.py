"""AI tools for the Services module."""
from assistant.tools import AssistantTool, register_tool


@register_tool
class ListServices(AssistantTool):
    name = "list_services"
    description = "List services with optional search. Returns name, price, duration, category."
    module_id = "services"
    required_permission = "services.view_service"
    parameters = {
        "type": "object",
        "properties": {
            "search": {"type": "string", "description": "Search by name"},
            "category_id": {"type": "string", "description": "Filter by category ID"},
            "limit": {"type": "integer", "description": "Max results (default 20)"},
        },
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from services.models import Service
        qs = Service.objects.select_related('category').all()
        if args.get('search'):
            qs = qs.filter(name__icontains=args['search'])
        if args.get('category_id'):
            qs = qs.filter(category_id=args['category_id'])
        limit = args.get('limit', 20)
        return {
            "services": [
                {
                    "id": str(s.id),
                    "name": s.name,
                    "price": str(s.price),
                    "pricing_type": s.pricing_type,
                    "duration_minutes": s.duration_minutes,
                    "category": s.category.name if s.category else None,
                    "is_bookable": s.is_bookable,
                }
                for s in qs[:limit]
            ],
            "total": qs.count(),
        }


@register_tool
class CreateService(AssistantTool):
    name = "create_service"
    description = "Create a new service."
    module_id = "services"
    required_permission = "services.change_service"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Service name"},
            "price": {"type": "string", "description": "Price"},
            "pricing_type": {"type": "string", "description": "Pricing type: fixed, hourly, from, variable, free"},
            "duration_minutes": {"type": "integer", "description": "Duration in minutes"},
            "description": {"type": "string", "description": "Service description"},
            "is_bookable": {"type": "boolean", "description": "Can be booked online"},
            "category_id": {"type": "string", "description": "Category ID"},
        },
        "required": ["name", "price"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from decimal import Decimal
        from django.utils.text import slugify
        from services.models import Service
        s = Service.objects.create(
            name=args['name'],
            slug=slugify(args['name']),
            price=Decimal(args['price']),
            pricing_type=args.get('pricing_type', 'fixed'),
            duration_minutes=args.get('duration_minutes', 60),
            description=args.get('description', ''),
            is_bookable=args.get('is_bookable', False),
            category_id=args.get('category_id'),
        )
        return {"id": str(s.id), "name": s.name, "created": True}


@register_tool
class ListServiceCategories(AssistantTool):
    name = "list_service_categories"
    description = "List service categories."
    module_id = "services"
    required_permission = "services.view_service"
    parameters = {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from services.models import ServiceCategory
        return {
            "categories": [
                {"id": str(c.id), "name": c.name}
                for c in ServiceCategory.objects.all()
            ]
        }
