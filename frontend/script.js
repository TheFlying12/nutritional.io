// For index.html: Form submission logic
if (document.getElementById("nutrition-form")) {
    const form = document.getElementById("nutrition-form");

    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        // Collect form data
        const formData = {
            name: document.getElementById("name").value,
            age: document.getElementById("age").value,
            height: document.getElementById("height").value,
            weight: document.getElementById("weight").value,
            goal: document.getElementById("goal").value,
            planType: document.getElementById("plan-type").value,
            currentDiet: document.getElementById("current-diet").value || "",
        };

        // Call backend to generate meal plan
        const response = await fetch("http://127.0.0.1:8000/generate-meal-plan", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(formData),
        });

        const mealPlan = await response.text();

        // Store meal plan and navigate to chat page
        localStorage.setItem("mealPlan", mealPlan);
        window.location.href = "chatpage.html";
    });
}

// For chat.html: Chat page logic
if (document.getElementById("chat-box")) {
    const chatBox = document.getElementById("chat-box");
    const userMessageInput = document.getElementById("user-message");
    const sendMessageButton = document.getElementById("send-message");

    // Load initial meal plan
    const mealPlan = localStorage.getItem("mealPlan");
    if (mealPlan) {
        const message = document.createElement("div");
        message.classList.add("chat-message");
        message.textContent = mealPlan;
        chatBox.appendChild(message);
    }

    let conversation = [
        { role: "assistant", content: mealPlan },
    ];

    // Handle user follow-up messages
    sendMessageButton.addEventListener("click", async () => {
        const userMessage = userMessageInput.value;
        if (!userMessage) return;

        // Add user message to chat
        const userDiv = document.createElement("div");
        userDiv.classList.add("chat-message");
        userDiv.textContent = `You: ${userMessage}`;
        chatBox.appendChild(userDiv);

        conversation.push({ role: "user", content: userMessage });
        userMessageInput.value = "";

        // Send user message to backend
        const response = await fetch("http://127.0.0.1:8000/follow-up", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ conversation }),
        });

        const data = await response.text();

        // Add backend response to chat
        const assistantDiv = document.createElement("div");
        assistantDiv.classList.add("chat-message");
        assistantDiv.textContent = `Assistant: ${data.response}`;
        chatBox.appendChild(assistantDiv);

        conversation.push({ role: "assistant", content: data });
    });
}
