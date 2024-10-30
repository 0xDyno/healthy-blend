// orders_all.js

import * as utils from "./utils.js";

const is_admin = utils.getUserRole() === 'owner' || utils.getUserRole() === 'administrator'

document.addEventListener('DOMContentLoaded', function () {
    loadAllOrders();

    // Event listeners for search, filters, and sorting
    document.getElementById('searchInput').addEventListener('input', filterOrders);
    document.getElementById('statusFilter').addEventListener('change', filterOrders);
    document.getElementById('paymentTypeFilter').addEventListener('change', filterOrders);
    document.getElementById('isPaidFilter').addEventListener('change', filterOrders);

    document.getElementById('tableIdFilter').addEventListener('input', filterOrders);
    document.getElementById('orderTypeFilter').addEventListener('change', filterOrders);
    document.getElementById('paymentIdFilter').addEventListener('input', filterOrders);
    document.getElementById('isRefundedFilter').addEventListener('change', filterOrders);

    document.getElementById('sortBy').addEventListener('change', filterOrders);
    if (is_admin) {
        document.getElementById("filterDate").addEventListener('change', filterOrders);
    }
    document.getElementById('clearFilters').addEventListener('click', clearFilters);

    document.getElementById('updateOrderBtn').addEventListener('click', utils.updateOrderStatus);
});

export function loadAllOrders() {
    utils.fetchOrders((data) => {
        displayAllOrders(data);
    });
}

function displayAllOrders(orders) {
    const allOrdersContainer = document.getElementById('allOrders');
    allOrdersContainer.innerHTML = '';

    orders.forEach(order => {
        const orderElement = utils.createOrderElement(order, 'col-md-4');
        allOrdersContainer.appendChild(orderElement);
    });
}

function filterOrders() {
    const searchInput = document.getElementById('searchInput').value;
    const statusFilter = document.getElementById('statusFilter').value;
    const paymentTypeFilter = document.getElementById('paymentTypeFilter').value;
    const isPaidFilter = document.getElementById('isPaidFilter').checked;

    const tableIdFilter = document.getElementById('tableIdFilter').value;
    const orderTypeFilter = document.getElementById('orderTypeFilter').value;
    const paymentIdFilter = document.getElementById('paymentIdFilter').value;
    const isRefundedFilter = document.getElementById('isRefundedFilter').checked;

    const sortBy = document.getElementById('sortBy').value;

    const params = new URLSearchParams({
        search: searchInput,
        status: statusFilter,
        payment_type: paymentTypeFilter,
        is_paid: isPaidFilter,

        table_id: tableIdFilter,
        order_type: orderTypeFilter,
        payment_id: paymentIdFilter,
        is_refunded: isRefundedFilter,

        sort_by: sortBy
    });

    if (is_admin) {
        const date = document.getElementById("filterDate").value;
        params.append("date", date);
    }

    fetch(`/api/control/get/orders/?${params.toString()}`)
        .then(response => response.json())
        .then(data => {
            if (data.messages) {
                MessageManager.handleAjaxMessages(data.messages);
            }

            if (data.orders) {
                displayAllOrders(data.orders);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

function clearFilters() {
    document.getElementById('searchInput').value = '';
    document.getElementById('tableIdFilter').value = '';
    document.getElementById('statusFilter').value = '';
    document.getElementById('orderTypeFilter').value = '';
    document.getElementById('paymentTypeFilter').value = '';
    document.getElementById('paymentIdFilter').value = '';
    document.getElementById('sortBy').value = '';
    document.getElementById('isPaidFilter').checked = false;
    document.getElementById('isRefundedFilter').checked = false;
    if (is_admin) {
        document.getElementById('filterDate').value = '';
    }

    if (document.getElementById('createdAtFilter')) {
        document.getElementById('createdAtFilter').value = '';
    }

    loadAllOrders();
}

document.addEventListener('click', function (event) {
    if (event.target.closest('.order-card')) {
        const orderId = event.target.closest('.order-card').getAttribute('data-order-id');
        utils.displayOrderDetails(orderId);
    }
});

export function refreshOrders() {
    loadAllOrders();
}