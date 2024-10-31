// promo.js

import {getCookie} from "./utils.js";

let data = [];
let activeFilters = {
    enabled: false,
    active: false,
    finished: false,
};

document.addEventListener('DOMContentLoaded', function () {
    initializeFeatures();
});

function initializeFeatures() {
    loadPromos();

    // Search input handler
    document.getElementById('searchInput').addEventListener('input', filterPromos);

    // Status filter buttons
    const filterButtons = document.querySelectorAll('.filter-btn');
    filterButtons.forEach(button => {
        button.addEventListener('click', toggleFilter);
    });

    // Create button handler
    const createBtn = document.getElementById('createPromoBtn');
    if (createBtn) {
        createBtn.addEventListener('click', () => showPromoModal(null));
    }

    // Form submit handler
    const form = document.getElementById('promoForm');
    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }
}

function toggleFilter(e) {
    const button = e.target;
    const filterType = button.dataset.filter;

    // Toggle filter state
    activeFilters[filterType] = !activeFilters[filterType];

    // Toggle visual state
    button.classList.toggle('active');

    filterPromos();
}

async function loadPromos() {
    try {
        const response = await fetch('/api/control/get/promos/');
        const responseData = await response.json();

        if (responseData.messages) {
            MessageManager.handleAjaxMessages(responseData.messages);
        }

        data = responseData.promos || [];
        displayPromos(data);
    } catch (error) {
        console.error('Error loading promos:', error);
    }
}

async function loadPromoDetails(promoId) {
    try {
        const response = await fetch(`/api/control/get/promo/${promoId}/`);
        const data = await response.json();

        if (data.messages) {
            MessageManager.handleAjaxMessages(data.messages);
        }

        return data.promo;
    } catch (error) {
        console.error('Error loading promo details:', error);
        return null;
    }
}

function filterPromos() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();

    let filteredPromos = data.filter(promo => {
        const searchMatch = promo.id.toString().includes(searchTerm) ||
            promo.promo_code.toLowerCase().includes(searchTerm);

        const enabledMatch = !activeFilters.enabled || promo.is_enabled;
        const activeMatch = !activeFilters.active || promo.is_active;
        const finishedMatch = !activeFilters.finished || promo.is_finished;

        return searchMatch && enabledMatch && activeMatch && finishedMatch;
    });

    displayPromos(filteredPromos);
}

function displayPromos(promos) {
    const grid = document.getElementById('promosGrid');
    grid.innerHTML = '';

    promos.forEach(promo => {
        const card = createPromoCard(promo);
        grid.appendChild(card);
    });
}

function createPromoCard(promo) {
    const card = document.createElement('div');
    card.className = 'promo-card';

    card.innerHTML = `
        <div class="promo-header">
            <div class="promo-title">
                <span class="promo-id">#${promo.id}</span>
                <span class="promo-code">${promo.promo_code}</span>
            </div>
            <div class="promo-discount">${(promo.discount * 100).toFixed(1)}%</div>
        </div>
        <div class="status-container">
            <span class="status-badge ${promo.is_enabled ? 'status-enabled' : 'status-disabled'}">
                ${promo.is_enabled ? 'Enabled' : 'Disabled'}
            </span>
            <span class="status-badge ${promo.is_active ? 'status-active' : 'status-not-active'}">
                ${promo.is_active ? 'Active' : 'Not Active'}
            </span>
            <span class="status-badge ${promo.is_finished ? 'status-finished' : 'status-not-finished'}">
                ${promo.is_finished ? 'Finished' : 'Not Finished'}
            </span>
        </div>
        <div class="promo-usage">
            ${promo.used_count} of ${promo.usage_limit}
        </div>
        <div class="promo-dates">
            <table class="dates-table">
                <tr>
                    <th>Starts</th>
                    <th>Ends</th>
                </tr>
                <tr>
                    <td>${new Date(promo.active_from).toLocaleDateString()}</td>
                    <td>${new Date(promo.active_until).toLocaleDateString()}</td>
                </tr>
                <tr>
                    <td>${new Date(promo.active_from).toLocaleTimeString()}</td>
                    <td>${new Date(promo.active_until).toLocaleTimeString()}</td>
                </tr>
            </table>
        </div>
        <div class="promo-creator">
            <small>${promo.creator}</small>
        </div>
    `;

    card.addEventListener('click', () => showPromoModal(promo));
    return card;
}

