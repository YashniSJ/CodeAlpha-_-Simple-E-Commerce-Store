document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".messages .message").forEach(function (msg) {
        setTimeout(() => msg.remove(), 4000);
    });
});

// Homepage banner carousel
(function () {
    const slides = document.querySelectorAll(".banner-slide");
    const dots = document.querySelectorAll(".dot");
    if (slides.length === 0) return;

    let current = 0;

    function showSlide(index) {
        slides.forEach((s, i) => s.classList.toggle("active", i === index));
        dots.forEach((d, i) => d.classList.toggle("active", i === index));
        current = index;
    }

    dots.forEach((dot) => {
        dot.addEventListener("click", () => showSlide(parseInt(dot.dataset.index)));
    });

    setInterval(() => {
        showSlide((current + 1) % slides.length);
    }, 4000);
})();
// AJAX cart add/decrement — no page reload, no scroll jump
document.addEventListener("submit", function (e) {
    const form = e.target;
    if (!form.classList.contains("cart-form")) return;

    e.preventDefault();
    const container = form.closest(".cart-control");
    if (!container) return;

    const productId = container.dataset.productId;
    const style = container.dataset.style;

    fetch(form.action, {
        method: "POST",
        headers: { "X-Requested-With": "XMLHttpRequest" },
        body: new FormData(form),
    })
        .then((res) => res.json())
        .then((data) => {
            const csrfToken = form.querySelector("[name=csrfmiddlewaretoken]").value;
            const addUrl = `/cart/add/${productId}/`;
            const decUrl = `/cart/decrement/${productId}/`;

            if (data.quantity > 0) {
                container.innerHTML = `
                    <div class="mini-stepper">
                        <form class="cart-form" action="${decUrl}" method="post">
                            <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                            <button type="submit" class="qty-btn">−</button>
                        </form>
                        <span class="mini-stepper-count">${data.quantity}</span>
                        <form class="cart-form" action="${addUrl}" method="post">
                            <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                            <button type="submit" class="qty-btn">+</button>
                        </form>
                    </div>`;
            } else {
                const btnClass = style === "mini" ? "btn btn-small-full" : "btn";
                container.innerHTML = `
                    <form class="cart-form" action="${addUrl}" method="post">
                        <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
                        <button type="submit" class="${btnClass}">Add to Cart</button>
                    </form>`;
            }
        })
        .catch(() => {
            // fallback: if anything goes wrong, just submit normally
            form.removeEventListener("submit", arguments.callee);
            form.submit();
        });
});