// storage.js
class Storage {
    constructor() {
        this.storageKey = 'restaurantStorage';
        this.data = this.loadFromLocalStorage();
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

    addItem(product, quantity) {
        const existingItem = this.data.officialMeals.find(item =>
            item.product.id === product.id &&
            item.product.selectedCalories === product.selectedCalories
        );
        if (existingItem) {
            existingItem.quantity += quantity;
        } else {
            this.data.officialMeals.push({ product, quantity });
        }
        this.saveToLocalStorage();
    }

    removeItem(productId, selectedCalories) {
        this.data.officialMeals = this.data.officialMeals.filter(item =>
            !(item.product.id === productId && item.product.selectedCalories === selectedCalories)
        );
        this.saveToLocalStorage();
    }

    addCustomMeal(customMeal) {
        this.data.customMeals.push(customMeal);
        this.saveToLocalStorage();
    }

    getTotalPrice() {
        return this.data.officialMeals.reduce((total, item) => total + item.product.nutritional_value.price * item.quantity, 0);
    }

    clearCart() {
        this.data.officialMeals = [];
        this.saveToLocalStorage();
    }

    clearCustomMeals() {
        this.data.customMeals = [];
        this.saveToLocalStorage();
    }

    getCartItems() {
        return this.data.officialMeals;
    }

    getCustomMeals() {
        return this.data.customMeals;
    }

    updateCartInfo() {
        const cartItems = this.getCartItems();
        const cartItemCountElement = document.getElementById('cartItemCount');
        const cartTotalElement = document.getElementById('cartTotal');

        if (cartItemCountElement && cartTotalElement) {
            const itemCount = cartItems.reduce((total, item) => total + item.quantity, 0);
            const totalPrice = this.getTotalPrice();

            cartItemCountElement.textContent = itemCount;
            cartTotalElement.textContent = `${totalPrice.toFixed(0)} IDR`;
        }
    }
}

const storage = new Storage();
export default storage;