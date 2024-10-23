// order_management.js

import * as utils from "../utils.js"

document.addEventListener('DOMContentLoaded', function () {
    utils.updateOrderSummary(false)
    fetchOrders();

    // Event listeners for search, filters, and sorting
    document.getElementById('searchInput').addEventListener('input', filterOrders);
    document.getElementById('tableIdFilter').addEventListener('input', filterOrders);
    document.getElementById('statusFilter').addEventListener('change', filterOrders);
    document.getElementById('paymentTypeFilter').addEventListener('change', filterOrders);
    document.getElementById('orderTypeFilter').addEventListener('change', filterOrders);
    document.getElementById('isPaidFilter').addEventListener('change', filterOrders);
    document.getElementById('isRefundedFilter').addEventListener('change', filterOrders);
    document.getElementById('sortBy').addEventListener('change', sortOrders);
    document.getElementById('clearFilters').addEventListener('click', clearFilters);

    // Event listener for updating order status
    document.getElementById('updateOrderBtn').addEventListener('click', updateOrderStatus);
    document.getElementById('toggleView').addEventListener('click', toggleView);
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
        <div class="card order-card" data-status="${order.order_status}" data-bs-toggle="modal" data-bs-target="#orderModal" data-order-id="${order.id}">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center">
                    <h5 class="card-title">Order #${order.id}</h5>
                    ${order.is_refunded ? '<span class="badge bg-danger">Refunded</span>' : ''}
                </div>
                <p class="card-text">${order.user_role} ${order.user_id}</p>
                <p class="card-text"><span class="badge bg-${getStatusColor(order.order_status)}">${order.order_status}</span></p>
                <p class="card-text">Type: ${order.order_type}</p>
                <p class="card-text">Payment: ${order.payment_type}</p>
                <p class="card-text">Total: ${order.total_price} IDR</p>
                <p class="card-text">Created: ${formatDate(order.created_at)}</p>
                <p class="card-text ${order.is_paid ? 'text-success' : 'text-danger'}">
                    ${order.paid_at ? `Paid: ${formatDate(order.paid_at)}` : 'Not Paid'}
                </p>
            </div>
        </div>
    `;
    return orderElement;
}

function formatDate(dateString) {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
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
                const matchesTableId = tableIdFilter === '' || order.user_id === parseInt(tableIdFilter);
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

function getStatusColor(status) {
    const statusColors = {
        'pending': 'secondary',
        'cooking': 'primary',
        'ready': 'info',
        'finished': 'success',
        'cancelled': 'danger',
        'problem': 'danger'
    };
    return statusColors[status] || 'secondary';
}

function sortOrders() {
    const sortBy = document.getElementById('sortBy').value;

    fetch('/api/get/orders/')
        .then(response => response.json())
        .then(data => {
            const sortedOrders = [...data].sort((a, b) => {
                if (sortBy === 'created_at_asc') {
                    return new Date(a.created_at) - new Date(b.created_at);
                } else {
                    return new Date(b.created_at) - new Date(a.created_at);
                }
            });
            displayAllOrders(sortedOrders);
        })
        .catch(error => {
            console.error('Error:', error);
            alert(error.message);
        });
}

function displayOrderDetails(orderId) {
    fetch(`/api/get/order/${orderId}/`)
        .then(response => response.json())
        .then(order => {
            // Устанавливаем ID заказа в заголовке модального окна
            document.getElementById('modalOrderId').textContent = order.id;
            document.getElementById('modalTableId').textContent = order.user_role + " " + order.user_id;

            // Отображаем детали заказа
            const orderDetailsContainer = document.getElementById('orderDetails');
            orderDetailsContainer.innerHTML = `
                <table class="table">
                    <thead>
                        <tr>
                            <th>Name</th>
                            <th class="text-center">Amount</th>
                            <th class="text-center">Price</th>
                            <th class="text-center">Total</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${order.products.map(product => `
                            <tr>
                                <td>${product.name}<br>
                                    <small>${product.ingredients.map(ing => `${ing.name} (${ing.weight_grams}g)`).join(', ')}</small>
                                </td>
                                <td class="text-center">${product.amount}</td>
                                <td class="text-center">${product.price}</td>
                                <td class="text-center">${product.price * product.amount}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                    <tfoot>
                        <tr>
                            <td colspan="3" class="text-end"><strong>Total:</strong></td>
                            <td class="text-center"><strong>${order.total_price}</strong></td>
                        </tr>
                    </tfoot>
                </table>
            `;

            // Установка значений в форме
            document.getElementById('paymentId').value = order.payment_id || '';
            document.getElementById('isPaid').checked = order.is_paid;
            document.getElementById('isRefunded').checked = order.is_refunded;
            document.getElementById('privateNote').value = order.private_note || '';

            // Обработка статуса заказа
            const statusButtons = document.querySelectorAll('.status-buttons-container button[data-status]');
            statusButtons.forEach(button => {
                button.classList.remove('active');
                if (button.getAttribute('data-status') === order.order_status) {
                    button.classList.add('active');
                }
            });

            // Добавляем обработчики для кнопок статуса
            statusButtons.forEach(button => {
                button.removeEventListener('click', handleStatusButtonClick);
                button.addEventListener('click', handleStatusButtonClick);
            });

            // Обработка типа заказа
            const orderTypeButtons = document.querySelectorAll('button[data-order-type]');
            orderTypeButtons.forEach(button => {
                button.classList.remove('active');
                if (button.getAttribute('data-order-type') === order.order_type) {
                    button.classList.add('active');
                }
                // Добавляем обработчик событий для каждой кнопки
                button.removeEventListener('click', handleOrderTypeButtonClick);
                button.addEventListener('click', handleOrderTypeButtonClick);
            });

            // Обработка типа оплаты
            const paymentTypeButtons = document.querySelectorAll('button[data-payment-type]');
            paymentTypeButtons.forEach(button => {
                button.classList.remove('active');
                if (button.getAttribute('data-payment-type') === order.payment_type) {
                    button.classList.add('active');
                }
                // Добавляем обработчик событий для каждой кнопки
                button.removeEventListener('click', handlePaymentTypeButtonClick);
                button.addEventListener('click', handlePaymentTypeButtonClick);
            });

            // Установка ID заказа в модальном окне
            document.getElementById('orderModal').setAttribute('data-order-id', orderId);
        })
        .catch(error => {
            console.error('Error:', error);
            alert(error.message);
        });
}

function handleStatusButtonClick(event) {
    const statusButtons = document.querySelectorAll('.status-buttons-container button[data-status]');
    statusButtons.forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
}

function handleOrderTypeButtonClick(event) {
    const orderTypeButtons = document.querySelectorAll('button[data-order-type]');
    orderTypeButtons.forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
}

function handlePaymentTypeButtonClick(event) {
    const paymentTypeButtons = document.querySelectorAll('button[data-payment-type]');
    paymentTypeButtons.forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
}

function updateOrderStatus() {
    const orderId = document.getElementById('orderModal').getAttribute('data-order-id');
    const activeStatusButton = document.querySelector('.status-buttons-container button.active');
    const activeOrderTypeButton = document.querySelector('button[data-order-type].active');
    const activePaymentTypeButton = document.querySelector('button[data-payment-type].active');

    const data = {
        order_status: activeStatusButton ? activeStatusButton.getAttribute('data-status') : null,
        order_type: activeOrderTypeButton ? activeOrderTypeButton.getAttribute('data-order-type') : null,
        payment_type: activePaymentTypeButton ? activePaymentTypeButton.getAttribute('data-payment-type') : null,
        payment_id: document.getElementById('paymentId').value,
        is_paid: document.getElementById('isPaid').checked,
        is_refunded: document.getElementById('isRefunded').checked,
        private_note: document.getElementById('privateNote').value
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
                    throw new Error(errorData.detail || 'Unknown error');
                });
            }
            return response.json();
        })
        .then(data => {
            // Закрываем модальное окно
            const modal = bootstrap.Modal.getInstance(document.getElementById('orderModal'));
            modal.hide();
            // Обновляем список заказов
            fetchOrders();
        })
        .catch(error => {
            console.error('Error:', error);
            alert(error.message);
        });
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

function clearFilters() {
    // Очистка текстовых полей
    document.getElementById('searchInput').value = '';
    document.getElementById('tableIdFilter').value = '';

    // Сброс select элементов
    document.getElementById('statusFilter').value = '';
    document.getElementById('orderTypeFilter').value = '';
    document.getElementById('paymentTypeFilter').value = '';
    document.getElementById('sortBy').value = '';

    // Сброс чекбоксов
    document.getElementById('isPaidFilter').checked = false;
    document.getElementById('isRefundedFilter').checked = false;

    // Сброс даты
    if (document.getElementById('createdAtFilter')) {
        document.getElementById('createdAtFilter').value = '';
    }

    // После очистки фильтров, обновляем отображение заказов
    fetchOrders();
}

// Добавляем обработчик кликов по карточкам заказов
document.addEventListener('click', function (event) {
    if (event.target.closest('.order-card')) {
        const orderId = event.target.closest('.order-card').getAttribute('data-order-id');
        displayOrderDetails(orderId);
    }
});