async function showPromoModal(promo) {
    const modal = new bootstrap.Modal(document.getElementById('promoModal'));
    const isNew = !promo;

    // Reset form
    document.getElementById('promoForm').reset();

    // Hide additional info section for new promos
    document.getElementById('additionalInfo').style.display = isNew ? 'none' : 'block';

    if (isNew) {
        setupModalForNewPromo();
        modal.show();
        return;
    }

    // Show loader
    document.getElementById('modalContent').style.display = 'none';
    document.getElementById('modalLoader').style.display = 'block';
    modal.show();

    // Load detailed info
    const promoDetails = await loadPromoDetails(promo.id);

    if (!promoDetails) {
        modal.hide();
        return;
    }

    // Hide loader and show content
    document.getElementById('modalLoader').style.display = 'none';
    document.getElementById('modalContent').style.display = 'block';

    setupModalForExistingPromo(promoDetails);
}

function setupModalForNewPromo() {
    document.getElementById('promoTitle').textContent = 'Create New Promo';
    document.getElementById('promoId').textContent = '';
    document.getElementById('submitButton').textContent = 'Create';
    document.getElementById('modalActiveStatus').style.display = 'none';

    setupStatusButtons({ is_enabled: true });

    // Set default dates
    const now = new Date();
    const tomorrow = new Date(now);
    tomorrow.setDate(tomorrow.getDate() + 1);

    document.getElementById('modalActiveFrom').value = now.toISOString().slice(0, 16);
    document.getElementById('modalActiveUntil').value = tomorrow.toISOString().slice(0, 16);
}

function setupModalForExistingPromo(promo) {
    document.getElementById('promoTitle').textContent = 'Edit Promo';
    document.getElementById('promoId').textContent = `#${promo.id}`;
    document.getElementById('submitButton').textContent = 'Update';

    // Set form values
    document.getElementById('modalPromoCode').value = promo.promo_code;
    document.getElementById('modalDiscount').value = promo.discount * 100;
    document.getElementById('modalUsageLimit').value = promo.usage_limit;
    document.getElementById('modalUsedCount').value = promo.used_count;
    document.getElementById('modalActiveFrom').value = new Date(promo.active_from).toISOString().slice(0, 16);
    document.getElementById('modalActiveUntil').value = new Date(promo.active_until).toISOString().slice(0, 16);
    document.getElementById('modalCreator').value = promo.creator;

    // Setup enabled checkbox and active status
    setupStatusButtons(promo);
    setupFinishedButton(promo);

    const statusBadge = document.getElementById('modalActiveStatus');
    statusBadge.style.display = 'inline';
    if (promo.is_active) {
        statusBadge.textContent = 'Active';
        statusBadge.className = 'badge bg-success';
    } else {
        statusBadge.textContent = 'Not Active';
        statusBadge.className = 'badge bg-secondary';
    }

    // Setup additional info
    if (promo.discounted_total) {
        document.getElementById('modalDiscountedTotal').value = promo.discounted_total;
    }

    // Clear and setup usage history
    const historyTable = document.getElementById('usageHistoryTable');
    historyTable.innerHTML = ''; // Clear existing history

    // Setup usage history
    if (promo.usage_history && promo.usage_history.length > 0) {
        historyTable.innerHTML = promo.usage_history.map(entry => `
            <tr>
                <td>${entry.user_role}</td>
                <td>${entry.user_nickname}</td>
                <td>${entry.order_id}</td>
                <td>${entry.order_base_price}</td>
                <td>${entry.discounted}</td>
                <td>${new Date(entry.used_at).toLocaleString()}</td>
            </tr>
        `).join('');
    }

    // Set form dataset for update
    document.getElementById('promoForm').dataset.promoId = promo.id;
}

function setupStatusButtons(promo) {
    const button = document.getElementById('isEnabledBtn');
    const checkbox = document.getElementById('modalIsEnabled');

    // Установка начального состояния
    const isEnabled = promo?.is_enabled || false;

    // Обновление состояния кнопки и скрытого чекбокса
    if (isEnabled) {
        button.classList.add('active');
        checkbox.checked = true;
    } else {
        button.classList.remove('active');
        checkbox.checked = false;
    }

    // Удаление старого обработчика событий (если есть)
    button.removeEventListener('click', handleStatusButtonClick);

    // Добавление нового обработчика событий
    button.addEventListener('click', handleStatusButtonClick);
}

