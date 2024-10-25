// orders_control.js

import * as utils from "./utils.js";

document.addEventListener('DOMContentLoaded', function () {
    loadControlOrders();

    // Event listener for updating order status
    document.getElementById('updateOrderBtn').addEventListener('click', utils.updateOrderStatus);
});

export function loadControlOrders() {
    utils.fetchOrders((data) => {
        displayPendingOrders(data);
        displayReadyOrders(data);
    });
}

function displayPendingOrders(orders) {
    const pendingOrders = orders.filter(order => order.order_status === 'pending');
    const pendingOrdersContainer = document.getElementById('pendingOrders');
    pendingOrdersContainer.innerHTML = '';

    pendingOrders.reverse().forEach(order => {
        const orderElement = utils.createOrderElement(order);
        pendingOrdersContainer.appendChild(orderElement);
    });
}

function displayReadyOrders(orders) {
    const readyOrders = orders.filter(order => order.order_status === 'ready');
    const readyOrdersContainer = document.getElementById('readyOrders');
    readyOrdersContainer.innerHTML = '';

    readyOrders.forEach(order => {
        const orderElement = utils.createOrderElement(order);
        readyOrdersContainer.appendChild(orderElement);
    });
}

document.addEventListener('click', function (event) {
    if (event.target.closest('.order-card')) {
        const orderId = event.target.closest('.order-card').getAttribute('data-order-id');
        utils.displayOrderDetails(orderId);
    }
});

export function refreshOrders() {
    loadControlOrders();
}