import { getCookie, getUserRole } from "./utils.js";

let allIngredients = [];
const nutritionalFields = [
    'calories', 'proteins', 'fats', 'saturated_fats', 'carbohydrates',
    'sugars', 'fiber', 'vitamin_a', 'vitamin_c', 'vitamin_d', 'vitamin_e',
    'vitamin_k', 'thiamin', 'riboflavin', 'niacin', 'vitamin_b6', 'folate',
    'vitamin_b12', 'calcium', 'iron', 'magnesium', 'phosphorus', 'potassium',
    'sodium', 'zinc', 'copper', 'manganese', 'selenium'
];

document.addEventListener('DOMContentLoaded', function () {
    const userRole = getUserRole();
    initializeCommonFeatures();

    if (userRole === 'owner' || userRole === 'administrator') {
        initializeAdminFeatures();
    }
});

function initializeCommonFeatures() {
    loadIngredients();

    document.getElementById('searchInput').addEventListener('input', filterIngredients);

    const filterButtons = document.querySelectorAll('.type-filter-btn');
    filterButtons.forEach(button => {
        button.addEventListener('click', (e) => {
            filterButtons.forEach(btn => btn.classList.remove('active'));
            e.target.classList.add('active');
            filterIngredients();
        });
    });
}

function initializeAdminFeatures() {
    const createBtn = document.getElementById('createIngredientBtn');
    if (createBtn) {
        createBtn.addEventListener('click', () => showIngredientModal(null));
    }

    const menuFilterBtn = document.querySelector('.menu-filter-btn');
    if (menuFilterBtn) {
        menuFilterBtn.addEventListener('click', (e) => {
            e.target.classList.toggle('active');
            filterIngredients();
        });
    }

    const form = document.getElementById('ingredientForm');
    if (form) {
        form.addEventListener('submit', handleFormSubmit);
    }
}

async function loadIngredients() {
    try {
        const response = await fetch('/api/get/ingredients/');
        allIngredients = await response.json();

        if (allIngredients.messages) {
            MessageManager.handleAjaxMessages(allIngredients.messages);
        }

        displayIngredients(allIngredients);
    } catch (error) {
        console.error('Error loading ingredients:', error);
    }
}

function filterIngredients() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const selectedType = document.querySelector('.type-filter-btn.active').dataset.type.toLowerCase();
    const userRole = getUserRole();

    let filteredIngredients = allIngredients.filter(ingredient => {
        const nameMatch = ingredient.name.toLowerCase().includes(searchTerm);
        const typeMatch = selectedType === '' || ingredient.ingredient_type.toLowerCase() === selectedType;

        if (userRole === 'owner' || userRole === 'administrator') {
            const menuFilterBtn = document.querySelector('.menu-filter-btn');
            const showMenuOnly = menuFilterBtn?.classList.contains('active');
            return nameMatch && typeMatch && (!showMenuOnly || ingredient.is_menu);
        }

        return nameMatch && typeMatch;
    });

    displayIngredients(filteredIngredients);
}

function displayIngredients(ingredients) {
    const grid = document.getElementById('ingredientsGrid');
    grid.innerHTML = '';
    const userRole = getUserRole();

    ingredients.forEach(ingredient => {
        const card = userRole === 'owner' || userRole === 'administrator'
            ? createAdminIngredientCard(ingredient)
            : createUserIngredientCard(ingredient);
        grid.appendChild(card);
    });
}

function createUserIngredientCard(ingredient) {
    const card = document.createElement('div');
    card.className = `ingredient-card ${!ingredient.available ? 'unavailable' : ''}`;

    card.innerHTML = `
        <img src="${ingredient.image}" alt="${ingredient.name}" class="ingredient-image">
        <div class="ingredient-name">${ingredient.name}</div>
        <div class="ingredient-type">${ingredient.ingredient_type}</div>
        <span class="availability-badge ${ingredient.available ? 'available' : 'unavailable'}">
            ${ingredient.available ? 'Available' : 'Unavailable'}
        </span>
    `;

    card.addEventListener('click', () => showIngredientModal(ingredient));
    return card;
}

function createAdminIngredientCard(ingredient) {
    const card = document.createElement('div');
    card.className = `ingredient-card ${!ingredient.available ? 'unavailable' : ''}`;

    card.innerHTML = `
        <img src="${ingredient.image}" alt="${ingredient.name}" class="ingredient-image">
        <div class="ingredient-name">${ingredient.name}</div>
        <div class="ingredient-type">${ingredient.ingredient_type}</div>
        ${ingredient.is_menu ? '<div class="menu-badge">Menu</div>' : ''}
        <div class="price-info">
            <span>Price: $${ingredient.price}</span>
            ${ingredient.price_per_gram ? `<span>Per gram: $${ingredient.price_per_gram}</span>` : ''}
            ${ingredient.custom_price ? `<span>Custom: $${ingredient.custom_price}</span>` : ''}
        </div>
        <span class="availability-badge ${ingredient.available ? 'available' : 'unavailable'}">
            ${ingredient.available ? 'Available' : 'Unavailable'}
        </span>
    `;

    card.addEventListener('click', () => showIngredientModal(ingredient));
    return card;
}

