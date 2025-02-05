// Shared utilities
const API_BASE_URL = 'http://localhost:8000';

// Helper functions
function createMessageElement(text, className = '') {
    const div = document.createElement('div');
    div.classList.add('chat-message', className);
    div.textContent = text;
    return div;
}

// Update the makeApiRequest function
async function makeApiRequest(endpoint, data) {
    const headers = { 'Content-Type': 'application/json' };
    const token = localStorage.getItem('token');
    
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(data),
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

// Form handling (index.html)
class NutritionForm {
    constructor() {
        this.form = document.getElementById('nutrition-form');
        if (this.form) {
            this.initializeForm();
            this.checkAuth();
        }
    }

    checkAuth() {
        if (!localStorage.getItem('token')) {
            window.location.href = 'login.html';
        }
    }

    initializeForm() {
        this.form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const submitButton = this.form.querySelector('button[type="submit"]');
            submitButton.disabled = true;

            try {
                const formData = this.collectFormData();
                await this.submitForm(formData);
            } catch (error) {
                alert('Error generating meal plan. Please try again.');
            } finally {
                submitButton.disabled = false;
            }
        });
    }

    collectFormData() {
        return {
            username: localStorage.getItem('username'),  // Add username from storage
            age: document.getElementById('age').value,
            height: document.getElementById('height').value,
            weight: document.getElementById('weight').value,
            goal: document.getElementById('goal').value,
            planType: document.getElementById('plan-type').value,
            currentDiet: document.getElementById('current-diet').value || '',
        };
    }

    async submitForm(formData) {
        try {
            console.log('Submitting form data:', formData);
            const response = await makeApiRequest('/generate-meal-plan', formData);
            console.log('Received response:', response);
            
            if (!response.mealPlan) {
                console.error('No meal plan in response:', response);
                throw new Error('Invalid response format');
            }
            
            localStorage.setItem('mealPlan', response.mealPlan);
            window.location.href = 'chatpage.html';
        } catch (error) {
            console.error('Form submission error:', error);
            alert(`Error generating meal plan: ${error.message}`);
            throw error;
        }
    }
}

// Chat handling (chat.html)
class ChatInterface {
    constructor() {
        this.chatBox = document.getElementById('chat-box');
        this.userMessageInput = document.getElementById('user-message');
        this.sendMessageButton = document.getElementById('send-message');
        
        // Initialize marked options
        marked.setOptions({
            breaks: true,  // Convert \n to <br>
            gfm: true     // Enable GitHub Flavored Markdown
        });
        
        if (this.chatBox) {
            this.initializeChat();
        }
    }

    displayMessage(text, className) {
        const messageElement = document.createElement('div');
        messageElement.classList.add('chat-message', className);
        // Use marked to render markdown
        messageElement.innerHTML = marked.parse(text);
        this.chatBox.appendChild(messageElement);
        this.chatBox.scrollTop = this.chatBox.scrollHeight;
    }

    initializeChat() {
        const mealPlan = localStorage.getItem('mealPlan');
        if (mealPlan) {
            this.displayMessage(mealPlan, 'assistant-message');
        }

        this.conversation = [
            { role: 'system', content: 'You are a dietician that should be polite and helpful.' }
        ];

        if (mealPlan) {
            this.conversation.push({ role: 'assistant', content: mealPlan });
        }

        this.setupEventListeners();
    }

