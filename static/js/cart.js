// cart.js
import storage from './storage.js';

document.addEventListener('DOMContentLoaded', function () {
    updateCartUI();
    updateOrderSummary();

    document.getElementById('checkoutButton').addEventListener('click', handleCheckout);
});

function updateCartUI() {
    const cartItemsContainer = document.getElementById('cartItems');
    const cartTotalElement = document.getElementById('cartTotalRes');

    cartItemsContainer.innerHTML = '';
    let total = 0;

    const { officialMeals, customMeals } = storage.getCartItemsSet();

    if (officialMeals.length === 0 && customMeals.length === 0) {
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

        officialMeals.forEach((item, index) => {
            const row = createTableRow(item, index, 'official');
            tableBody.appendChild(row);
            total += item.product.nutritional_value.price * item.quantity;
        });

        customMeals.forEach((item, index) => {
            const row = createTableRow(item, index, 'custom');
            tableBody.appendChild(row);
            total += item.product.nutritional_value.price * item.quantity;
        });

        addRemoveEventListeners();
    }

    cartTotalElement.textContent = `${total.toFixed(0)} IDR`;
}

function createTableRow(item, index, type) {
    const row = document.createElement('tr');
    row.innerHTML = `
        <td>
            ${item.product.name}
            ${type === 'custom' ? createIngredientsList(item.product.ingredients) : ''}
        </td>
        <td>${(item.product.nutritional_value.calories).toFixed(0)}</td>
        <td>${item.quantity}</td>
        <td>${item.product.nutritional_value.price.toFixed(0)} IDR</td>
        <td>${(item.product.nutritional_value.price * item.quantity).toFixed(0)} IDR</td>
        <td><button class="btn btn-sm btn-danger remove-from-cart" data-type="${type}" data-id="${item.product.id}" 
        data-calories="${item.product.nutritional_value.calories}">Remove</button></td>
    `;
    return row;
}

function createIngredientsList(ingredients) {
    if (!ingredients || ingredients.length === 0) return '';

    const ingredientsList = ingredients.map(ing => `<li>${ing.name}, ${ing.weight_grams}g</li>`).join('');
    return `
        <small class="d-block mt-1">
            Ingredients:
            <ul class="list-unstyled ml-3 mb-0">
                ${ingredientsList}
            </ul>
        </small>
    `;
}

function addRemoveEventListeners() {
    document.querySelectorAll('.remove-from-cart').forEach(button => {
        button.addEventListener('click', function () {
            const type = this.getAttribute('data-type');
            const id = this.getAttribute('data-id');
            const calories = this.getAttribute('data-calories');
            storage.removeItem(id, calories, type === 'official');
            updateCartUI();
            updateOrderSummary();
        });
    });
}

function updateOrderSummary() {
    const { officialMeals, customMeals } = storage.getCartItemsSet();
    const allItems = [...officialMeals, ...customMeals];

    const summary = allItems.reduce((acc, item) => {
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

    document.getElementById('totalKcal').textContent = summary.kcal.toFixed(0);
    document.getElementById('totalFat').textContent = summary.fat.toFixed(1);
    document.getElementById('totalSaturatedFat').textContent = summary.saturatedFat.toFixed(1);
    document.getElementById('totalCarbs').textContent = summary.carbs.toFixed(1);
    document.getElementById('totalSugar').textContent = summary.sugar.toFixed(1);
    document.getElementById('totalFiber').textContent = summary.fiber.toFixed(1);
    document.getElementById('totalProtein').textContent = summary.protein.toFixed(1);

    // Обновление общей стоимости
    const cartTotalElement = document.getElementById('cartTotal');
    if (cartTotalElement) {
        cartTotalElement.textContent = `${summary.total.toFixed(0)} IDR`;
    }

    // Обновление количества товаров в корзине в навигационной панели
    const cartItemCountElement = document.getElementById('cartItemCount');
    if (cartItemCountElement) {
        cartItemCountElement.textContent = allItems.reduce((total, item) => total + item.quantity, 0);
    }
}

function handleCheckout() {
    const paymentType = document.getElementById('paymentType').value;

    if (!paymentType) {
        alert('Please select a payment type');
        return;
    }

    const { officialMeals, customMeals } = storage.getCartItemsSet();
    const totalPrice = storage.getTotalPrice();

    const cartData = {
        price: totalPrice,
        payment_type: paymentType,
        officialMeals: officialMeals.map(item => ({
            id: item.product.id,
            calories: item.product.nutritional_value.calories,
            quantity: item.quantity,
            price: item.product.nutritional_value.price,
        })),
        customMeals: customMeals.map(item => ({
            ingredients: item.product.ingredients.map(ing => ({
                id: ing.id,
                weight: ing.weight_grams,
            })),
            quantity: item.quantity,
            price: item.product.nutritional_value.price,
        }))
    };

    fetch('/checkout/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        },
        body: JSON.stringify(cartData),
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // storage.clearCart();
            // storage.clearCustomMeals();
            updateCartUI();
            updateOrderSummary();
            window.location.href = data.redirect_url;
        } else {
            console.error('Checkout failed:', data.error);
            // Здесь можно добавить отображение ошибки для пользователя
        }
    })
    .catch(error => console.error('Error:', error));
}