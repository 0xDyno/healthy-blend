// checkout.js
import storage from './storage.js';

document.addEventListener('DOMContentLoaded', function() {
    const orderSummary = document.getElementById('orderSummary');
    const checkoutButton = document.getElementById('checkoutButton');

    updateOrderSummary();

    checkoutButton.addEventListener('click', submitOrder);
});

function updateOrderSummary() {
    const orderSummary = document.getElementById('orderSummary');
    orderSummary.innerHTML = '';

    const cartItems = storage.getCartItems();

    cartItems.forEach(item => {
        const itemDiv = document.createElement('div');
        itemDiv.innerHTML = `
            <h3>${item.product.name}</h3>
            <ul>
                ${item.product.ingredients ? item.product.ingredients.map(ing => `
                    <li>${ing.name}: ${ing.weight_grams}g</li>
                `).join('') : 'No ingredients'}
            </ul>
            <p>Quantity: ${item.quantity}</p>
        `;
        orderSummary.appendChild(itemDiv);
    });

    const totalDiv = document.createElement('div');
    totalDiv.innerHTML = `<h3>Total: ${storage.getTotalPrice().toFixed(0)} IDR</h3>`;
    orderSummary.appendChild(totalDiv);
}

function submitOrder() {
    const cartItems = storage.getCartItems();
    const orderData = {
        items: cartItems.map(item => ({
            product_id: item.product.id,
            quantity: item.quantity,
            ingredients: item.product.ingredients ? item.product.ingredients.map(ing => ({
                id: ing.id,
                weight: ing.weight_grams
            })) : []
        }))
    };

    fetch('/api/orders/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(orderData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            storage.clearCart();
            window.location.href = `/order-confirmation/${data.order_id}/`;
        } else {
            alert('Error creating order. Please try again.');
        }
    });
}

function getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}