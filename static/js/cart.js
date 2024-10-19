// cart.js
import storage from './storage.js';

document.addEventListener('DOMContentLoaded', function () {
    updateCartUI();
    updateOrderSummary();

    document.getElementById('checkoutButton').addEventListener('click', handleCheckout);
});

function updateCartUI() {
    const cartItemsContainer = document.getElementById('cartItems');
    const cartTotalElement = document.getElementById('cartTotal');

    cartItemsContainer.innerHTML = '';
    let total = 0;

    const cartItems = storage.getCartItems();

    if (cartItems.length === 0) {
        cartItemsContainer.innerHTML = '<p>Your cart is empty.</p>';
    } else {
        const table = document.createElement('table');
        table.className = 'table';
        table.innerHTML = `
            <thead>
                <tr>
                    <th>Product</th>
                    <th>Calories</th>
                    <th>Quantity</th>
                    <th>Price</th>
                    <th>Total</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody id="cartTableBody"></tbody>
        `;
        cartItemsContainer.appendChild(table);

        const tableBody = document.getElementById('cartTableBody');
        cartItems.forEach((item, index) => {
            const row = tableBody.insertRow();
            console.log(item)
            row.innerHTML = `
                <td>${item.product.name}</td>
                <td>${item.product.selectedCalories || item.product.nutritional_value.calories}</td>
                <td>${item.quantity}</td>
                <td>${item.product.nutritional_value.price.toFixed(0)} IDR</td>
                <td>${(item.product.nutritional_value.price * item.quantity).toFixed(0)} IDR</td>
                <td><button class="btn btn-sm btn-danger remove-from-cart" data-index="${index}">Remove</button></td>
            `;
            total += item.product.nutritional_value.price * item.quantity;
        });

        document.querySelectorAll('.remove-from-cart').forEach(button => {
            button.addEventListener('click', function () {
                const index = this.getAttribute('data-index');
                const item = cartItems[index];
                storage.removeItem(item.product.id, item.product.selectedCalories);
                updateCartUI();
                updateOrderSummary();
            });
        });
    }

    cartTotalElement.textContent = total.toFixed(0);
}

function updateOrderSummary() {
    const cartItems = storage.getCartItems();
    const summary = cartItems.reduce((acc, item) => {
        const nutritionalInfo = item.product.nutritional_value;
        acc.total += nutritionalInfo.price * item.quantity;
        acc.kcal += nutritionalInfo.calories * item.quantity;
        acc.fat += nutritionalInfo.fats * item.quantity;
        acc.saturatedFat += nutritionalInfo.saturated_fats * item.quantity;
        acc.carbs += nutritionalInfo.carbohydrates * item.quantity;
        acc.sugar += nutritionalInfo.sugars * item.quantity;
        acc.fiber += nutritionalInfo.fiber * item.quantity;
        acc.protein += nutritionalInfo.proteins * item.quantity;
        return acc;
    }, {total: 0, kcal: 0, fat: 0, saturatedFat: 0, carbs: 0, sugar: 0, fiber: 0, protein: 0});

    document.getElementById('totalPrice').textContent = summary.total.toFixed(0);
    document.getElementById('totalKcal').textContent = summary.kcal.toFixed(0);
    document.getElementById('totalFat').textContent = summary.fat.toFixed(1);
    document.getElementById('totalSaturatedFat').textContent = summary.saturatedFat.toFixed(1);
    document.getElementById('totalCarbs').textContent = summary.carbs.toFixed(1);
    document.getElementById('totalSugar').textContent = summary.sugar.toFixed(1);
    document.getElementById('totalFiber').textContent = summary.fiber.toFixed(1);
    document.getElementById('totalProtein').textContent = summary.protein.toFixed(1);

    // Обновление количества товаров в корзине в навигационной панели
    const cartItemCountElement = document.getElementById('cartItemCount');
    if (cartItemCountElement) {
        cartItemCountElement.textContent = cartItems.reduce((total, item) => total + item.quantity, 0);
    }

    // Обновление общей стоимости в навигационной панели
    const cartTotalElement = document.getElementById('cartTotal');
    if (cartTotalElement) {
        cartTotalElement.textContent = `${storage.getTotalPrice().toFixed(0)} IDR`;
    }
}

function handleCheckout() {
    const cartItems = storage.getCartItems();
    if (cartItems.length > 0) {
        fetch('/checkout/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
            },
            body: JSON.stringify({cart: cartItems}),
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    storage.clearCart();
                    updateCartUI();
                    updateOrderSummary();
                    window.location.href = data.redirect_url;
                } else {
                    console.error('Checkout failed:', data.error);
                }
            })
            .catch(error => console.error('Error:', error));
    }
}