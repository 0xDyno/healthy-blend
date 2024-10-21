// orders.js

document.addEventListener('DOMContentLoaded', function () {
    const userRole = '{{ user.role }}';
    const ordersContainer = document.getElementById('ordersContainer');

    // Function to fetch orders
    async function fetchOrders() {
        try {
            const response = await fetch('/api/orders/all_orders/');
            if (!response.ok) {
                throw new Error('Failed to fetch orders');
            }
            return await response.json();
        } catch (error) {
            console.error('Error:', error);
            return [];
        }
    }

    // Function to render orders for table view
    function renderTableOrders(orders) {
        const tableOrdersContainer = document.getElementById('tableOrders');
        tableOrdersContainer.innerHTML = '';

        orders.forEach(order => {
            const orderElement = document.createElement('div');
            orderElement.classList.add('order-block');
            orderElement.innerHTML = `
                <h4>Order #${order.id}</h4>
                <p>Status: ${order.order_status}</p>
                <p>Paid at: ${new Date(order.paid_at).toLocaleString()}</p>
                <p>Products: ${order.products.map(p => `${p.product_name} (x${p.quantity})`).join(', ')}</p>
            `;
            orderElement.addEventListener('click', () => {
                window.location.href = `/orders/${order.id}/`;
            });
            tableOrdersContainer.appendChild(orderElement);
        });
    }

    // Function to render orders for admin/manager view
    function renderAdminOrders(orders) {
        const pendingOrdersContainer = document.getElementById('pendingOrders');
        const readyOrdersContainer = document.getElementById('readyOrders');
        const allOrdersContainer = document.getElementById('allOrders');

        pendingOrdersContainer.innerHTML = '<h3>Pending Orders</h3>';
        readyOrdersContainer.innerHTML = '<h3>Ready Orders</h3>';
        allOrdersContainer.innerHTML = '';

        orders.forEach(order => {
            const orderElement = createOrderElement(order);

            if (order.order_status === 'pending') {
                pendingOrdersContainer.appendChild(orderElement.cloneNode(true));
            } else if (order.order_status === 'ready') {
                readyOrdersContainer.appendChild(orderElement.cloneNode(true));
            }

            allOrdersContainer.appendChild(orderElement);
        });
    }

    // Function to create an order element
    function createOrderElement(order) {
        const orderElement = document.createElement('div');
        orderElement.classList.add('order-block');
        orderElement.innerHTML = `
            <h4>Order #${order.id}</h4>
            <p>Table: ${order.table_id}</p>
            <p>Status: ${order.order_status}</p>
            <p>Type: ${order.order_type}</p>
            <p>Payment: ${order.payment_type}</p>
            <p>Total: ${order.total_price} IDR</p>
            <p>Created: ${new Date(order.created_at).toLocaleString()}</p>
            <p>Paid: ${order.paid_at ? new Date(order.paid_at).toLocaleString() : 'Not paid'}</p>
        `;
        orderElement.addEventListener('click', () => {
            window.location.href = `/orders/${order.id}/`;
        });
        return orderElement;
    }

    // Main function to initialize the page
    async function initOrdersPage() {
        const orders = await fetchOrders();

        if (userRole === 'table') {
            renderTableOrders(orders);
        } else {
            renderAdminOrders(orders);

            // Set up event listeners for admin/manager view
            document.getElementById('splitViewBtn').addEventListener('click', () => {
                document.getElementById('splitView').style.display = 'flex';
                document.getElementById('fullView').style.display = 'none';
            });

            document.getElementById('fullViewBtn').addEventListener('click', () => {
                document.getElementById('splitView').style.display = 'none';
                document.getElementById('fullView').style.display = 'block';
            });

            document.getElementById('statusFilter').addEventListener('change', filterOrders);
            document.getElementById('sortBy').addEventListener('change', sortOrders);
        }
    }

    // Function to filter orders
    function filterOrders() {
        const status = document.getElementById('statusFilter').value;
        const orderElements = document.querySelectorAll('#allOrders .order-block');

        orderElements.forEach(el => {
            const orderStatus = el.querySelector('p:nth-child(3)').textContent.split(': ')[1];
            el.style.display = status === '' || orderStatus === status ? 'block' : 'none';
        });
    }

    // Function to sort orders
    function sortOrders() {
        const sortBy = document.getElementById('sortBy').value;
        const orderElements = Array.from(document.querySelectorAll('#allOrders .order-block'));

        orderElements.sort((a, b) => {
            const dateA = new Date(a.querySelector(`p:nth-child(${sortBy === 'created_at' ? 7 : 8})`).textContent.split(': ')[1]);
            const dateB = new Date(b.querySelector(`p:nth-child(${sortBy === 'created_at' ? 7 : 8})`).textContent.split(': ')[1]);
            return dateB - dateA;
        });

        const allOrdersContainer = document.getElementById('allOrders');
        allOrdersContainer.innerHTML = '';
        orderElements.forEach(el => allOrdersContainer.appendChild(el));
    }

    initOrdersPage();
});