    setupEventListeners() {
        this.sendMessageButton.addEventListener('click', () => this.handleSendMessage());
        
        this.userMessageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleSendMessage();
            }
        });
    }

    async handleSendMessage() {
        const userMessage = this.userMessageInput.value.trim();
        if (!userMessage) return;

        this.sendMessageButton.disabled = true;
        this.userMessageInput.value = '';

        try {
            // Display user message
            this.displayMessage(`You: ${userMessage}`, 'user-message');
            this.conversation.push({ role: 'user', content: userMessage });

            // Add loading indicator
            const loadingElement = createMessageElement('Assistant is typing...', 'loading-message');
            this.chatBox.appendChild(loadingElement);

            // Get assistant response
            const response = await makeApiRequest('/follow-up', { conversation: this.conversation });
            
            // Remove loading indicator
            loadingElement.remove();

            // Display assistant response
            if (response && response.response) {
                this.displayMessage(`Assistant: ${response.response}`, 'assistant-message');
                this.conversation.push({ role: 'assistant', content: response.response });
            } else {
                throw new Error('Invalid response format');
            }

        } catch (error) {
            console.error('Chat Error:', error);
            this.displayMessage('Error: Unable to get response. Please try again.', 'error-message');
        } finally {
            this.sendMessageButton.disabled = false;
            this.userMessageInput.focus();
        }
    }
}

// Initialize appropriate handler based on current page
document.addEventListener('DOMContentLoaded', () => {
    AuthManager.redirectToLogin();
    
    // Initialize forms
    new NutritionForm();
    new ChatInterface();
    
    // Initialize dashboard if we're on the dashboard page
    if (window.location.pathname.endsWith('dashboard.html')) {
        loadDashboard();
    }
});

// Add styles
const styles = `
    .chat-message {
        margin: 10px;
        padding: 10px;
        border-radius: 5px;
    }
    
    .user-message {
        background-color: #e3f2fd;
    }
    
    .assistant-message {
        background-color: #f5f5f5;
    }
    
    .error-message {
        background-color: #ffebee;
        color: #c62828;
    }
    
    .loading-message {
        background-color: #f5f5f5;
        font-style: italic;
    }
`;

const styleSheet = document.createElement('style');
styleSheet.textContent = styles;
document.head.appendChild(styleSheet);


class AuthManager {
    static async register(formData) {
        const response = await fetch('http://localhost:8000/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Registration failed');
        }

        return response.json();
    }

    static async login(username, password) {
        try {
            const response = await fetch('http://localhost:8000/token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: new URLSearchParams({
                    'username': username,
                    'password': password,
                    'grant_type': 'password'
                }).toString()
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Login failed');
            }

            const data = await response.json();
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('username', username);
            
            // Redirect to dashboard instead of index
            window.location.href = 'dashboard.html';
            return data;
        } catch (error) {
            console.error('Login error:', error);
            throw error;
        }
    }

    static isLoggedIn() {
        return !!localStorage.getItem('token');
    }

    static logout() {
        localStorage.removeItem('token');
        localStorage.removeItem('username');
        window.location.href = 'login.html';
    }

    static redirectToLogin() {
        if (!this.isLoggedIn() && !window.location.pathname.endsWith('login.html')) {
            window.location.href = 'login.html';
        }
    }
}

// Add event listeners for login/register forms
document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');

    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            try {
                await AuthManager.login(
                    document.getElementById('login-username').value,
                    document.getElementById('login-password').value
                );
                // Login handler in AuthManager already redirects to dashboard
            } catch (error) {
                alert('Login failed: ' + error.message);
            }
        });
    }

    if (registerForm) {
        registerForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            try {
                const formData = {
                    username: document.getElementById('register-username').value,
                    email: document.getElementById('register-email').value,
                    first_name: document.getElementById('register-firstname').value,
                    last_name: document.getElementById('register-lastname').value,
                    birthday: document.getElementById('register-birthday').value,
                    age: parseInt(document.getElementById('register-age').value),
                    height: parseFloat(document.getElementById('register-height').value),
                    weight: parseFloat(document.getElementById('register-weight').value),
                    goal: document.getElementById('register-goal').value,
                    password: document.getElementById('register-password').value
                };

                await AuthManager.register(formData);
                await AuthManager.login(formData.username, formData.password);
                window.location.href = 'index.html';  // New users go to meal plan generation
            } catch (error) {
                alert('Registration failed: ' + error.message);
            }
        });
    }
});

