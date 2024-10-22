// order_management.js

import * as utils from "../utils.js"

document.addEventListener('DOMContentLoaded', function () {
    fetchOrders();
    utils.updateOrderSummary(false)

    // Event listeners for search, filters, and sorting
    document.getElementById('searchInput').addEventListener('input', filterOrders);
    document.getElementById('tableIdFilter').addEventListener('input', filterOrders);

    document.getElementById('statusFilter').addEventListener('change', filterOrders);
    document.getElementById('paymentTypeFilter').addEventListener('change', filterOrders);
    document.getElementById('orderTypeFilter').addEventListener('change', filterOrders);
    document.getElementById('isPaidFilter').addEventListener('change', filterOrders);
    document.getElementById('isRefundedFilter').addEventListener('change', filterOrders);
    document.getElementById('sortBy').addEventListener('change', sortOrders);

    // Event listener for updating order status
    document.getElementById('updateOrderBtn').addEventListener('click', updateOrderStatus);
    document.getElementById('toggleView').addEventListener('click', toggleView)

});

function fetchOrders() {
    fetch('/api/get_orders/')
        .then(response => response.json())
        .then(data => {
            displayPendingOrders(data);
            displayReadyOrders(data);
            displayAllOrders(data);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error fetching orders');
        });
}

function displayPendingOrders(orders) {
    const pendingOrders = orders.filter(order => order.order_status === 'pending');
    const pendingOrdersContainer = document.getElementById('pendingOrders');
    pendingOrdersContainer.innerHTML = '';

    pendingOrders.forEach(order => {
        const orderElement = createOrderElement(order);
        pendingOrdersContainer.appendChild(orderElement);
    });
}

function displayReadyOrders(orders) {
    const readyOrders = orders.filter(order => order.order_status === 'ready');
    const readyOrdersContainer = document.getElementById('readyOrders');
    readyOrdersContainer.innerHTML = '';

    readyOrders.forEach(order => {
        const orderElement = createOrderElement(order);
        readyOrdersContainer.appendChild(orderElement);
    });
}

function displayAllOrders(orders) {
    const allOrdersContainer = document.getElementById('allOrders');
    allOrdersContainer.innerHTML = '';

    orders.forEach(order => {
        const orderElement = createOrderElement(order, 'col-md-4');
        allOrdersContainer.appendChild(orderElement);
    });
}

function createOrderElement(order, colClass = 'col-12') {
    const orderElement = document.createElement('div');
    orderElement.classList.add(colClass, 'mb-3');
    orderElement.innerHTML = `
        <div class="card order-card" data-bs-toggle="modal" data-bs-target="#orderModal" data-order-id="${order.id}">
            <div class="card-body">
                <h5 class="card-title">Order ID: ${order.id} ${order.is_refunded ? '<span style="color:red;">refunded</span>' : ''}</h5>
                <p class="card-text">Table ID: ${order.table_id}</p>
                <p class="card-text">Order Status: ${order.order_status}</p>
                <p class="card-text">Order Type: ${order.order_type}</p>
                <p class="card-text">Payment Type: ${order.payment_type}</p>
                <p class="card-text">Total Price: ${order.total_price}</p>
                <p class="card-text">Created At: ${new Date(order.created_at).toLocaleString()}</p>
                <p class="card-text" style="color: ${order.paid_at ? 'green' : 'red'};">
                    ${order.paid_at ? `Paid At: ${new Date(order.paid_at).toLocaleString()}` : 'Not Paid'}
                </p>
            </div>
        </div>
    `;
    return orderElement;
}

function filterOrders() {
    const searchInput = document.getElementById('searchInput').value.toLowerCase();
    const statusFilter = document.getElementById('statusFilter').value;
    const orderTypeFilter = document.getElementById('orderTypeFilter').value;
    const paymentTypeFilter = document.getElementById('paymentTypeFilter').value;
    const tableIdFilter = document.getElementById('tableIdFilter').value;
    const isPaidFilter = document.getElementById('isPaidFilter').checked;
    const isRefundedFilter = document.getElementById('isRefundedFilter').checked;

    fetch('/api/get_orders/')
        .then(response => response.json())
        .then(data => {
            const filteredOrders = data.filter(order => {
                const matchesSearch = order.id.toString().includes(searchInput);
                const matchesStatus = statusFilter === '' || order.order_status === statusFilter;
                const matchesOrderType = orderTypeFilter === '' || order.order_type === orderTypeFilter;
                const matchesPaymentType = paymentTypeFilter === '' || order.payment_type === paymentTypeFilter;
                const matchesTableId = tableIdFilter === '' || order.table_id === parseInt(tableIdFilter);
                const matchesIsPaid = !isPaidFilter || order.is_paid;
                const matchesIsRefunded = !isRefundedFilter || order.is_refunded;

                return matchesSearch && matchesStatus && matchesOrderType && matchesPaymentType &&
                    matchesTableId && matchesIsPaid && matchesIsRefunded;
            });
            displayAllOrders(filteredOrders);
        })
        .catch(error => {
            console.error('Error:', error);
            alert(error.message);
        });
}

