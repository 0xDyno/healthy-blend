// kitchen.js

import { REFRESH_INTERVAL, getCookie } from "./utils.js";

document.addEventListener('DOMContentLoaded', function () {
    // DOM Elements
    const ordersBtn = document.getElementById('ordersBtn');
    const ingredientsBtn = document.getElementById('ingredientsBtn');
    const ordersSection = document.getElementById('ordersSection');
    const ingredientsSection = document.getElementById('ingredientsSection');
    const orderModal = document.getElementById('orderModal');

    // Navigation Handling
    ordersBtn.onclick = () => switchSection('orders');
    ingredientsBtn.onclick = () => switchSection('ingredients');

    // Modal Close Handling
    window.onclick = (event) => {
        if (event.target === orderModal) {
            orderModal.style.display = 'none';
        }
    };

    document.querySelector('.close').onclick = () => {
        orderModal.style.display = 'none';
    };

    // Render Functions
    function renderOrders(orders) {
        const ordersList = document.getElementById('ordersList');
        ordersList.innerHTML = orders.map(order => {
            const timeSincePayment = order.paid_at ? getTimeSincePayment(order.paid_at) : '';
            const orderTypeBadge = order.order_type !== 'offline' ?
                `<span class="order-type-badge order-type-${order.order_type}">${order.order_type.toUpperCase()}</span>` : '';

            // Добавляем отображение заметок
            const publicNote = order.public_note ?
                `<div class="note public-note" title="${order.public_note}">📝 ${order.public_note.substring(0, 30)}${order.public_note.length > 30 ? '...' : ''}</div>` : '';
            const privateNote = order.private_note ?
                `<div class="note private-note" title="${order.private_note}">🔒 ${order.private_note.substring(0, 30)}${order.private_note.length > 30 ? '...' : ''}</div>` : '';

            return `
        <div class="order-card" data-id="${order.id}" data-order-type="${order.order_type}">
            <div class="order-header">
                <div>
                    <span class="order-number">Order #${order.id}</span>
                    ${orderTypeBadge}
                </div>
                <div>
                    <span class="payment-time">${timeSincePayment}</span>
                </div>
            </div>
            ${publicNote}
            ${privateNote}
            <div class="order-content">
                ${order.products.map(product => `
                    <div class="product-item">
                        <div class="product-header">
                            <span class="product-name">${product.product_name}</span>
                            <span class="product-amount">×${product.amount}</span>
                        </div>
                        <div class="ingredients-list">
                            ${product.ingredients.map(ing => `
                                <span class="ingredient-pill">
                                    ${ing.name} ${ing.weight_grams}g
                                </span>
                            `).join('')}
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `
        }).join('');

        // Add click handlers
        ordersList.querySelectorAll('.order-card').forEach(card => {
            card.onclick = () => showOrderDetails(
                orders.find(o => o.id === parseInt(card.dataset.id))
            );
        });
    }

    function showOrderDetails(order) {
        const orderTypeBadge = order.order_type !== 'offline' ?
            `<span class="order-type-badge order-type-${order.order_type}">${order.order_type.toUpperCase()}</span>` : '';

        const notesSection = `
        ${order.public_note ? `
            <div class="note-section">
                <h3>Public Note:</h3>
                <p class="full-note public-note">${order.public_note}</p>
            </div>
        ` : ''}
        ${order.private_note ? `
            <div class="note-section">
                <h3>Private Note:</h3>
                <p class="full-note private-note">${order.private_note}</p>
            </div>
        ` : ''}
    `;

        document.getElementById('orderDetails').innerHTML = `
        <div style="display: flex; align-items: center; margin-bottom: 15px;">
            <h2>Order Details #${order.id}</h2>
            ${orderTypeBadge}
        </div>
        ${notesSection}
            ${order.products.map(product => `
                <div class="product-item">
                    <div class="product-header">
                        <span class="product-name">${product.product_name}</span>
                        <span class="product-amount">×${product.amount}</span>
                    </div>
                    <div class="ingredients-list">
                        ${product.ingredients.map(ing => `
                            <span class="ingredient-pill">
                                ${ing.name}
                                <span class="ingredient-weight">&nbsp;${ing.weight_grams}g</span>
                            </span>
                        `).join('')}
                    </div>
                </div>
            `).join('')}
        `;

        document.getElementById('orderReadyBtn').onclick = () => markOrderReady(order.id);
        orderModal.style.display = 'block';
    }

    // API Functions
    async function fetchOrders() {
        try {
            const response = await fetch('/api/get/orders/kitchen/');
            const orders = await response.json();
            renderOrders(orders);
        } catch (error) {
            console.error('Error fetching orders:', error);
        }
    }

    function getTimeSincePayment(paidAt) {
        const paid = new Date(paidAt);
        const now = new Date();
        const diffInMinutes = Math.floor((now - paid) / 1000 / 60);

        if (diffInMinutes < 60) {
            return `${diffInMinutes}m ago`;
        } else {
            const hours = Math.floor(diffInMinutes / 60);
            const minutes = diffInMinutes % 60;
            return `${hours}h ${minutes}m ago`;
        }
    }

    async function markOrderReady(orderId) {
        try {
            await fetch(`/api/update/order/${orderId}/`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });
            orderModal.style.display = 'none';
            fetchOrders();
        } catch (error) {
            console.error('Error updating order:', error);
        }
    }

    // Utility Functions
    function switchSection(section) {
        if (section === 'orders') {
            ordersSection.classList.add('active');
            ingredientsSection.classList.remove('active');
            ordersBtn.classList.add('active');
            ingredientsBtn.classList.remove('active');
            fetchOrders();
        } else {
            ingredientsSection.classList.add('active');
            ordersSection.classList.remove('active');
            ingredientsBtn.classList.add('active');
            ordersBtn.classList.remove('active');
            // Вызываем событие для обновления ингредиентов
            window.dispatchEvent(new Event('fetchIngredients'));
        }
    }

    // Initial load
    fetchOrders();

    // Auto-refresh
    setInterval(() => {
        if (ordersSection.classList.contains('active')) {
            fetchOrders();
        }
    }, REFRESH_INTERVAL);
});