function setupUserModal(ingredient) {
    document.getElementById('modalName').textContent = ingredient.name;
    document.getElementById('modalImage').src = ingredient.image;

    const availabilityButton = document.getElementById('availabilityButton');
    availabilityButton.textContent = ingredient.available ? 'Mark as Unavailable' : 'Mark as Available';
    availabilityButton.className = `availability-btn ${ingredient.available ? 'btn-unavailable' : 'btn-available'}`;
    availabilityButton.onclick = () => updateIngredientAvailability(ingredient.id, !ingredient.available);
}

function setupAdminModal(ingredient) {
    const isNew = !ingredient;
    document.getElementById('modalName').textContent = isNew ? 'Create New Ingredient' : 'Edit Ingredient';

    // Basic fields
    document.getElementById('modalIngredientName').value = ingredient?.name || '';
    document.getElementById('modalDescription').value = ingredient?.description || '';
    document.getElementById('modalImageUrl').value = ingredient?.image || '';
    document.getElementById('modalType').value = ingredient?.ingredient_type || 'other';
    document.getElementById('modalStep').value = ingredient?.step || 0.5;
    document.getElementById('modalMinOrder').value = ingredient?.min_order || 1;
    document.getElementById('modalMaxOrder').value = ingredient?.max_order || 50;
    document.getElementById('modalPrice').value = ingredient?.price || 0;
    document.getElementById('modalPricePerGram').value = ingredient?.price_per_gram || 0;
    document.getElementById('modalCustomPrice').value = ingredient?.custom_price || '';
    document.getElementById('modalIsMenu').checked = ingredient?.is_menu || false;
    document.getElementById('modalIsForDish').checked = ingredient?.is_for_dish || false;
    document.getElementById('modalAvailable').checked = ingredient?.available || false;

    // Nutritional values
    const nutritionalContainer = document.querySelector('.nutritional-values');
    nutritionalContainer.innerHTML = '<h6>Nutritional Values</h6>';

    nutritionalFields.forEach(field => {
        const value = ingredient?.nutritional_value?.[field] || 0;
        nutritionalContainer.innerHTML += `
            <div class="form-group">
                <label>${field.replace('_', ' ')}:</label>
                <input type="number" step="0.01" class="form-control" 
                       id="modal${field}" value="${value}">
            </div>
        `;
    });

    document.getElementById('ingredientForm').dataset.ingredientId = ingredient?.id || '';
}

async function handleFormSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const ingredientId = form.dataset.ingredientId;
    const isNew = !ingredientId;

    const nutritionalValue = {};
    nutritionalFields.forEach(field => {
        nutritionalValue[field] = parseFloat(document.getElementById(`modal${field}`).value) || 0;
    });

    const ingredientData = {
        name: document.getElementById('modalIngredientName').value,
        description: document.getElementById('modalDescription').value,
        image: document.getElementById('modalImageUrl').value,
        ingredient_type: document.getElementById('modalType').value,
        step: parseFloat(document.getElementById('modalStep').value),
        min_order: parseInt(document.getElementById('modalMinOrder').value),
        max_order: parseInt(document.getElementById('modalMaxOrder').value),
        price: parseFloat(document.getElementById('modalPrice').value),
        price_per_gram: parseInt(document.getElementById('modalPricePerGram').value),
        custom_price: document.getElementById('modalCustomPrice').value || null,
        is_menu: document.getElementById('modalIsMenu').checked,
        is_for_dish: document.getElementById('modalIsForDish').checked,
        available: document.getElementById('modalAvailable').checked,
        nutritional_value: nutritionalValue
    };

    try {
        const url = isNew ? '/api/create/ingredient/' : `/api/update/ingredient/${ingredientId}/`;
        const method = isNew ? 'POST' : 'PUT';

        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(ingredientData)
        });

        const data = await response.json();

        if (data.messages) {
            MessageManager.handleAjaxMessages(data.messages);
        }

        if (response.ok) {
            await loadIngredients();
            bootstrap.Modal.getInstance(document.getElementById('ingredientModal')).hide();
        }
    } catch (error) {
        console.error('Error saving ingredient:', error);
    }
}

async function updateIngredientAvailability(id, newAvailability) {
    try {
        const response = await fetch(`/api/update/ingredient/${id}/`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({available: newAvailability})
        });

        const data = await response.json();

        if (data.messages) {
            MessageManager.handleAjaxMessages(data.messages);
        }

        if (response.ok) {
            await loadIngredients();
            bootstrap.Modal.getInstance(document.getElementById('ingredientModal')).hide();
        }
    } catch (error) {
        console.error('Error updating ingredient:', error);
    }
}