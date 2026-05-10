// Constants
let modalShown = false;
let botEnabled = true; // This can be toggled based on user preferences

// Function to check if the current page is a PDF
function isPDF() {
    return window.location.href.includes(".pdf") ||
           document.contentType === "application/pdf" ||
           window.location.pathname.endsWith('.pdf');
}

/**
 * A lightweight markdown parser to convert basic MD syntax to HTML.
 * Handles headers, bold, italics, code snippets, and simple lists.
 */
function formatMarkdown(text) {
    if (!text) return "";
    return text
        // Headers (using smaller heading tags for the chat UI)
        .replace(/^### (.*$)/gim, '<h4 style="margin: 8px 0 4px; color: #333;">$1</h4>')
        .replace(/^## (.*$)/gim, '<h5 style="margin: 10px 0 5px; color: #333;">$1</h5>')
        .replace(/^# (.*$)/gim, '<h6 style="margin: 12px 0 6px; color: #333;">$1</h6>')
        // Formatting
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        // Code and Lists
        .replace(/`(.*?)`/g, '<code style="background: rgba(0,0,0,0.05); padding: 2px 4px; border-radius: 3px; font-family: monospace;">$1</code>')
        .replace(/^\s*[\-\*]\s+(.*)$/gim, '<div style="display: list-item; list-style-type: disc; margin-left: 20px; margin-bottom: 4px;">$1</div>')
        // Line breaks
        .replace(/\n/g, '<br>');
}

// Sends the current PDF URL to the webhook through the extension background worker
function sendPdfUrlToWebhook(pdfUrl) {
    return new Promise((resolve) => {
        chrome.runtime.sendMessage(
            { type: 'sendWebhook', url: pdfUrl },
            (response) => {
                if (!response || !response.success) {
                    console.warn('Webhook request failed:', response?.error || 'no response');
                }
                resolve(response);
            }
        );
    });
}

// Function to create and set up the initial PDF detection modal
function createInitialModal() {
    const modal = document.createElement('div');
    modal.id = "gem-reader-popup";
    modal.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        width: 280px;
        padding: 20px;
        background: #ffffff;
        border-left: 5px solid #4A90E2;
        box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        z-index: 1000000;
        border-radius: 4px;
        font-family: sans-serif;
    `;

    modal.innerHTML = `
        <div style="margin-bottom: 10px; font-weight: bold; color: #333;">Gem Reader: PDF! 📖</div>
        <div style="font-size: 13px; color: #666; margin-bottom: 15px;">
            I have detected that you're viewing a PDF. I can help you summarize the content as you read - please open the extension and get started!
        </div>
        <div style="display: flex; gap: 10px;">
            <button id="init-eb-yes" style="flex: 1; padding: 8px; background: #4A90E2; color: white; border: none; border-radius: 4px; cursor: pointer;">Start Analysis</button>
            <button id="init-eb-no" style="flex: 1; padding: 8px; background: #eee; color: #333; border: none; border-radius: 4px; cursor: pointer;">Ignore</button>
        </div>
    `;

    document.body.appendChild(modal);

    // Button Listeners
    document.getElementById('init-eb-yes').onclick = async () => { // Changed to async
        const response = await sendPdfUrlToWebhook(window.location.href);
        if (response && response.success) {
            modal.remove(); // Remove initial modal
            modalShown = true; // Set modalShown to true to prevent follow-up modal
            createChatModal(window.location.href); // Pass current PDF URL to chat modal
        } else {
            alert("Failed to start analysis: " + (response?.error || "Unknown error"));
        }
    };
    document.getElementById('init-eb-no').onclick = () => modal.remove();
}

// Function to create and inject the follow-up modal
function showFollowUpModal() {
    const modal = document.createElement('div');
    modal.id = "gem-reader-followup";
    modal.style.cssText = `
        position: fixed;
        bottom: 10px;
        right: 30px;
        width: 280px;
        padding: 20px;
        background: #ffffff;
        border-left: 5px solid #4A90E2;
        box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        z-index: 1000000;
        border-radius: 4px;
        font-family: sans-serif;
    `;

    modal.innerHTML = `
        <div style="margin-bottom: 10px; font-weight: bold; color: #333;">Gem Reader: Deep Dive detected! 📚</div>
        <div style="font-size: 13px; color: #666; margin-bottom: 15px;">
            You have spent some time on the PDF. Would you like a summary of the key concepts covered so far?
        </div>
        <div style="display: flex; gap: 10px;">
            <button id="followup-eb-yes" style="flex: 1; padding: 8px; background: #4A90E2; color: white; border: none; border-radius: 4px; cursor: pointer;">Analyze</button>
            <button id="followup-eb-no" style="flex: 1; padding: 8px; background: #eee; color: #333; border: none; border-radius: 4px; cursor: pointer;">Ignore</button>
        </div>
    `;

    document.body.appendChild(modal);

    // Button Listeners
    document.getElementById('followup-eb-yes').onclick = async () => {
        await sendPdfUrlToWebhook(window.location.href);
        // alert("Analyzing..."); // Replace with your logic
        modal.remove();
    };
    document.getElementById('followup-eb-no').onclick = () => modal.remove();
}

// Function to create and inject the chat modal
function createChatModal(pdfUrl) {
    const chatModal = document.createElement('div');
    chatModal.id = "gem-reader-chat-modal";
    chatModal.style.cssText = `
        position: fixed;
        bottom: 20px;
        right: 30px;
        width: 400px;
        height: 700px;
        background: #ffffff;
        border: 1px solid #ddd;
        box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        z-index: 1000001;
        border-radius: 8px;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        font-size: 13px;
        display: flex;
        flex-direction: column;
        overflow: hidden;
    `;

    chatModal.innerHTML = `
        <div style="padding: 15px; background: #4A90E2; color: white; font-size: 16px; font-weight: bold; border-top-left-radius: 8px; border-top-right-radius: 8px; display: flex; justify-content: space-between; align-items: center;">
            Gem Reader Chat 💬
            <button id="close-chat-modal" style="background: none; border: none; color: white; font-size: 18px; cursor: pointer;">&times;</button>
        </div>
        <div id="chat-messages" style="flex-grow: 1; padding: 15px; overflow-y: auto; background: #f9f9f9; border-bottom: 1px solid #eee;">
            <div style="margin-bottom: 10px; padding: 8px; background: #e0f7fa; border-radius: 5px;">
                Hello! I'm your Gem Reader assistant. Ask me anything about this PDF.
            </div>
        </div>
        <div style="padding: 15px; display: flex; border-top: 1px solid #eee;">
            <input type="text" id="chat-input" placeholder="Ask a question..." style="flex-grow: 1; padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin-right: 10px; font-size: 13px; font-family: inherit;">
            <button id="send-chat-message" style="padding: 10px 15px; background: #4A90E2; color: white; border: none; border-radius: 5px; cursor: pointer;">Send</button>
        </div>
    `;

    document.body.appendChild(chatModal);

    document.getElementById('close-chat-modal').onclick = () => chatModal.remove();

    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-chat-message');
    const chatMessages = document.getElementById('chat-messages');

    async function sendMessage() {
        const query = chatInput.value.trim();
        if (!query) return;

        // Display user message
        const userMessageDiv = document.createElement('div');
        userMessageDiv.style.cssText = 'margin-bottom: 10px; padding: 8px; background: #dcf8c6; border-radius: 5px; text-align: right;';
        userMessageDiv.textContent = query;
        chatMessages.appendChild(userMessageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight; // Scroll to bottom

        chatInput.value = ''; // Clear input

        // Display loading indicator
        const loadingDiv = document.createElement('div');
        loadingDiv.id = 'loading-indicator';
        loadingDiv.style.cssText = 'margin-bottom: 10px; padding: 8px; background: #f0f0f0; border-radius: 5px;';
        loadingDiv.innerHTML = 'Gem Reader is thinking<span class="loading-dots">.</span>'; // Simple loading animation
        chatMessages.appendChild(loadingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        let dots = 0;
        const loadingInterval = setInterval(() => {
            dots = (dots + 1) % 4;
            loadingDiv.querySelector('.loading-dots').textContent = '.'.repeat(dots);
        }, 300);

        try {
            const response = await chrome.runtime.sendMessage({
                type: 'sendChatQuery',
                query: query,
                pdfUrl: pdfUrl // Pass the current PDF URL
            });

            clearInterval(loadingInterval); // Stop loading animation
            loadingDiv.remove(); // Remove loading indicator

            const botMessageDiv = document.createElement('div');
            botMessageDiv.style.cssText = 'margin-bottom: 10px; padding: 8px; background: #e0f7fa; border-radius: 5px;';
            if (response && response.success && response.answer) {
                botMessageDiv.innerHTML = formatMarkdown(response.answer);
            } else {
                botMessageDiv.textContent = "Sorry, I couldn't get an answer. " + (response?.error || "Please try again.");
            }
            chatMessages.appendChild(botMessageDiv);
        } catch (error) {
            clearInterval(loadingInterval); // Stop loading animation
            loadingDiv.remove(); // Remove loading indicator
            const errorMessageDiv = document.createElement('div');
            errorMessageDiv.style.cssText = 'margin-bottom: 10px; padding: 8px; background: #ffebee; color: #d32f2f; border-radius: 5px;';
            errorMessageDiv.textContent = `Error: ${error.message}`;
            chatMessages.appendChild(errorMessageDiv);
        }
        chatMessages.scrollTop = chatMessages.scrollHeight; // Scroll to bottom again
    }

    sendButton.onclick = sendMessage;
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });
}

// Main initialization
if (isPDF()) {
    console.log("PDF detected. Tracking scroll depth...");
    createInitialModal();

    // This timeout will now only trigger the follow-up modal if the initial modal was ignored.
    // If "Start Analysis" is clicked, modalShown is set to true, preventing this.
    setTimeout(() => { 
        if (!modalShown) {
            modalShown = true;
            const initialModal = document.getElementById('gem-reader-popup');
            if (initialModal) initialModal.remove();
            showFollowUpModal();
        }
    }, 60000); // 1 minute
}