function handleStatusButtonClick(e) {
    const button = e.currentTarget;
    const checkbox = document.getElementById('modalIsEnabled');

    // Переключение состояния
    const newState = !checkbox.checked;
    checkbox.checked = newState;

    // Обновление внешнего вида кнопки
    if (newState) {
        button.classList.add('active');
    } else {
        button.classList.remove('active');
    }
}

function setupFinishedButton(promo) {
    const button = document.getElementById('isFinishedBtn');
    const checkbox = document.getElementById('modalIsFinished');

    // Установка начального состояния
    const isFinished = promo?.is_finished || false;

    // Обновление состояния кнопки и скрытого чекбокса
    if (isFinished) {
        button.classList.add('active');
        checkbox.checked = true;
    } else {
        button.classList.remove('active');
        checkbox.checked = false;
    }

    // Удаление старого обработчика событий (если есть)
    button.removeEventListener('click', handleFinishedButtonClick);

    // Добавление нового обработчика событий
    button.addEventListener('click', handleFinishedButtonClick);
}

function handleFinishedButtonClick(e) {
    const button = e.currentTarget;
    const checkbox = document.getElementById('modalIsFinished');

    // Переключение состояния
    const newState = !checkbox.checked;
    checkbox.checked = newState;

    // Обновление внешнего вида кнопки
    if (newState) {
        button.classList.add('active');
    } else {
        button.classList.remove('active');
    }
}

async function handleFormSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const promoId = form.dataset.promoId;
    const isNew = !promoId;

    const promoData = {
        promo_code: document.getElementById('modalPromoCode').value,
        discount: parseFloat(document.getElementById('modalDiscount').value) / 100,
        usage_limit: parseInt(document.getElementById('modalUsageLimit').value),
        active_from: document.getElementById('modalActiveFrom').value,
        active_until: document.getElementById('modalActiveUntil').value,
        is_enabled: document.getElementById('modalIsEnabled').checked,
        is_finished: document.getElementById('modalIsFinished').checked,
    };

    try {
        const url = isNew ? '/api/control/create/promo/' : `/api/control/update/promo/${promoId}/`;
        const method = isNew ? 'POST' : 'PUT';

        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(promoData)
        });

        const data = await response.json();

        if (data.messages) {
            MessageManager.handleAjaxMessages(data.messages);
        }

        if (response.ok) {
            await loadPromos(); // Reload all promos
            bootstrap.Modal.getInstance(document.getElementById('promoModal')).hide();
        }
    } catch (error) {
        console.error('Error saving promo:', error);
    }
}

// Modal cleanup
document.getElementById('promoModal').addEventListener('hidden.bs.modal', function () {
    document.body.classList.remove('modal-open');
    const modalBackdrop = document.querySelector('.modal-backdrop');
    if (modalBackdrop) {
        modalBackdrop.remove();
    }

    const enabledButton = document.getElementById('isEnabledBtn');
    if (enabledButton) {
        enabledButton.removeEventListener('click', handleStatusButtonClick);
    }

    const finishedButton = document.getElementById('isFinishedBtn');
    if (finishedButton) {
        finishedButton.removeEventListener('click', handleFinishedButtonClick);
    }
});

// Validation functions
function validatePromoForm() {
    const promoCode = document.getElementById('modalPromoCode').value;
    const discount = parseFloat(document.getElementById('modalDiscount').value);
    const usageLimit = parseInt(document.getElementById('modalUsageLimit').value);
    const activeFrom = new Date(document.getElementById('modalActiveFrom').value);
    const activeUntil = new Date(document.getElementById('modalActiveUntil').value);

    // Basic validation
    if (!promoCode || promoCode.trim() === '') {
        MessageManager.showError('Promo code cannot be empty');
        return false;
    }

    if (isNaN(discount) || discount < 0 || discount > 50) {
        MessageManager.showError('Discount must be between 0 and 50');
        return false;
    }

    if (isNaN(usageLimit) || usageLimit < 0) {
        MessageManager.showError('Usage limit must be a positive number');
        return false;
    }

    if (activeFrom >= activeUntil) {
        MessageManager.showError('Active until date must be after active from date');
        return false;
    }

    return true;
}

// Utility functions
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

// Export if needed
export {
    loadPromos,
    showPromoModal,
    handleFormSubmit
};