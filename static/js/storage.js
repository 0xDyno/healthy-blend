// storage.js

const OFFICIAL_MEALS_KEY = 'officialMeals';
const CUSTOM_MEALS_KEY = 'customMeals';
const CUSTOM_MEAL_DRAFT_KEY = 'customMealDraft';

export default {
    getOfficialMeals() {
        return JSON.parse(localStorage.getItem(OFFICIAL_MEALS_KEY)) || [];
    },

    setOfficialMeals(meals) {
        localStorage.setItem(OFFICIAL_MEALS_KEY, JSON.stringify(meals));
    },

    getCustomMeals() {
        return JSON.parse(localStorage.getItem(CUSTOM_MEALS_KEY)) || [];
    },

    setCustomMeals(meals) {
        localStorage.setItem(CUSTOM_MEALS_KEY, JSON.stringify(meals));
    },

    getCustomMealDraft() {
        return JSON.parse(localStorage.getItem(CUSTOM_MEAL_DRAFT_KEY)) || null;
    },

    setCustomMealDraft(draft) {
        localStorage.setItem(CUSTOM_MEAL_DRAFT_KEY, JSON.stringify(draft));
    },

    clearCustomMealDraft() {
        localStorage.removeItem(CUSTOM_MEAL_DRAFT_KEY);
    },

    addItem(product, amount) {
        const isCustom = product.product_type === 'custom';
        const storageKey = isCustom ? CUSTOM_MEALS_KEY : OFFICIAL_MEALS_KEY;
        const meals = JSON.parse(localStorage.getItem(storageKey)) || [];

        const existingItemIndex = meals.findIndex(item =>
            item.product.id === product.id &&
            item.product.selectedCalories === product.selectedCalories
        );

        if (existingItemIndex !== -1) {
            meals[existingItemIndex].amount += amount;
        } else {
            meals.push({
                product: {
                    id: product.id,
                    name: product.name,
                    description: product.description,
                    image: product.image,
                    product_type: product.product_type,
                    selectedCalories: product.selectedCalories,
                    nutritional_value: {...product.nutritional_value},
                    price: product.price,
                    ingredients: product.ingredients ? [...product.ingredients] : []
                },
                amount
            });
        }

        localStorage.setItem(storageKey, JSON.stringify(meals));
    },


    removeItem(productId, calories, isCustom) {
        const storageKey = isCustom ? CUSTOM_MEALS_KEY : OFFICIAL_MEALS_KEY;
        const meals = JSON.parse(localStorage.getItem(storageKey)) || [];
        const updatedMeals = meals.filter(item =>
            !(item.product.id === parseInt(productId) &&
                parseInt(item.product.nutritional_value.calories) === parseInt(calories))
        );

        localStorage.setItem(storageKey, JSON.stringify(updatedMeals));
    },

    // updateItemAmount(productId, amount, isCustom) {
    //     const storageKey = isCustom ? CUSTOM_MEALS_KEY : OFFICIAL_MEALS_KEY;
    //     const meals = JSON.parse(localStorage.getItem(storageKey)) || [];
    //
    //     const updatedMeals = meals.map(item => {
    //         if (item.product.id === productId) {
    //             return {...item, amount};
    //         }
    //         return item;
    //     });
    //
    //     localStorage.setItem(storageKey, JSON.stringify(updatedMeals));
    // },

    getCartItemsSet() {
        return {
            officialMeals: this.getOfficialMeals(),
            customMeals: this.getCustomMeals()
        };
    },

    getTotalPrice() {
        const {officialMeals, customMeals} = this.getCartItemsSet();
        const allMeals = [...officialMeals, ...customMeals];

        return allMeals.reduce((total, item) => {
            return total + (item.product.price * item.amount);
        }, 0);
    },

    clearCart() {
        localStorage.removeItem(OFFICIAL_MEALS_KEY);
        localStorage.removeItem(CUSTOM_MEALS_KEY);
    },

    updateCartInfo() {
        const cartItemCount = document.getElementById('cartItemCount');
        const cartTotal = document.getElementById('cartTotal');

        if (cartItemCount && cartTotal) {
            const {officialMeals, customMeals} = this.getCartItemsSet();
            const totalItems = [...officialMeals, ...customMeals].reduce((sum, item) => sum + item.amount, 0);
            const totalPrice = this.getTotalPrice();

            cartItemCount.textContent = totalItems;
            cartTotal.textContent = `${totalPrice.toFixed(0)} IDR`;
        }
    }
};