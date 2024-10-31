// products.js

import {getCookie, getUserRole} from "./utils.js";

let productsData = [];
const isAdmin = getUserRole() === 'owner' || getUserRole() === 'administrator';

document.addEventListener('DOMContentLoaded', function () {
    initializeProducts();
});

function initializeProducts() {
    loadProducts();
    setupSearchAndFilters();
}

function setupSearchAndFilters() {
    // Search input handler
    document.getElementById('searchInput').addEventListener('input', filterProducts);

    // Type filter handler
    document.getElementById('typeFilter').addEventListener('change', filterProducts);

    // Filter buttons handler
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.target.classList.toggle('active');
            filterProducts();
        });
    });
}

async function loadProducts() {
    try {
        const response = await fetch('/api/control/get/products/');
        const data = await response.json();

        if (data.messages) {
            MessageManager.handleAjaxMessages(data.messages);
        }

        productsData = data.products || [];
        displayProducts(productsData);
    } catch (error) {
        console.error('Error loading products:', error);
    }
}

function filterProducts() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const selectedType = document.getElementById('typeFilter').value.toLowerCase();

    // Get active filters
    const activeFilters = Array.from(document.querySelectorAll('.filter-btn.active'))
        .map(btn => btn.dataset.filter);

    let filtered = productsData.filter(product => {
        // Search by name or ID
        const searchMatch = product.name.toLowerCase().includes(searchTerm) ||
            product.id.toString().includes(searchTerm);

        // Type filter
        const typeMatch = !selectedType || product.product_type.toLowerCase() === selectedType;

        // Status filters
        const filterMatch = activeFilters.every(filter => {
            switch (filter) {
                case 'available':
                    return product.is_available;
                case 'enabled':
                    return product.is_enabled;
                case 'official':
                    return product.is_official;
                case 'menu':
                    return product.is_menu;
                default:
                    return true;
            }
        });

        return searchMatch && typeMatch && filterMatch;
    });

    displayProducts(filtered);
}

function displayProducts(products) {
    const grid = document.getElementById('productsGrid');
    grid.innerHTML = '';

    products.forEach(product => {
        const card = createProductCard(product);
        grid.appendChild(card);
    });
}

function createProductCard(product) {
    const card = document.createElement('div');
    card.className = 'product-card';

    // Create badges HTML
    const badgesHtml = `
        <div class="product-badges">
            <span class="badge ${product.is_available ? 'badge-available' : 'badge-unavailable'}">
                ${product.is_available ? 'Available' : 'Unavailable'}
            </span>
            <span class="badge ${product.is_enabled ? 'badge-enabled' : 'badge-disabled'}">
                ${product.is_enabled ? 'Enabled' : 'Disabled'}
            </span>
        </div>
    `;

    // Create menu indicator
    const menuIndicator = product.is_menu ? '<div class="menu-indicator"></div>' : '';

    card.innerHTML = `
        <div class="product-image-container">
            <img src="${product.image}" alt="${product.name}" class="product-image">
            ${badgesHtml}
        </div>
        <div class="product-info">
            <div class="product-name-container">
                ${menuIndicator}
                <h3 class="product-name">${product.name}</h3>
            </div>
            <div class="product-details">
                <span class="product-type">${product.product_type}</span>
                ${product.selling_price ? `<span class="product-price">${product.selling_price}</span>` : ''}
            </div>
        </div>
    `;

    card.addEventListener('click', () => showProductModal(product.id));
    return card;
}

async function showProductModal(productId) {
    try {
        const response = await fetch(`/api/control/get/product/${productId}/`);
        const data = await response.json();

        if (data.messages) {
            MessageManager.handleAjaxMessages(data.messages);
        }

        const product = data.product;
        if (!product) return;

        populateModal(product);

        const modal = new bootstrap.Modal(document.getElementById('productModal'));
        modal.show();
    } catch (error) {
        console.error('Error loading product details:', error);
    }
}

function populateModal(product) {
    // Header information
    document.getElementById('modalProductName').textContent = product.name;
    document.getElementById('modalProductId').textContent = product.id;

    // First row
    document.getElementById('modalProductType').textContent = product.product_type;
    document.getElementById('modalSellingPrice').textContent =
        product.selling_price ? `${product.selling_price} IDR` : '';

    // Second row
    document.getElementById('modalProductImage').src = product.image;
    document.getElementById('modalIsMenu').innerHTML =
        `<span class="status-indicator ${product.is_menu ? 'active' : ''}"></span>`;
    document.getElementById('modalIsAvailable').innerHTML =
        `<span class="status-indicator ${product.is_available ? 'active' : ''}"></span>`;
    document.getElementById('modalIsEnabled').innerHTML =
        `<span class="status-indicator ${product.is_enabled ? 'active' : ''}"></span>`;
    if (isAdmin) {
        document.getElementById('modalIngredientsPrice').textContent =
        product.ingredients_price ? `${product.ingredients_price} IDR` : 'N/A';
    }
    document.getElementById('modalPrice').textContent =
        product.selling_price ? `${product.selling_price} IDR` : 'N/A';

    // Third row
    document.getElementById('modalDescription').textContent = product.description || '';

    // Fourth row - Lack of ingredients warning
    const warningElement = document.getElementById('lackOfIngredientsWarning');
    if (product.lack_of_ingredients && product.lack_of_ingredients.length > 0) {
        const ingredientNames = product.lack_of_ingredients.map(ing => ing.name).join(', ');
        warningElement.textContent = `Lack of ingredients: ${ingredientNames}`;
        warningElement.style.display = 'block';
    } else {
        warningElement.style.display = 'none';
    }

    // Fifth row - Toggle button
    const toggleBtn = document.getElementById('toggleEnableBtn');
    toggleBtn.textContent = product.is_enabled ? 'Disable' : 'Enable';
    toggleBtn.className = `btn ${product.is_enabled ? 'btn-danger' : 'btn-success'}`;
    toggleBtn.onclick = () => toggleProductStatus(product.id);

    // Sixth row - Ingredients table
    const ingredientsTable = document.getElementById('ingredientsTable');
    ingredientsTable.innerHTML = product.ingredients.map(ing => `
        <tr>
            <td>${ing.id}</td>
            <td>${ing.name}</td>
            <td>${ing.weight_grams}g</td>
        </tr>
    `).join('');

    // Seventh row - Nutritional values
    const nutritionalGrid = document.getElementById('nutritionalGrid');
    nutritionalGrid.innerHTML = Object.entries(product.nutritional_value || {})
        .map(([key, value]) => `
            <div class="nutritional-item">
                <span class="nutrient-name">${key.replace(/_/g, ' ')}</span>
                <span class="nutrient-value">${value}</span>
            </div>
        `).join('');
}

async function toggleProductStatus(productId) {
    try {
        const response = await fetch(`/api/control/update/product/${productId}/`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        });

        const data = await response.json();

        if (data.messages) {
            MessageManager.handleAjaxMessages(data.messages);
        }

        if (response.ok) {
            await loadProducts(); // Reload all products
            bootstrap.Modal.getInstance(document.getElementById('productModal')).hide();
        }
    } catch (error) {
        console.error('Error toggling product status:', error);
    }
}

// Modal cleanup
document.getElementById('productModal').addEventListener('hidden.bs.modal', function () {
    document.body.classList.remove('modal-open');
    const modalBackdrop = document.querySelector('.modal-backdrop');
    if (modalBackdrop) {
        modalBackdrop.remove();
    }
});