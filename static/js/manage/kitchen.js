// kitchen.js

document.addEventListener('DOMContentLoaded', function () {
    // DOM Elements
    const ordersBtn = document.getElementById('ordersBtn');
    const ingredientsBtn = document.getElementById('ingredientsBtn');
    const ordersSection = document.getElementById('ordersSection');
    const ingredientsSection = document.getElementById('ingredientsSection');
    const orderModal = document.getElementById('orderModal');
    const ingredientModal = document.getElementById('ingredientModal');

    // Navigation Handling
    ordersBtn.onclick = () => switchSection('orders');
    ingredientsBtn.onclick = () => switchSection('ingredients');

    // Modal Close Handling
    window.onclick = (event) => {
        if (event.target === orderModal || event.target === ingredientModal) {
            orderModal.style.display = 'none';
            ingredientModal.style.display = 'none';
        }
    };

    document.querySelectorAll('.close').forEach(btn => {
        btn.onclick = () => {
            orderModal.style.display = 'none';
            ingredientModal.style.display = 'none';
        };
    });

    // Render Functions
    function renderOrders(orders) {
        const ordersList = document.getElementById('ordersList');
        ordersList.innerHTML = orders.map(order => {
            const timeSincePayment = order.paid_at ? getTimeSincePayment(order.paid_at) : '';

            return `
        <div class="order-card" data-id="${order.id}">
            <div class="order-header">
                <span class="order-number">Order #${order.id}</span>
                <div>
                    <span class="payment-time">${timeSincePayment}</span>
                </div>
            </div>
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

    function renderIngredients(ingredients) {
        const ingredientsList = document.getElementById('ingredientsList');
        ingredientsList.innerHTML = ingredients.map(ingredient => `
            <div class="ingredient-card ${!ingredient.available ? 'unavailable' : ''}" 
                 data-id="${ingredient.id}">
                <img src="${ingredient.image}" alt="${ingredient.name}">
                <h3>${ingredient.name}</h3>
                <p>${ingredient.ingredient_type}</p>
                <p class="status">${ingredient.available ? 'Available' : 'Unavailable'}</p>
            </div>
        `).join('');

        ingredientsList.querySelectorAll('.ingredient-card').forEach(card => {
            card.onclick = () => showIngredientDetails(
                ingredients.find(i => i.id === parseInt(card.dataset.id))
            );
        });
    }

    // Modal Content Functions
    function showOrderDetails(order) {
        document.getElementById('orderDetails').innerHTML = `
            <h2>Order Details</h2>
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

    function showIngredientDetails(ingredient) {
        document.getElementById('ingredientDetails').innerHTML = `
        <div style="display: flex; gap: 20px;">
            <div style="flex: 1;">
                <h2>${ingredient.name}</h2>
                <p>Type: ${ingredient.ingredient_type}</p>
                <p>${ingredient.description}</p>
            </div>
            <div>
                <img src="${ingredient.image}" alt="${ingredient.name}" 
                     style="width: 200px; height: 200px; object-fit: cover; border-radius: 8px;">
            </div>
        </div>
    `;

        const statusBtn = document.getElementById('ingredientStatusBtn');
        statusBtn.textContent = ingredient.available ? 'Mark as Unavailable' : 'Mark as Available';
        statusBtn.style.backgroundColor = ingredient.available ? 'var(--danger-color)' : 'var(--success-color)';
        statusBtn.onclick = () => updateIngredientStatus(ingredient.id);
        ingredientModal.style.display = 'block';
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

    async function fetchIngredients() {
        try {
            const response = await fetch('/api/get/ingredients/');
            const ingredients = await response.json();
            renderIngredients(ingredients);
        } catch (error) {
            console.error('Error fetching ingredients:', error);
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

    async function updateIngredientStatus(ingredientId) {
        try {
            await fetch(`/api/update/ingredient/${ingredientId}/`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                }
            });
            ingredientModal.style.display = 'none';
            fetchIngredients();
        } catch (error) {
            console.error('Error updating ingredient:', error);
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
            fetchIngredients();
        }
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // Initial load
    fetchOrders();

    // Auto-refresh
    setInterval(() => {
        if (ordersSection.classList.contains('active')) {
            fetchOrders();
        } else {
            fetchIngredients();
        }
    }, 10000);
});