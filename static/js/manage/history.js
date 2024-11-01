// history.js

let orders = [];

async function loadOrders() {
    try {
        const response = await fetch('/api/control/get/orders/history/');
        orders = await response.json();
        displayOrders(orders);
    } catch (error) {
        console.error('Error loading orders:', error);
    }
}

function displayOrders(ordersToShow) {
    const ordersList = document.getElementById('ordersList');
    ordersList.innerHTML = '';

    ordersToShow.forEach(order => {
        const orderElement = document.createElement('div');
        orderElement.className = 'col-md-4 mb-3';
        orderElement.innerHTML = `
            <div class="card" style="cursor: pointer" onclick="showOrderHistory(${order.id})">
                <div class="card-body">
                    <h5 class="card-title">Order #${order.id}</h5>
                    <p class="card-text">
                        Status: <span class="badge bg-${getStatusColor(order.order_status)}">${order.order_status}</span><br>
                        Created: ${new Date(order.created_at).toLocaleString()}
                    </p>
                </div>
            </div>
        `;
        ordersList.appendChild(orderElement);
    });
}

function getStatusColor(status) {
    const statusColors = {
        'pending': 'warning',
        'cooking': 'info',
        'ready': 'primary',
        'finished': 'success',
        'cancelled': 'danger',
        'problem': 'danger'
    };
    return statusColors[status] || 'secondary';
}

window.showOrderHistory = async function (orderId) {
    try {
        const response = await fetch(`/api/control/get/order/history/${orderId}/`);
        const history = await response.json();

        const historyContent = document.getElementById('historyContent');
        historyContent.innerHTML = '';

        history.forEach(record => {
            const historyElement = document.createElement('div');
            historyElement.className = 'card mb-3';
            historyElement.innerHTML = `
                <div class="card-body">
                    <h6 class="card-subtitle mb-2 text-muted">
                        ${new Date(record.created_at).toLocaleString()} - Updated by ${record.user_last_update_name}
                    </h6>
                    <div class="row">
                        <div class="col-md-6">
                            <div class="row">
                                <div class="col-6">Status:</div>
                                <div class="col-6">
                                    <span class="badge bg-${getStatusColor(record.order_status)}">${record.order_status}</span>
                                </div>
                            </div>
                            <div class="row">
                                <div class="col-6">Order Type:</div>
                                <div class="col-6">${record.order_type}</div>
                            </div>
                            <div class="row">
                                <div class="col-6">Payment Type:</div>
                                <div class="col-6">${record.payment_type}</div>
                            </div>
                            <div class="row">
                                <div class="col-6">Payment Status:</div>
                                <div class="col-6">${record.is_paid ? '<span class="badge bg-success">Paid</span>' : '<span class="badge bg-warning">Not Paid</span>'}
                                ${record.is_refunded ? '<span class="badge bg-danger">Refunded</span>' : ''}</div>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <table class="table table-borderless m-0">
                                <tr>
                                    <td>Base Price:</td>
                                    <td>${record.base_price}</td>
                                </tr>
                                <tr>
                                    <td>Tax (${record.tax}%):</td>
                                    <td>${(record.base_price * record.tax / 100).toFixed(2)}</td>
                                </tr>
                                <tr>
                                    <td>Service (${record.service}%):</td>
                                    <td>${(record.base_price * record.service / 100).toFixed(2)}</td>
                                </tr>
                                <tr>
                                    <td>Total Price:</td>
                                    <td>${record.total_price}</td>
                                </tr>
                            </table>
                        </div>
                    </div>
                    <div class="row">
                        <div class="col-12">
                            ${record.public_note ? `
                                <div class="mt-2">
                                    <strong>Public Note:</strong><br>
                                    <small>${record.public_note}</small>
                                </div>
                            ` : ''}
                            ${record.private_note ? `
                                <div class="mt-2">
                                    <strong>Private Note:</strong><br>
                                    <small>${record.private_note}</small>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `;
            historyContent.appendChild(historyElement);
        });

        const modal = new bootstrap.Modal(document.getElementById('historyModal'));
        modal.show();
    } catch (error) {
        console.error('Error loading order history:', error);
    }
}

function searchOrders() {
    const searchValue = document.getElementById('orderSearch').value.trim();
    if (searchValue === '') {
        displayOrders(orders);
        return;
    }

    const filteredOrders = orders.filter(order =>
        order.id.toString().includes(searchValue)
    );
    displayOrders(filteredOrders);
}

// Event Listeners
document.addEventListener('DOMContentLoaded', () => {
    loadOrders();

    document.getElementById('orderSearch').addEventListener('input', searchOrders);
});