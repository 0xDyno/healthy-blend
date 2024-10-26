// ingredients.js

import {getCookie} from "./utils.js";

let allIngredients = [];

document.addEventListener('DOMContentLoaded', function() {
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
});

async function loadIngredients() {
    try {
        const response = await fetch('/api/get/ingredients/');
        allIngredients = await response.json();
        displayIngredients(allIngredients);
    } catch (error) {
        console.error('Error loading ingredients:', error);
    }
}

function filterIngredients() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const selectedType = document.querySelector('.type-filter-btn.active').dataset.type.toLowerCase();

    const filteredIngredients = allIngredients.filter(ingredient => {
        const nameMatch = ingredient.name.toLowerCase().includes(searchTerm);
        const typeMatch = selectedType === '' || ingredient.ingredient_type.toLowerCase() === selectedType;
        return nameMatch && typeMatch;
    });

    displayIngredients(filteredIngredients);
}

function displayIngredients(ingredients) {
    const grid = document.getElementById('ingredientsGrid');
    grid.innerHTML = '';

    ingredients.forEach(ingredient => {
        const card = createIngredientCard(ingredient);
        grid.appendChild(card);
    });
}

function createIngredientCard(ingredient) {
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

function showIngredientModal(ingredient) {
    const modal = new bootstrap.Modal(document.getElementById('ingredientModal'));

    document.getElementById('modalName').textContent = ingredient.name;
    document.getElementById('modalImage').src = ingredient.image;

    const availabilityButton = document.getElementById('availabilityButton');
    availabilityButton.textContent = ingredient.is_available ?
        'Mark as Unavailable' : 'Mark as Available';
    availabilityButton.className = `availability-btn ${ingredient.is_available ? 
        'btn-unavailable' : 'btn-available'}`;

    availabilityButton.onclick = () => updateIngredientAvailability(ingredient.id, !ingredient.is_available);

    modal.show();
}

async function updateIngredientAvailability(id, newAvailability) {
    try {
        const response = await fetch(`/api/update/ingredient/${id}/`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ available: newAvailability })
        });

        if (response.ok) {
            loadIngredients();
            bootstrap.Modal.getInstance(document.getElementById('ingredientModal')).hide();
        }
        filterIngredients();
        bootstrap.Modal.getInstance(document.getElementById('ingredientModal')).hide();
    } catch (error) {
        console.error('Error updating ingredient:', error);
    }
}