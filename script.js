// Shared utilities
const API_BASE_URL = 'http://127.0.0.1:8000';

// Helper functions
function createMessageElement(text, className = '') {
    const div = document.createElement('div');
    div.classList.add('chat-message', className);
    div.textContent = text;
    return div;
}

async function makeApiRequest(endpoint, data) {
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status} - ${await response.text()}`);
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
            console.log('Received response:', response); // Log the entire response
            
            if (!response.mealPlan) {
                throw new Error('No meal plan in response');
            }
            
            localStorage.setItem('mealPlan', response.mealPlan);
            window.location.href = 'chatpage.html';
        } catch (error) {
            console.error('Form submission error:', error);
            throw error; // Re-throw to trigger the error handling in initializeForm
        }
    }
}

// Chat handling (chat.html)
class ChatInterface {
    constructor() {
        this.chatBox = document.getElementById('chat-box');
        this.userMessageInput = document.getElementById('user-message');
        this.sendMessageButton = document.getElementById('send-message');
        
        if (this.chatBox) {
            this.initializeChat();
        }
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