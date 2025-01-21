// Shared utilities
const API_URL = 'https://your-backend-domain.com';

// Helper functions
function createMessageElement(text, className = '') {
    const div = document.createElement('div');
    div.classList.add('chat-message', className);
    div.textContent = text;
    return div;
}

// Update the makeApiRequest function to include authentication
async function makeApiRequest(endpoint, data) {
    const headers = { 'Content-Type': 'application/json' };
    const token = AuthManager.getToken();
    
    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    try {
        const response = await fetch(`http://localhost:8000${endpoint}`, {
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
            name: document.getElementById('name').value,
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
        const messageElement = createMessageElement(text, className);
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

    displayMessage(text, className) {
        const messageElement = createMessageElement(text, className);
        this.chatBox.appendChild(messageElement);
        this.chatBox.scrollTop = this.chatBox.scrollHeight;
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
    new NutritionForm();
    new ChatInterface();
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
    static token = null;

    static async login(username, password) {
        const response = await fetch(`${API_URL}/token`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: new URLSearchParams({
                username: username,
                password: password
            })
        });

        if (!response.ok) {
            throw new Error('Login failed');
        }

        const data = await response.json();
        this.token = data.access_token;
        localStorage.setItem('token', this.token);
        return this.token;
    }

    static async register(formData) {
        const response = await fetch(`${API_URL}/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        if (!response.ok) {
            throw new Error('Registration failed');
        }

        return await response.json();
    }

    static getToken() {
        if (!this.token) {
            this.token = localStorage.getItem('token');
        }
        return this.token;
    }

    static logout() {
        this.token = null;
        localStorage.removeItem('token');
        window.location.href = 'index.html';
    }
}
