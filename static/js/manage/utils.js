// utils.js

export const REFRESH_INTERVAL = 10000;

export function fetchOrders(callback) {
    fetch('/api/get/orders/')
        .then(async response => {
            const data = await response.json();

            if (data.messages) {
                MessageManager.handleAjaxMessages(data.messages);
            }

            if (data.orders) {
                callback(data.orders);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            MessageManager.handleAjaxMessages([{level: 'error', message: 'No connection.'}]);
        });
}


export function createOrderElement(order, colClass = 'col-12') {
    const orderElement = document.createElement('div');
    orderElement.classList.add(colClass, 'mb-3');

    // Определяем класс и текст для статуса оплаты
    let paymentStatus, paymentClass;
    if (order.is_paid && order.paid_at) {
        paymentStatus = 'Paid';
        paymentClass = 'text-success';
    } else if (!order.is_paid && order.paid_at) {
        paymentStatus = 'Was Paid';
        paymentClass = 'text-danger';
    } else {
        paymentStatus = 'Not Paid';
        paymentClass = 'text-danger';
    }

    orderElement.innerHTML = `
        <div class="card order-card" data-status="${order.order_status}" data-bs-toggle="modal" data-bs-target="#orderModal" data-order-id="${order.id}">
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <h5 class="card-title mb-0">Order #${order.id}</h5>
                    <p class="card-text mb-0"><span class="badge bg-${getStatusColor(order.order_status)}">${order.order_status}</span></p>
                </div>
                <div class="d-flex justify-content-between align-items-center mb-3">
                    <p class="card-text mb-0">${order.user_role} (${order.user_nickname})</p>
                    ${order.is_refunded ? '<span class="badge bg-danger">Refunded</span>' : ''}
                </div>
        
                <table class="table table-borderless text-center mb-3">
                    <tbody>
                        <tr>
                            <td>Order Type</td>
                            <td>Payment Type</td>
                            <td>Price</td>
                        </tr>
                        <tr>
                            <td>${order.order_type}</td>
                            <td>${order.payment_type}</td>
                            <td>${order.total_price} IDR</td>
                        </tr>
                    </tbody>
                </table>
                
                ${order.public_note ? `
                    <div class="public-note-truncate mb-3">
                        ${order.public_note}
                    </div>
                ` : ''}

                <div class="d-flex justify-content-between mt-2">
                    <div class="order-dates">
                        <div>Created</div>
                        <div class="text-muted">
                            ${getUserRole() === 'manager' ? formatTime(order.created_at) : formatDate(order.created_at)}
                        </div>
                    </div>
                    <div class="order-dates text-end">
                        <div class="${paymentClass}"><b>${paymentStatus}</b></div>
                        <div class="text-muted">
                            ${order.paid_at ? (getUserRole() === 'manager' ? formatTime(order.paid_at) : formatDate(order.paid_at)) : ''}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    return orderElement;
}

function getStatusColor(status) {
    const statusColors = {
        'pending': 'secondary', 'cooking': 'info', 'ready': 'primary', 'finished': 'success', 'cancelled': 'danger', 'problem': 'danger'
    };
    return statusColors[status] || 'secondary';
}

export function formatDate(dateString) {
    if (!dateString) return '';
    return new Date(dateString).toLocaleString();
}

export function formatTime(dateString) {
    if (!dateString) return '';
    return new Date(dateString).toLocaleTimeString();
}

export function displayOrderDetails(orderId) {
    fetch(`/api/get/order/${orderId}/`)
        .then(async response => {
            const data = await response.json()

            if (data.messages) {
                MessageManager.handleAjaxMessages(data.messages)
            }

            if (!response.ok) {
                throw new Error()
            }

            const order = data.order

            // Устанавливаем ID заказа в заголовке модального окна
            document.getElementById('modalOrderId').textContent = order.id;
            document.getElementById('modalTableId').textContent = `${order.user_role} (${order.user_nickname})`;

            // Отображение публичной заметки
            const publicNoteDisplay = document.getElementById('publicNoteDisplay');
            if (order.public_note) {
                publicNoteDisplay.textContent = `Customer Note: ${order.public_note}`;
                publicNoteDisplay.parentElement.style.display = 'block';
            } else {
                publicNoteDisplay.parentElement.style.display = 'none';
            }

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
        });
}

export function handleStatusButtonClick(event) {
    const statusButtons = document.querySelectorAll('.status-buttons-container button[data-status]');
    statusButtons.forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
}

export function handleOrderTypeButtonClick(event) {
    const orderTypeButtons = document.querySelectorAll('button[data-order-type]');
    orderTypeButtons.forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
}

export function handlePaymentTypeButtonClick(event) {
    const paymentTypeButtons = document.querySelectorAll('button[data-payment-type]');
    paymentTypeButtons.forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
}

export function updateOrderStatus() {
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
        method: 'PUT', headers: {
            'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken')
        }, body: JSON.stringify(data)
    })
        .then(async response => {
            const data = await response.json()

            if (data.messages) {
                MessageManager.handleAjaxMessages(data.messages)
            }

            if (!response.ok) {
                return response.json().then(errorData => {
                    throw new Error(errorData.detail || 'Unknown error');
                });
            }
            return data;
        })
        .then(data => {
            // Закрываем модальное окно
            const modal = bootstrap.Modal.getInstance(document.getElementById('orderModal'));
            modal.hide();

            // Обновляем список заказов на текущей странице
            if (window.location.pathname.includes('control')) {
                import('./orders_control.js').then(module => module.loadControlOrders());
            } else {
                import('./orders_all.js').then(module => module.loadAllOrders());
            }
        })
        .catch(error => {
            MessageManager.handleAjaxMessages([{level: 'error', message: 'No connection.'}]);
            console.error('Error:', error);
        });
}

export function getCookie(name) {
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

export function getUserRole() {
    return window.currentUserRole || null;
}