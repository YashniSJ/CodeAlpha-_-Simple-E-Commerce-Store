from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction

from .models import Product, Category, Cart, CartItem, Order, OrderItem
from .forms import RegisterForm, CheckoutForm


def get_or_create_cart(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    return cart


CATEGORY_ICONS = {
    "electronics": "📱",
    "fashion": "👗",
    "clothing": "👕",
    "footwear": "👟",
    "home": "🏠",
    "kitchen": "🍳",
    "beauty": "💄",
    "personal care": "🧴",
    "books": "📚",
    "stationery": "✏️",
    "sports": "🏋️",
    "fitness": "🏋️",
    "toys": "🧸",
    "games": "🎮",
    "groceries": "🛒",
    "mobile": "📱",
    "accessories": "🎧",
}


def get_category_icon(name):
    name_lower = name.lower()
    for keyword, icon in CATEGORY_ICONS.items():
        if keyword in name_lower:
            return icon
    return "🛍️"


def landing(request):
    return render(request, "store/landing.html")


def home(request):
    categories = Category.objects.all()
    new_arrivals = Product.objects.order_by("-created_at")[:8]
    top_picks = Product.objects.filter(stock__gt=0).order_by("?")[:8]

    categories_with_icons = [
        {"category": c, "icon": get_category_icon(c.name)} for c in categories
    ]

    category_sections = []
    for category in categories:
        products = category.products.all()[:8]
        if products:
            category_sections.append({"category": category, "products": products})

    cart_quantities = {}
    if request.user.is_authenticated:
        cart = get_or_create_cart(request)
        cart_quantities = {item.product_id: item.quantity for item in cart.items.all()}

    return render(request, "store/home.html", {
        "categories": categories,
        "categories_with_icons": categories_with_icons,
        "new_arrivals": new_arrivals,
        "top_picks": top_picks,
        "category_sections": category_sections,
        "cart_quantities": cart_quantities,
    })


def product_list(request):
    products = Product.objects.all().order_by("-created_at")
    categories = Category.objects.all()

    category_slug = request.GET.get("category")
    if category_slug:
        products = products.filter(category__slug=category_slug)

    query = request.GET.get("q")
    if query:
        products = products.filter(name__icontains=query)

    cart_quantities = {}
    if request.user.is_authenticated:
        cart = get_or_create_cart(request)
        cart_quantities = {item.product_id: item.quantity for item in cart.items.all()}

    return render(request, "store/product_list.html", {
        "products": products,
        "categories": categories,
        "selected_category": category_slug,
        "query": query or "",
        "cart_quantities": cart_quantities,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    return render(request, "store/product_detail.html", {"product": product})


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created! Welcome.")
            return redirect("home")
    else:
        form = RegisterForm()
    return render(request, "store/register.html", {"form": form})


@login_required
def cart_detail(request):
    cart = get_or_create_cart(request)
    return render(request, "store/cart_detail.html", {"cart": cart})


@login_required
def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = get_or_create_cart(request)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity += 1
    item.save()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"quantity": item.quantity})

    messages.success(request, f"Added {product.name} to your cart.")
    return redirect(request.META.get("HTTP_REFERER", "home"))


@login_required
def cart_decrement(request, product_id):
    cart = get_or_create_cart(request)
    quantity = 0
    try:
        item = CartItem.objects.get(cart=cart, product_id=product_id)
        item.quantity -= 1
        if item.quantity <= 0:
            item.delete()
            quantity = 0
        else:
            item.save()
            quantity = item.quantity
    except CartItem.DoesNotExist:
        pass

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"quantity": quantity})

    return redirect(request.META.get("HTTP_REFERER", "home"))


@login_required
def cart_update(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    if request.method == "POST":
        quantity = int(request.POST.get("quantity", 1))
        if quantity <= 0:
            item.delete()
        else:
            item.quantity = quantity
            item.save()
    return redirect("cart_detail")


@login_required
def cart_remove(request, item_id):
    item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    item.delete()
    return redirect("cart_detail")


@login_required
def checkout(request):
    cart = get_or_create_cart(request)
    if cart.items.count() == 0:
        messages.warning(request, "Your cart is empty.")
        return redirect("home")

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                order = form.save(commit=False)
                order.user = request.user
                order.status = "pending"
                order.save()

                for cart_item in cart.items.select_related("product"):
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        price=cart_item.product.price,
                        quantity=cart_item.quantity,
                    )
                    cart_item.product.stock = max(0, cart_item.product.stock - cart_item.quantity)
                    cart_item.product.save()

                cart.items.all().delete()

            messages.success(request, "Order placed successfully!")
            return redirect("order_detail", order_id=order.id)
    else:
        form = CheckoutForm()

    return render(request, "store/checkout.html", {"form": form, "cart": cart})


@login_required
def order_list(request):
    orders = Order.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "store/order_list.html", {"orders": orders})


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, "store/order_detail.html", {"order": order})


@login_required
def profile(request):
    orders_count = request.user.orders.count()
    return render(request, "store/profile.html", {
        "orders_count": orders_count,
    })