// purchase.js

import {getCookie} from './utils.js';

let purchases = [];

document.addEventListener('DOMContentLoaded', function () {
    loadPurchases();
    setupEventListeners();
});

function setupEventListeners() {
    // Search inputs
    document.getElementById('search-id').addEventListener('input', filterPurchases);
    document.getElementById('search-bought').addEventListener('input', filterPurchases);
    document.getElementById('search-note').addEventListener('input', filterPurchases);

    // Date search
    document.getElementById('date-search-from').addEventListener('change', filterPurchases);
    document.getElementById('date-search-to').addEventListener('change', filterPurchases);

    // Clear search
    document.getElementById('clear-search').addEventListener('click', clearSearch);

    // Add purchase button
    document.getElementById('add-purchase').addEventListener('click', () => showPurchaseModal());

    // Form submit
    document.getElementById('purchase-form').addEventListener('submit', handleFormSubmit);

    // Modal click outside
    document.addEventListener('click', function (e) {
        const modal = document.getElementById('purchaseModal');
        if (e.target === modal) {
            closeModal();
        }
    });
}

async function loadPurchases() {
    try {
        const response = await fetch('/api/control/get/purchases/');
        const data = await response.json();

        purchases = data.purchases || [];
        displayPurchases(purchases);
    } catch (error) {
        console.error('Error loading purchases:', error);
    }
}

function displayPurchases(purchasesToShow) {
    const container = document.getElementById('purchases-container');
    container.innerHTML = '';

    purchasesToShow.forEach(purchase => {
        const card = createPurchaseCard(purchase);
        container.appendChild(card);
    });
}

function createPurchaseCard(purchase) {
    const card = document.createElement('div');
    card.className = 'purchase-card';

    card.innerHTML = `
        <div class="purchase-header">
            <span class="purchase-id">#${purchase.id}</span>
            <span class="purchase-paid">${purchase.paid} IDR</span>
        </div>
        <div class="purchase-date">
            ${new Date(purchase.created_at).toLocaleDateString()}
        </div>
        <div class="purchase-creator">
            Created by: ${purchase.creator?.username || 'Unknown'}
        </div>
    `;

    card.addEventListener('click', () => showPurchaseModal(purchase));
    return card;
}


function filterPurchases() {
    const idSearch = document.getElementById('search-id').value.toLowerCase();
    const boughtSearch = document.getElementById('search-bought').value.toLowerCase();
    const noteSearch = document.getElementById('search-note').value.toLowerCase();
    const dateFrom = document.getElementById('date-search-from').value;
    const dateTo = document.getElementById('date-search-to').value;

    let filtered = purchases.filter(purchase => {
        const matchId = purchase.id.toString().includes(idSearch);
        const matchBought = purchase.what_bought?.toLowerCase().includes(boughtSearch);
        const matchNote = purchase.admin_note?.toLowerCase().includes(noteSearch);

        // Проверка даты
        let matchDate = true;
        const purchaseDate = new Date(purchase.created_at);

        if (dateFrom) {
            const fromDate = new Date(dateFrom);
            matchDate = matchDate && purchaseDate >= fromDate;
        }

        if (dateTo) {
            const toDate = new Date(dateTo);
            // Добавляем один день к конечной дате, чтобы включить весь последний день
            toDate.setDate(toDate.getDate() + 1);
            matchDate = matchDate && purchaseDate < toDate;
        }

        return matchId && matchBought && matchNote && matchDate;
    });

    displayPurchases(filtered);
}

function clearSearch() {
    document.getElementById('search-id').value = '';
    document.getElementById('search-bought').value = '';
    document.getElementById('search-note').value = '';
    document.getElementById('date-search-from').value = '';
    document.getElementById('date-search-to').value = '';
    displayPurchases(purchases);
}

function showPurchaseModal(purchase = null) {
    const modal = document.getElementById('purchaseModal');
    const form = document.getElementById('purchase-form');

    if (purchase) {
        form.dataset.purchaseId = purchase.id;
        document.getElementById('paid').value = purchase.paid;
        document.getElementById('what-bought').value = purchase.what_bought || '';
        document.getElementById('admin-note').value = purchase.admin_note || '';
        document.getElementById('creator').value = purchase.creator?.username || 'Unknown'; // Добавлено поле создателя
    } else {
        form.dataset.purchaseId = '';
        form.reset();
        document.getElementById('creator').value = ''; // Очистка поля создателя для новой записи
    }

    modal.style.display = 'block';
}

function closeModal() {
    const modal = document.getElementById('purchaseModal');
    modal.style.display = 'none';
}

async function handleFormSubmit(e) {
    e.preventDefault();

    const form = e.target;
    const purchaseId = form.dataset.purchaseId;
    const isNew = !purchaseId;

    const purchaseData = {
        paid: parseInt(document.getElementById('paid').value),
        what_bought: document.getElementById('what-bought').value,
        admin_note: document.getElementById('admin-note').value
    };

    try {
        const url = isNew
            ? '/api/control/create/purchase/'
            : `/api/control/update/purchase/${purchaseId}/`;

        const response = await fetch(url, {
            method: isNew ? 'POST' : 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(purchaseData)
        });

        const data = await response.json();

        if (response.ok) {
            await loadPurchases();
            closeModal();
        }
    } catch (error) {
        console.error('Error saving purchase:', error);
    }
}