function sortOrders() {
    const sortBy = document.getElementById('sortBy').value;

    fetch('/api/get_orders/')
        .then(response => response.json())
        .then(data => {
            const sortedOrders = data.sort((a, b) => {
                if (sortBy === 'created_at_asc') {
                    return new Date(a.created_at) - new Date(b.created_at);
                } else if (sortBy === 'created_at_desc') {
                    return new Date(b.created_at) - new Date(a.created_at);
                } else if (sortBy === 'paid_at_asc') {
                    const paidAtA = a.paid_at ? new Date(a.paid_at) : Infinity;
                    const paidAtB = b.paid_at ? new Date(b.paid_at) : Infinity;
                    return paidAtA - paidAtB;
                } else if (sortBy === 'paid_at_desc') {
                    const paidAtA = a.paid_at ? new Date(a.paid_at) : -Infinity;
                    const paidAtB = b.paid_at ? new Date(b.paid_at) : -Infinity;
                    return paidAtB - paidAtA;
                }
                return 0;
            });
            displayAllOrders(sortedOrders);
        })
        .catch(error => {
            console.error('Error:', error);
            alert(error.message);
        });
}

function updateOrderStatus() {
    const orderId = document.getElementById('orderModal').getAttribute('data-order-id');
    const orderStatus = document.querySelector('.modal-body button.active').getAttribute('data-status');
    const paymentId = document.getElementById('paymentId').value;
    const isPaid = document.getElementById('isPaid').checked;
    const isRefunded = document.getElementById('isRefunded').checked;
    const privateNote = document.getElementById('privateNote').value;

    const data = {
        order_status: orderStatus,
        payment_id: paymentId,
        is_paid: isPaid,
        is_refunded: isRefunded,
        private_note: privateNote
    };

    fetch(`/api/update_order/${orderId}/`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify(data)
    })
        .then(response => {
            if (!response.ok) {
                return response.json().then(errorData => {
                    throw new Error(errorData.detail ? errorData.detail[0] : 'Unknown error');
                });
            }
            return response.json();
        })
        .then(data => {
            console.log('Order updated:', data);
            fetchOrders();
            document.getElementById('orderModal').classList.remove('show');
            document.querySelector('.modal-backdrop').remove();
        })
        .catch(error => {
            console.error('Error:', error);
            alert(error.message);
        });
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

function toggleView() {
    const splitView = document.getElementById('splitView');
    const allOrdersView = document.getElementById('allOrdersView');

    if (splitView.style.display === 'none') {
        splitView.style.display = 'flex';
        allOrdersView.style.display = 'none';
    } else {
        splitView.style.display = 'none';
        allOrdersView.style.display = 'block';
    }
}

document.addEventListener('click', function (event) {
    if (event.target.closest('.order-card')) {
        const orderId = event.target.closest('.order-card').getAttribute('data-order-id');
        displayOrderDetails(orderId);
    }
});

function displayOrderDetails(orderId) {
    fetch(`/api/get_order/${orderId}/`)
        .then(response => response.json())
        .then(order => {
            const orderDetailsContainer = document.getElementById('orderDetails');
            orderDetailsContainer.innerHTML = `
                <div class="row">
                    <div class="col-md-6">
                        <h5>Order ID: ${order.id}</h5>
                        <p>Table ID: ${order.table_id}</p>
                        <p>Order Status: ${order.order_status}</p>
                        <p>Order Type: ${order.order_type}</p>
                        <p>Payment Type: ${order.payment_type}</p>
                        <p>Payment ID: ${order.payment_id}</p>
                    </div>
                    <div class="col-md-6">
                        <h6>Nutritional Value:</h6>
                        <table class="table table-sm">
                            <tbody>
                                <tr>
                                    <td>Calories</td>
                                    <td>${order.nutritional_value.calories}</td>
                                </tr>
                                <tr>
                                    <td>Proteins</td>
                                    <td>${order.nutritional_value.proteins}</td>
                                </tr>
                                <tr>
                                    <td>Fats</td>
                                    <td>${order.nutritional_value.fats}</td>
                                </tr>
                                <tr>
                                    <td>Saturated Fats</td>
                                    <td>${order.nutritional_value.saturated_fats}</td>
                                </tr>
                                <tr>
                                    <td>Carbohydrates</td>
                                    <td>${order.nutritional_value.carbohydrates}</td>
                                </tr>
                                <tr>
                                    <td>Sugars</td>
                                    <td>${order.nutritional_value.sugars}</td>
                                </tr>
                                <tr>
                                    <td>Fiber</td>
                                    <td>${order.nutritional_value.fiber}</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
                <h6>Products:</h6>
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Name</th>
                            <th>Quantity</th>
                            <th>Price</th>
                            <th>Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${order.products.map(product => `
                            <tr>
                                <td>${product.id}</td>
                                <td>${product.name}<br><small>${product.ingredients.map(ingredient => ingredient.name).join(', ')}</small></td>
                                <td>${product.amount}</td>
                                <td>${product.price}</td>
                                <td>${product.price * product.amount}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
            document.getElementById('orderModal').setAttribute('data-order-id', orderId);
            const statusButtons = document.querySelectorAll('.modal-body button[data-status]');
            statusButtons.forEach(button => {
                if (button.getAttribute('data-status') === order.order_status) {
                    button.classList.add('active');
                } else {
                    button.classList.remove('active');
                }
                button.addEventListener('click', function () {
                    statusButtons.forEach(btn => btn.classList.remove('active'));
                    this.classList.add('active');
                });
            });

            // Load payment ID, is paid, is refunded, and private note
            document.getElementById('paymentId').value = order.payment_id;
            document.getElementById('isPaid').checked = order.is_paid;
            document.getElementById('isRefunded').checked = order.is_refunded;
            document.getElementById('privateNote').value = order.private_note;
        })
        .catch(error => {
            console.error('Error:', error);
            alert(error.message);
        });
}
