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
    fetch('/api/get/orders/')
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
                <p class="card-text">${order.user_role} # ${order.user_id}</p>
                <p class="card-text">Order Status: ${order.order_status}</p>
                <p class="card-text">Order Type: ${order.order_type}</p>
                <p class="card-text">Payment Type: ${order.payment_type}</p>
                <p class="card-text">Total Price: ${order.total_price}</p>
                <p class="card-text">Created At: ${new Date(order.created_at).toLocaleString()}</p>
                <p class="card-text" style="color: ${order.paid_at ? 'green' : 'red'};">
                    ${order.paid_at ? `Paid: ${new Date(order.paid_at).toLocaleString()}` : 'Not Paid'}
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

    fetch('/api/get/orders/')
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

    fetch('/api/get/orders/')
        .then(response => response.json())
        .then(data => {
            const sortedOrders = data.sort((a, b) => {
                if (sortBy === 'created_at_asc') {
                    return new Date(a.created_at) - new Date(b.created_at);
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
    const orderStatus = document.querySelector('.modal-body button[data-status].active').getAttribute('data-status');
    const orderType = document.querySelector('.modal-body button[data-order-type].active').getAttribute('data-order-type');
    const paymentType = document.querySelector('.modal-body button[data-payment-type].active').getAttribute('data-payment-type');
    const paymentId = document.getElementById('paymentId').value;
    const isPaid = document.getElementById('isPaid').checked;
    const isRefunded = document.getElementById('isRefunded').checked;
    const privateNote = document.getElementById('privateNote').value;

    const data = {
        order_status: orderStatus,
        order_type: orderType,
        payment_type: paymentType,
        payment_id: paymentId,
        is_paid: isPaid,
        is_refunded: isRefunded,
        private_note: privateNote
    };

    fetch(`/api/update/order/${orderId}/`, {
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
    fetch(`/api/get/order/${orderId}/`)
        .then(response => response.json())
        .then(order => {
            const orderDetailsContainer = document.getElementById('orderDetails');
            orderDetailsContainer.innerHTML = `
                <div class="row">
                    <div class="col-md-6">
                        <h5>Order #${order.id} - ${order.user_role} ${order.user_id}</h5>
                        <p>${order.user_role} # ${order.user_id}</p>
                    </div>
                </div>
                <table class="table table-sm">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th class="text-center" >Amount</th>
                            <th class="text-center" >Price</th>
                            <th class="text-center" >Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${order.products.map(product => `
                            <tr>
                                <td>${product.name}<br><small>${product.ingredients.map(ingredient => ingredient.name).join(', ')}</small></td>
                                <td class="text-center" style="width: 100px">${product.amount}</td>
                                <td class="text-center" style="width: 100px">${product.price}</td>
                                <td class="text-center" style="width: 100px">${product.price * product.amount}</td>
                            </tr>
                        `).join('')}
                        <tr>
                            <td class="text-center">Total Price</td>
                            <td colspan="3" class="text-center">${order.total_price}</td>
                        </tr>
                    </tbody>
                </table>
            `;
            document.getElementById('orderModal').setAttribute('data-order-id', orderId);
            // Обработка статуса заказа
            const statusButtons = document.querySelectorAll('.modal-body button[data-status]');
            statusButtons.forEach(button => {
                if (button.getAttribute('data-status') === order.order_status) {
                    button.classList.add('active');
                } else {
                    button.classList.remove('active');
                }
            });

            // Обработка типа заказа
            const orderTypeButtons = document.querySelectorAll('.modal-body button[data-order-type]');
            orderTypeButtons.forEach(button => {
                if (button.getAttribute('data-order-type') === order.order_type) {
                    button.classList.add('active');
                } else {
                    button.classList.remove('active');
                }
            });

            // Обработка типа оплаты
            const paymentTypeButtons = document.querySelectorAll('.modal-body button[data-payment-type]');
            paymentTypeButtons.forEach(button => {
                if (button.getAttribute('data-payment-type') === order.payment_type) {
                    button.classList.add('active');
                } else {
                    button.classList.remove('active');
                }
            });

            // Добавляем обработчики событий для всех кнопок
            document.querySelectorAll('.modal-body button[data-status], .modal-body button[data-order-type], .modal-body button[data-payment-type]').forEach(button => {
                button.addEventListener('click', function () {
                    // Находим все кнопки в той же группе
                    const group = this.closest('.btn-group, .btn-group-vertical');
                    if (group) {
                        group.querySelectorAll('button').forEach(btn => btn.classList.remove('active'));
                    }
                    this.classList.add('active');
                });
            });

            // Установка остальных значений
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
