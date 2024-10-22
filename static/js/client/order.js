// order.js

import * as utils from '../utils.js';

document.addEventListener('DOMContentLoaded', function() {
    fetchOrderDetails();
    utils.updateOrderSummary(false)
});

function fetchOrderDetails() {
    fetch('/api/get_orders/')
        .then(response => response.json())
        .then(data => {
            if (data.length > 0) {
                displayOrderDetails(data[0]);
            } else {
                console.error('No order data received');
            }
        })
        .catch(error => console.error('Error:', error));
}

function displayOrderDetails(order) {
    // Display the order ID and status
    document.getElementById('order-id').textContent = order.id;
    document.getElementById('order-status').textContent = order.order_status;

    // Determine the payment status based on order.is_paid
    const paidStatus = order.is_paid ? 'Paid' : 'Not Paid';
    const paidStatusElement = document.getElementById('order-paid-status');
    paidStatusElement.textContent = paidStatus;

    // Add appropriate background color class based on the payment status
    paidStatusElement.classList.add(order.is_paid ? 'bg-success' : 'bg-danger');

    // Set the text color based on the payment status in another element
    const paymentStatusElement = document.getElementById('payment-status');
    paymentStatusElement.style.color = order.is_paid ? 'green' : 'red';

    // Display payment time if the order is paid, otherwise display order creation time
    const paymentTimeElement = document.getElementById('payment-time');
    if (order.is_paid && order.paid_at) {
        paymentTimeElement.textContent = `Paid: ${new Date(order.paid_at).toLocaleString()}`;
    } else {
        paymentTimeElement.textContent = `Ordered: ${new Date(order.created_at).toLocaleString()}`;
    }

    // Display the list of products and nutritional value details
    displayProducts(order.products);
    displayNutritionalValue(order.nutritional_value);

    // Display the total price of the order
    console.log(order)
    document.getElementById('total-price').textContent = `${order.total_price}`;
}

function displayProducts(products) {
    const productList = document.getElementById('product-list');
    productList.innerHTML = '';

    products.forEach((product, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${product.product_name}</td>
            <td>${product.amount}</td>
            <td>${product.price} IDR</td>
            <td>${utils.formatNumber(product.price * product.amount, 0)} IDR</td>
        `;
        productList.appendChild(row);
    });
}

function displayNutritionalValue(nutritionalValue) {
    const nutritionRows = [
        document.getElementById('nutrition-row-1'),
        document.getElementById('nutrition-row-2'),
        document.getElementById('nutrition-row-3')
    ];

    const nutritionData = [
        ['calories', 'fats', 'saturated_fats', 'carbohydrates', 'sugars', 'fiber', 'proteins'],
        ['vitamin_a', 'vitamin_c', 'vitamin_d', 'vitamin_e', 'vitamin_k', 'thiamin', 'riboflavin', 'niacin', 'vitamin_b6', 'folate', 'vitamin_b12'],
        ['calcium', 'iron', 'magnesium', 'phosphorus', 'potassium', 'sodium', 'zinc', 'copper', 'manganese', 'selenium']
    ];

    nutritionRows.forEach((row, index) => {
        const cells = row.getElementsByClassName('nutrition-cell');
        nutritionData[index].forEach((nutrient, cellIndex) => {
            const value = nutritionalValue[nutrient] !== undefined ?
                (nutritionalValue[nutrient] === 0 ? '0' : utils.formatNumber(nutritionalValue[nutrient], 1)) : 'N/A';

            // Сначала получаем текст ячейки, чтобы сохранить название, затем добавляем значение
            const nutrientName = cells[cellIndex].textContent.split(':')[0]; // Оставляем название до символа ":"
            cells[cellIndex].textContent = `${nutrientName}: ${value}`;
        });
    });
}