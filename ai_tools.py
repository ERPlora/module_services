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
    examples = [
        {"name": "Corte + Peinado", "price": "25.00", "duration_minutes": 45, "pricing_type": "fixed"},
        {"name": "Consulta Inicial", "price": "0", "duration_minutes": 30, "pricing_type": "free", "is_bookable": True},
    ]
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


@register_tool
class CreateServiceCategory(AssistantTool):
    name = "create_service_category"
    description = "Create a service category (e.g., 'Cortes', 'Color', 'Tratamientos')."
    module_id = "services"
    required_permission = "services.change_service"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Category name"},
            "icon": {"type": "string", "description": "Icon name"},
            "color": {"type": "string", "description": "Hex color"},
        },
        "required": ["name"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from django.utils.text import slugify
        from services.models import ServiceCategory
        c = ServiceCategory.objects.create(
            name=args['name'],
            slug=slugify(args['name']),
            icon=args.get('icon', ''),
            color=args.get('color', ''),
        )
        return {"id": str(c.id), "name": c.name, "created": True}


@register_tool
class UpdateService(AssistantTool):
    name = "update_service"
    description = "Update an existing service."
    module_id = "services"
    required_permission = "services.change_service"
    requires_confirmation = True
    parameters = {
        "type": "object",
        "properties": {
            "service_id": {"type": "string", "description": "Service ID"},
            "name": {"type": "string"}, "price": {"type": "string"},
            "duration_minutes": {"type": "integer"}, "description": {"type": "string"},
            "is_bookable": {"type": "boolean"}, "category_id": {"type": "string"},
        },
        "required": ["service_id"],
        "additionalProperties": False,
    }

    def execute(self, args, request):
        from decimal import Decimal
        from services.models import Service
        s = Service.objects.get(id=args['service_id'])
        if 'name' in args:
            s.name = args['name']
        if 'price' in args:
            s.price = Decimal(args['price'])
        if 'duration_minutes' in args:
            s.duration_minutes = args['duration_minutes']
        if 'description' in args:
            s.description = args['description']
        if 'is_bookable' in args:
            s.is_bookable = args['is_bookable']
        if 'category_id' in args:
            s.category_id = args['category_id']
        s.save()
        return {"id": str(s.id), "name": s.name, "updated": True}
