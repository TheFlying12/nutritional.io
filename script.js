// Update all localhost URLs to your Heroku URL
const API_BASE_URL = 'https://nutritional.herokuapp.com';

// Update any other localhost references in AuthManager class
static async register(formData) {
    const response = await fetch(`${API_BASE_URL}/register`, {
        // ...
    });
}

static async login(username, password) {
    const response = await fetch(`${API_BASE_URL}/token`, {
        // ...
    });
}

// Update fetchUserData
async function fetchUserData() {
    const response = await fetch(`${API_BASE_URL}/user/me`, {
        // ...
    });
}

// Update loadCurrentMealPlan
async function loadCurrentMealPlan() {
    const response = await fetch(`${API_BASE_URL}/user/meal-plan`, {
        // ...
    });
} 