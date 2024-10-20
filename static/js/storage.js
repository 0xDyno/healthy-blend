// storage.js

class Storage {
    constructor() {
        this.storageKey = 'restaurantStorage';
        this.data = this.loadFromLocalStorage();
        if (!this.data.customMealDraft) {
            this.data.customMealDraft = null;
        }
    }

    loadFromLocalStorage() {
        const savedData = localStorage.getItem(this.storageKey);
        if (savedData) {
            return JSON.parse(savedData);
        }
        return {
            officialMeals: [],
            customMeals: []
        };
    }

    saveToLocalStorage() {
        localStorage.setItem(this.storageKey, JSON.stringify(this.data));
    }

    addItem(product, quantity, isCustom = false) {
        const targetArray = isCustom ? this.data.customMeals : this.data.officialMeals;
        const existingItem = targetArray.find(item =>
            item.product.id === product.id &&
            item.product.nutritional_value.calories === product.nutritional_value.calories
        );
        if (existingItem) {
            existingItem.quantity += quantity;
        } else {
            targetArray.push({product, quantity});
        }
        this.saveToLocalStorage();
    }

    removeItem(id, calories, isOfficial) {
        id = parseInt(id)
        calories = parseInt(calories)
        if (isOfficial) {
            this.data.officialMeals = this.data.officialMeals.filter(item =>
                !(item.product.id === id && item.product.nutritional_value.calories === calories)
            );
        } else {
            this.data.customMeals = this.data.customMeals.filter(item =>
                !(item.product.id === id)
            );
        }

        this.saveToLocalStorage();
    }

    getTotalPrice() {
        const {officialMeals, customMeals} = this.getCartItemsSet();
        const officialTotal = officialMeals.reduce((sum, item) => sum + item.product.nutritional_value.price * item.quantity, 0);
        const customTotal = customMeals.reduce((sum, item) => sum + item.product.nutritional_value.price * item.quantity, 0);
        return officialTotal + customTotal;
    }

    clearCart() {
        this.data.officialMeals = [];
        this.data.customMeals = [];
        this.saveToLocalStorage();
    }

    getCartItemsSet() {
        return {
            officialMeals: this.data.officialMeals,
            customMeals: this.data.customMeals
        };
    }

    getCustomMeals() {
        return this.data.customMeals || [];
    }

    setCustomMeals(customMeals) {
        this.data.customMeals = customMeals;
        this.saveToLocalStorage();
    }

    updateCartInfo() {
        const {officialMeals, customMeals} = this.getCartItemsSet();
        const allItems = [...officialMeals, ...customMeals];
        const cartItemCountElement = document.getElementById('cartItemCount');
        const cartTotalElement = document.getElementById('cartTotal');

        if (cartItemCountElement && cartTotalElement) {
            const itemCount = allItems.reduce((total, item) => total + item.quantity, 0);
            const totalPrice = this.getTotalPrice();

            cartItemCountElement.textContent = itemCount;
            cartTotalElement.textContent = `${totalPrice.toFixed(0)} IDR`;
        }
    }

    getCustomMealDraft() {
        return this.data.customMealDraft;
    }

    setCustomMealDraft(draft) {
        this.data.customMealDraft = draft;
        this.saveToLocalStorage();
    }

    clearCustomMealDraft() {
        this.data.customMealDraft = null;
        this.saveToLocalStorage();
    }
}

const storage = new Storage();
export default storage;