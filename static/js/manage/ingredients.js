// ingredients.js

import {getCookie, getUserRole} from "./utils.js";

let data = [];
const is_admin = getUserRole() === 'owner' || getUserRole() === 'administrator';
const nutritionalFields = [
    'calories', 'proteins', 'fats', 'saturated_fats', 'carbohydrates',
    'sugars', 'fiber', 'vitamin_a', 'vitamin_c', 'vitamin_d', 'vitamin_e',
    'vitamin_k', 'thiamin', 'riboflavin', 'niacin', 'vitamin_b6', 'folate',
    'vitamin_b12', 'calcium', 'iron', 'magnesium', 'phosphorus', 'potassium',
    'sodium', 'zinc', 'copper', 'manganese', 'selenium'
];

document.addEventListener('DOMContentLoaded', function () {
    initializeCommonFeatures();

    if (is_admin) {
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

    const imageUpload = document.getElementById('modalImageUpload');
    if (imageUpload) {
        imageUpload.addEventListener('change', function (e) {
            if (this.files && this.files[0]) {
                const reader = new FileReader();
                reader.onload = function (e) {
                    document.getElementById('modalPreviewImage').src = e.target.result;
                };
                reader.readAsDataURL(this.files[0]);
            }
        });
    }
}

async function loadIngredients() {
    try {
        const response = await fetch('/api/control/get/ingredients/');
        const responseData = await response.json();

        if (responseData.messages) {
            MessageManager.handleAjaxMessages(responseData.messages);
        }

        // Сохраняем только массив ингредиентов
        data = responseData.ingredients || [];

        displayIngredients(data);
    } catch (error) {
        console.error('Error loading ingredients:', error);
    }
}

async function loadIngredientDetails(ingredientId) {
    try {
        const response = await fetch(`/api/control/get/ingredient/${ingredientId}/`);
        const data = await response.json();

        if (data.messages) {
            MessageManager.handleAjaxMessages(data.messages);
        }

        return data.ingredient;
    } catch (error) {
        console.error('Error loading ingredient details:', error);
        return null;
    }
}

function filterIngredients() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const selectedType = document.querySelector('.type-filter-btn.active').dataset.type.toLowerCase();
    const showMenuOnly = document.querySelector('.menu-filter-btn')?.classList.contains('active');

    // Сначала фильтруем по поиску и типу
    let filteredIngredients = data.filter(ingredient => {
        const nameMatch = ingredient.name.toLowerCase().includes(searchTerm);
        const typeMatch = selectedType === '' || ingredient.ingredient_type.toLowerCase() === selectedType;
        return nameMatch && typeMatch;
    });

    // Если активна кнопка меню, показываем только элементы меню
    if (showMenuOnly) {
        filteredIngredients = filteredIngredients.filter(ingredient => ingredient.is_menu);
    }

    displayIngredients(filteredIngredients);
}

function displayIngredients(ingredients) {
    const grid = document.getElementById('ingredientsGrid');
    grid.innerHTML = '';

    ingredients.forEach(ingredient => {
        const card = is_admin ? createAdminIngredientCard(ingredient) : createUserIngredientCard(ingredient);
        grid.appendChild(card);
    });
}

function createUserIngredientCard(ingredient) {
    const card = document.createElement('div');
    card.className = `ingredient-card ${!ingredient.is_available ? 'unavailable' : ''}`;

    card.innerHTML = `
        <img src="${ingredient.image}" alt="${ingredient.name}" class="ingredient-image">
        <div class="ingredient-name">${ingredient.name}</div>
        <div class="ingredient-type">${ingredient.ingredient_type}</div>
        <span class="availability-badge ${ingredient.is_available ? 'available' : 'unavailable'}">
            ${ingredient.is_available ? 'Available' : 'Unavailable'}
        </span>
    `;

    card.addEventListener('click', () => showIngredientModal(ingredient));
    return card;
}

function createAdminIngredientCard(ingredient) {
    const card = document.createElement('div');
    card.className = `ingredient-card ${!ingredient.is_available ? 'unavailable' : ''}`;

    // Create the card content with menu indicator
    card.innerHTML = `
        <img src="${ingredient.image}" alt="${ingredient.name}" class="ingredient-image">
        <div class="ingredient-name-container">
            ${ingredient.is_menu ? '<div class="menu-indicator"></div>' : ''}
            <div class="ingredient-name">${ingredient.name}</div>
        </div>
        <div class="ingredient-info-container">
            <div class="ingredient-type">${ingredient.ingredient_type}</div>
            ${ingredient.selling_price ? `<div class="custom-price">${ingredient.selling_price} IDR</div>` : ''}
        </div>
        <span class="availability-badge ${ingredient.is_available ? 'available' : 'unavailable'}">
            ${ingredient.is_available ? 'Available' : 'Unavailable'}
        </span>
    `;

    card.addEventListener('click', () => showIngredientModal(ingredient));
    return card;
}

async function showIngredientModal(ingredient) {
    const modal = new bootstrap.Modal(document.getElementById('ingredientModal'));

    if (!ingredient) {
        // Создание нового ингредиента
        if (is_admin) {
            setupAdminModal(null);
            setupStatusButtons(null);
        }
        modal.show();
        return;
    }

    // Показываем модальное окно с загрузкой
    document.getElementById('modalContent').style.display = 'none';
    document.getElementById('modalLoader').style.display = 'block';
    modal.show();

    // Загружаем детальную информацию
    const ingredientDetails = await loadIngredientDetails(ingredient.id);

    if (!ingredientDetails) {
        modal.hide();
        return;
    }

    // Скрываем загрузку и показываем контент
    document.getElementById('modalLoader').style.display = 'none';
    document.getElementById('modalContent').style.display = 'block';

    if (is_admin) {
        setupAdminModal(ingredientDetails);
        setupStatusButtons(ingredientDetails);
    } else {
        setupUserModal(ingredientDetails);
    }
}

function setupStatusButtons(ingredient) {
    const statusButtons = document.querySelectorAll('.status-button');

    statusButtons.forEach(button => {
        const fieldId = button.dataset.field;
        const checkbox = document.getElementById(fieldId);

        // Установка начального состояния
        let isActive = false;
        if (ingredient) {
            switch (fieldId) {
                case 'modalIsMenu':
                    isActive = ingredient.is_menu;
                    break;
                case 'modalIsAvailable':
                    isActive = ingredient.is_available;
                    break;
                case 'modalIsDishIngredient':
                    isActive = ingredient.is_dish_ingredient;
                    break;
            }
        }

        if (isActive) {
            button.classList.add('active');
            checkbox.checked = true;
        } else {
            button.classList.remove('active');
            checkbox.checked = false;
        }

        button.onclick = function() {
            this.classList.toggle('active');
            checkbox.checked = this.classList.contains('active');
        };
    });
}

function setupUserModal(ingredient) {
    document.getElementById('modalName').textContent = ingredient.name;
    document.getElementById('modalImage').src = ingredient.image;
    document.getElementById('modalType').textContent = ingredient.ingredient_type;

    const availabilityStatus = document.getElementById('modalAvailabilityStatus');
    availabilityStatus.textContent = ingredient.is_available ? 'Available' : 'Unavailable';
    availabilityStatus.className = `availability-badge ${ingredient.is_available ? 'available' : 'unavailable'}`;

    // Настройка кнопки переключения доступности
    const toggleBtn = document.getElementById('toggleAvailabilityBtn');
    if (toggleBtn) {
        toggleBtn.textContent = ingredient.is_available ? 'Mark as Unavailable' : 'Mark as Available';
        toggleBtn.className = `availability-btn ${ingredient.is_available ? 'btn-unavailable' : 'btn-available'}`;

        // Добавляем обработчик события
        toggleBtn.onclick = async () => {
            try {
                const response = await fetch(`/api/control/update/ingredient/${ingredient.id}/`, {
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
                    // Обновляем состояние на странице
                    ingredient.is_available = !ingredient.is_available;
                    await loadIngredients(); // Перезагружаем все ингредиенты

                    // Закрываем модальное окно
                    const modal = bootstrap.Modal.getInstance(document.getElementById('ingredientModal'));
                    modal.hide();
                }
            } catch (error) {
                console.error('Error toggling availability:', error);
            }
        };
    }
}

function setupAdminModal(ingredient) {
    const isNew = !ingredient;
    document.getElementById('ingredientName').textContent = isNew ? 'Create new Ingredient' : ingredient.name;
    document.getElementById('ingredientId').textContent = isNew ? '' : '#' + ingredient.id;

    const submitButton = document.getElementById('submitButton');
    if (submitButton) {
        submitButton.textContent = isNew ? 'Create' : 'Update';
    }

    const previewImage = document.getElementById('modalPreviewImage');
    const imagePlaceholder = document.querySelector('.image-placeholder');
    if (previewImage && imagePlaceholder) {
        if (ingredient?.image) {
            previewImage.src = ingredient.image;
            previewImage.style.display = 'block';
            imagePlaceholder.style.display = 'none';
        } else {
            previewImage.src = '';
            previewImage.style.display = 'none';
            imagePlaceholder.style.display = 'flex';
        }
    }

    if (!document.getElementById('ingredientForm')) {
        console.error('Admin form not found');
        return;
    }

    // Set values for all form fields
    const fields = {
        modalIngredientName: ingredient?.name || '',
        modalDescription: ingredient?.description || '',
        modalType: ingredient?.ingredient_type || 'other',
        modalStep: ingredient?.step || 1,
        modalMinOrder: ingredient?.min_order || 0,
        modalMaxOrder: ingredient?.max_order || 500,
        modalPurchasePrice: ingredient?.purchase_price || 0,
        modalSellingPrice: ingredient?.selling_price || '',
        modalIsMenu: ingredient?.is_menu || false,
        modalIsDishIngredient: ingredient?.is_dish_ingredient || false,
        modalIsAvailable: ingredient?.is_available || false
    };

    // Set values for all fields
    Object.entries(fields).forEach(([id, value]) => {
        const element = document.getElementById(id);
        if (element) {
            if (element.type === 'checkbox') {
                element.checked = value;
            } else {
                element.value = value;
            }
        }
    });

    // Setup nutritional values
    const nutritionalContainer = document.querySelector('.nutritional-values');
    if (nutritionalContainer) {
        let nutritionalContent = '<h6 class="mb-3">Nutritional Values</h6><div class="nutritional-grid">';

        nutritionalFields.forEach(field => {
            nutritionalContent += `
                <div class="nutritional-item">
                    <label>${field.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:</label>
                    <input type="number" 
                           step="0.01" 
                           class="form-control" 
                           id="modal${field}" 
                           value="${ingredient?.nutritional_value?.[field] || 0}">
                </div>
            `;
        });

        nutritionalContent += '</div>';
        nutritionalContainer.innerHTML = nutritionalContent;
    }

    const form = document.getElementById('ingredientForm');
    if (form) {
        form.dataset.ingredientId = ingredient?.id || '';
    }
}

async function handleFormSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const ingredientId = form.dataset.ingredientId;
    const isNew = !ingredientId;

    // Создаем FormData для отправки файлов
    const formData = new FormData();

    // Добавляем файл изображения, если он был выбран
    const imageInput = document.getElementById('modalImageUpload');
    if (imageInput.files.length > 0) {
        formData.append('image', imageInput.files[0]);
    }

    // Собираем nutritional value
    const nutritionalValue = {};
    nutritionalFields.forEach(field => {
        nutritionalValue[field] = parseFloat(document.getElementById(`modal${field}`).value) || 0;
    });

    // Собираем основные данные ингредиента
    const ingredientData = {
        name: document.getElementById('modalIngredientName').value,
        description: document.getElementById('modalDescription').value,
        ingredient_type: document.getElementById('modalType').value,
        step: parseFloat(document.getElementById('modalStep').value),
        min_order: parseInt(document.getElementById('modalMinOrder').value),
        max_order: parseInt(document.getElementById('modalMaxOrder').value),
        purchase_price: parseInt(document.getElementById('modalPurchasePrice').value),
        selling_price: document.getElementById('modalSellingPrice').value || null,
        is_menu: document.getElementById('modalIsMenu').checked,
        is_dish_ingredient: document.getElementById('modalIsDishIngredient').checked,
        is_available: document.getElementById('modalIsAvailable').checked,
        nutritional_value: nutritionalValue
    };

    // Добавляем JSON данные в FormData
    formData.append('data', JSON.stringify(ingredientData));

    try {
        const url = isNew ? '/api/control/create/ingredient/' : `/api/control/update/ingredient/${ingredientId}/`;
        const method = isNew ? 'POST' : 'PUT';
        console.log(isNew)

        const response = await fetch(url, {
            method: method,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: formData
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

document.getElementById('ingredientModal').addEventListener('hidden.bs.modal', function () {
    document.body.classList.remove('modal-open');
    const modalBackdrop = document.querySelector('.modal-backdrop');
    if (modalBackdrop) {
        modalBackdrop.remove();
    }
});