// Add to the top of your script
let currentUser = null;

// Add this function to display user info
function displayUserInfo() {
    const username = localStorage.getItem('username');
    const userDisplay = document.getElementById('user-display');
    const userDetails = document.getElementById('user-details');
    
    if (userDisplay) {
        userDisplay.textContent = username;
    }
    
    if (userDetails && currentUser) {
        userDetails.innerHTML = `
            <p><strong>Name:</strong> ${currentUser.first_name} ${currentUser.last_name}</p>
            <p><strong>Age:</strong> ${currentUser.age}</p>
            <p><strong>Height:</strong> ${currentUser.height} inches</p>
            <p><strong>Weight:</strong> ${currentUser.weight} lbs</p>
            <p><strong>Goal:</strong> ${currentUser.goal}</p>
        `;
    }
}

// Add function to fetch user data
async function fetchUserData() {
    try {
        const response = await fetch('http://localhost:8000/user/me', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        if (response.ok) {
            currentUser = await response.json();
            displayUserInfo();
        }
    } catch (error) {
        console.error('Error fetching user data:', error);
    }
}

// Update the generateMealPlan function
async function generateMealPlan() {
    try {
        const planType = document.getElementById('plan-type').value;
        const currentDiet = document.getElementById('current-diet').value;

        const mealPlanRequest = {
            username: currentUser.username,
            age: currentUser.age,
            height: currentUser.height,
            weight: currentUser.weight,
            goal: currentUser.goal,
            planType: planType,
            currentDiet: currentDiet || ''
        };

        const response = await makeApiRequest('/generate-meal-plan', mealPlanRequest);
        
        if (response.mealPlan) {
            localStorage.setItem('mealPlan', response.mealPlan);
            window.location.href = 'dashboard.html';  // Redirect to dashboard instead of chatpage
        }
    } catch (error) {
        alert('Error generating meal plan: ' + error.message);
    }
}

// Update the DOMContentLoaded event listener
document.addEventListener('DOMContentLoaded', () => {
    AuthManager.redirectToLogin();
    
    if (AuthManager.isLoggedIn()) {
        fetchUserData();
    }
    
    // ... rest of your initialization code ...
});

// Add these new functions
async function loadDashboard() {
    if (!AuthManager.isLoggedIn()) {
        window.location.href = 'login.html';
        return;
    }

    await fetchUserData();
    await loadCurrentMealPlan();
}

async function loadCurrentMealPlan() {
    try {
        const response = await fetch('http://localhost:8000/user/meal-plan', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            const mealPlanElement = document.getElementById('current-meal-plan');
            if (mealPlanElement && data.meal_plan) {
                mealPlanElement.innerHTML = marked.parse(data.meal_plan);
            } else {
                mealPlanElement.innerHTML = '<p>No meal plan generated yet. Click "Generate New Plan" to create one.</p>';
            }
        }
    } catch (error) {
        console.error('Error loading meal plan:', error);
    }
}

function showTweakForm() {
    const tweakForm = document.getElementById('tweak-form');
    tweakForm.style.display = 'block';
}

async function submitTweakRequest() {
    const tweakRequest = document.getElementById('tweak-request').value;
    if (!tweakRequest.trim()) {
        alert('Please describe what changes you would like to make.');
        return;
    }

    try {
        const response = await makeApiRequest('/tweak-meal-plan', {
            username: currentUser.username,
            currentDiet: tweakRequest
        });

        if (response.mealPlan) {
            // Update the meal plan display directly instead of redirecting
            const mealPlanElement = document.getElementById('current-meal-plan');
            if (mealPlanElement) {
                mealPlanElement.innerHTML = marked.parse(response.mealPlan);
            }
            // Hide the tweak form
            document.getElementById('tweak-form').style.display = 'none';
        }
    } catch (error) {
        alert('Error processing tweak request: ' + error.message);
    }
}
