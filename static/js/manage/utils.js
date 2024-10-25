// utils.js

export const REFRESH_INTERVAL = 10000;

export function fetchOrders(callback) {
    fetch('/api/get/orders/')
        .then(response => response.json())
        .then(data => {
            callback(data);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error fetching orders');
        });
}


export function createOrderElement(order, colClass = 'col-12') {
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

export function formatDate(dateString) {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
}

export function displayOrderDetails(orderId) {
    fetch(`/api/get/order/${orderId}/`)
        .then(response => response.json())
        .then(order => {
            // Устанавливаем ID заказа в заголовке модального окна
            document.getElementById('modalOrderId').textContent = order.id;
            document.getElementById('modalTableId').textContent = order.user_role + " " + order.user_id;

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
            alert(error.message);
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

            // Обновляем список заказов на текущей странице
            if (window.location.pathname.includes('control')) {
                import('./orders_control.js').then(module => module.loadControlOrders());
            } else {
                import('./orders_all.js').then(module => module.loadAllOrders());
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert(error.message);
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

export function refreshOrders() {
    if (document.getElementById('splitView')) {
        // for control
        import('./orders_control.js').then(module => module.loadControlOrders());
    } else {
        // for all
        import('./orders_all.js').then(module => module.loadAllOrders());
    }
}