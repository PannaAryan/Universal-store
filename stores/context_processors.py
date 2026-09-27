def dashboard(request):
    store = getattr(request, "store", None)
    if store is None:
        return {}
    return {"pending_count": store.orders.filter(status="pending").count()}
