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
 * Creates a copy button for chat responses with visual feedback.
 */
function createCopyButton(textToCopy) {
    const button = document.createElement('button');
    button.title = "Copy to clipboard";
    button.style.cssText = `
        position: absolute; bottom: 5px; left: 5px; background: #fff; border: 1px solid #ddd;
        border-radius: 4px; cursor: pointer; padding: 4px; display: flex; align-items: center;
        justify-content: center; opacity: 0; transition: opacity 0.2s; z-index: 10;
    `;
    const copyIcon = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#666" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>`;
    const checkIcon = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#4caf50" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>`;
    
    button.innerHTML = copyIcon;
    button.onclick = () => {
        navigator.clipboard.writeText(textToCopy).then(() => {
            button.innerHTML = checkIcon;
            setTimeout(() => button.innerHTML = copyIcon, 2000);
        });
    };

    return button;
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
        border-left: 5px solid #c6384b;
        box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        z-index: 1000000;
        border-radius: 4px;
        font-family: Inter;
    `;

    modal.innerHTML = `
        <span style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px; font-size: 16px; font-weight: bold; color: #c6384b;">
            <img src="${chrome.runtime.getURL('icons48.png')}" alt="Gem Reader" style="width: 24px; height: 24px;"> Gem Reader
        </span>
        <div style="font-size: 13px; color: #666; margin-bottom: 15px;">
            I have detected that you're viewing a PDF. I can help you summarize the content as you read - please open the extension and get started!
        </div>
        <div style="display: flex; gap: 10px;">
            <button id="init-eb-yes" style="flex: 1; padding: 8px; background: #c6384b; color: white; border: none; border-radius: 4px; cursor: pointer;">Start Analysis</button>
            <button id="init-eb-no" style="flex: 1; padding: 8px; background: #eee; color: #333; border: none; border-radius: 4px; cursor: pointer;">Ignore</button>
        </div>
    `;

    document.body.appendChild(modal);

    // Button Listeners
    document.getElementById('init-eb-yes').onclick = async () => {
        const description = modal.querySelector('div');
        const buttonContainer = modal.querySelector('div:last-of-type');
        
        // Hide existing UI elements
        description.style.display = 'none';
        buttonContainer.style.display = 'none';

        // Show loading screen
        const loadingContainer = document.createElement('div');
        loadingContainer.style.cssText = 'text-align: center; padding: 10px;';
        loadingContainer.innerHTML = `
            <div style="border: 3px solid #f3f3f3; border-top: 3px solid #c6384b; border-radius: 50%; width: 24px; height: 24px; animation: modal-spin 1s linear infinite; margin: 0 auto 10px;"></div>
            <div style="font-size: 13px; color: #666;">Analyzing document</div>
            <style>@keyframes modal-spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }</style>
        `;
        modal.appendChild(loadingContainer);

        const response = await sendPdfUrlToWebhook(window.location.href);
        if (response && response.success) {
            modal.remove();
            markIngested();
            modalShown = true;
            createChatModal(window.location.href);
        } else {
            // Restore UI on failure
            loadingContainer.remove();
            description.style.display = 'block';
            buttonContainer.style.display = 'flex';
            alert("Failed to start analysis: " + (response?.error || "Unknown error"));
        }
    };
    document.getElementById('init-eb-no').onclick = () => modal.remove();
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
        font-family: Inter;
        font-size: 13px;
        display: flex;
        flex-direction: column;
        overflow: hidden;
    `;

    chatModal.innerHTML = `
        <div style="padding: 15px; background: #c6384b; color: white; font-size: 16px; font-weight: bold; border-top-left-radius: 8px; border-top-right-radius: 8px; display: flex; justify-content: space-between; align-items: center;">
            <span style="display: flex; align-items: center; gap: 8px;">
                <img src="${chrome.runtime.getURL('icons48.png')}" alt="Gem Reader" style="width: 24px; height: 24px;"> Gem Reader
            </span>
            <button id="close-chat-modal" style="background: none; border: none; color: white; font-size: 24px; cursor: pointer;">&times;</button>
        </div>
        <div id="chat-messages" style="flex-grow: 1; padding: 15px; overflow-y: auto; background: #f9f9f9; border-bottom: 1px solid #eee;">
            <div style="margin-bottom: 10px; padding: 8px; background: #edd9dc; border-radius: 5px;">
                Hello! I'm your personal assistant. Feel free to ask me anything about this PDF.
            </div>
        </div>
        <div style="padding: 15px; display: flex; border-top: 1px solid #eee;">
            <input type="text" id="chat-input" placeholder="Ask a question..." style="flex-grow: 1; padding: 10px; border: 1px solid #ddd; border-radius: 5px; margin-right: 10px; font-size: 13px; font-family: inherit;">
            <button id="send-chat-message" style="padding: 10px 15px; background: #c6384b; color: white; border: none; border-radius: 5px; cursor: pointer;">Send</button>
        </div>
    `;

    document.body.appendChild(chatModal);

    document.getElementById('close-chat-modal').onclick = () => chatModal.remove();

    const chatInput = document.getElementById('chat-input');
    const sendButton = document.getElementById('send-chat-message');
    const chatMessages = document.getElementById('chat-messages');

    // Fetch and display chat history for this PDF
    (async function loadHistory() {
        try {
            const historyResponse = await chrome.runtime.sendMessage({
                type: 'getChatHistory',
                url: pdfUrl
            });

            if (historyResponse && historyResponse.success && historyResponse.history) {
                historyResponse.history.forEach(item => {
                    // Add User Query
                    const userDiv = document.createElement('div');
                    userDiv.style.cssText = 'margin-bottom: 10px; padding: 8px; border-radius: 5px; text-align: right;';
                    userDiv.textContent = item.query;
                    chatMessages.appendChild(userDiv);

                    // Add Bot Response
                    const botDiv = document.createElement('div');
                    botDiv.style.cssText = 'margin-bottom: 20px; padding: 8px 8px 30px 8px; background: #edd9dc; border-radius: 5px; position: relative;';
                    botDiv.innerHTML = marked.parse(item.response);

                    const copyBtn = createCopyButton(item.response);
                    botDiv.onmouseenter = () => copyBtn.style.opacity = '1';
                    botDiv.onmouseleave = () => copyBtn.style.opacity = '0';
                    botDiv.appendChild(copyBtn);

                    chatMessages.appendChild(botDiv);
                });
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        } catch (err) {
            console.error("Error loading chat history:", err);
        }
    })();

    async function sendMessage() {
        const query = chatInput.value.trim();
        if (!query) return;

        // Display user message
        const userMessageDiv = document.createElement('div');
        userMessageDiv.style.cssText = 'margin-bottom: 10px; padding: 8px; border-radius: 5px; text-align: right;';
        userMessageDiv.textContent = query;
        chatMessages.appendChild(userMessageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight; // Scroll to bottom

        chatInput.value = ''; // Clear input

        // Display loading indicator
        const loadingDiv = document.createElement('div');
        loadingDiv.id = 'loading-indicator';
        loadingDiv.style.cssText = 'margin-bottom: 10px; padding: 8px; background: #edd9dc; border-radius: 5px;';
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
            botMessageDiv.style.cssText = 'margin-bottom: 20px; padding: 8px 8px 30px 8px; background: #edd9dc; border-radius: 5px; position: relative;';
            if (response && response.success && response.answer) {
                botMessageDiv.innerHTML = marked.parse(response.answer);
                
                const copyBtn = createCopyButton(response.answer);
                botMessageDiv.onmouseenter = () => copyBtn.style.opacity = '1';
                botMessageDiv.onmouseleave = () => copyBtn.style.opacity = '0';
                botMessageDiv.appendChild(copyBtn);

            } else {
                botMessageDiv.textContent = "Sorry, I couldn't get an answer. " + (response?.error || "Please try again.");
            }
            chatMessages.appendChild(botMessageDiv);
        } catch (error) {
            clearInterval(loadingInterval); // Stop loading animation
            loadingDiv.remove(); // Remove loading indicator
            const errorMessageDiv = document.createElement('div');
            errorMessageDiv.style.cssText = 'margin-bottom: 10px; padding: 8px; background: #edd9dc; color: #d32f2f; border-radius: 5px;';
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

// Listen for messages from the background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (!isPDF()) {
        createUnsupportedModal();
    } else if (message.type === 'openChatModal') {
        (async () => {
            const ingested = await isIngested();
            // Close initialModal if it's open
            const initialModal = document.getElementById('gem-reader-popup');
            if (initialModal) {
                initialModal.remove();
            }

            if (ingested && !document.getElementById('gem-reader-chat-modal')) {
                console.log("Document already ingested. Opening chat modal...");
                createChatModal(window.location.href);
            } else if (!ingested) {
                console.log("Document not ingested. Opening initial modal...");
                createInitialModal();
            }
        })();
    }
});

function createUnsupportedModal() {
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;    width: 280px;
        padding: 20px;
        background: #ffffff;
        border-left: 5px solid #c6384b;
        box-shadow: 0 10px 25px rgba(0,0,0,0.3);
        z-index: 1000000;
        border-radius: 4px;
        font-family: Inter;
    `;
    modal.innerHTML = `
        <span style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px; font-size: 16px; font-weight: bold; color: #c6384b;">
            <img src="${chrome.runtime.getURL('icons48.png')}" alt="Gem Reader" style="width: 24px; height: 24px;"> Gem Reader
        </span>
        <div style="font-size: 13px; color: #666;">
            Oops! This extension only works on PDF files.
        </div>
    `;
    document.body.appendChild(modal);
    setTimeout(() => modal.remove(), 5000); // Auto-remove after 5 seconds
}

function markIngested() {
    const key = window.location.href;
    const data = {
        ingested: "true",
        timestamp: Date.now() // Helpful for debugging/cache clearing
    };
    
    chrome.storage.local.set({ [key]: data }, () => {
        console.log(`Document marked as ingested: ${window.location.href}`);
    });
}

/**
 * Checks if the document is ingested by verifying the specific property
 */
function isIngested() {
    try {
        return new Promise((resolve) => {
            const key = window.location.href;
            chrome.storage.local.get([key], (result) => {
                const entry = result[key];
                // Returns true only if the entry exists and the property matches "true"
                resolve(!!(entry && entry.ingested === "true"));
            });
        });
    } catch (error) {
        console.error("Error checking if document is ingested:", error);
        return false;
    }
    
}

// Main initialization
if (isPDF()) {
    console.log("PDF detected. Tracking scroll depth...");
    (async () => {
        const ingested = await isIngested();
        if (ingested) {
            console.log("Document already ingested. Opening chat modal...");
            createChatModal(window.location.href);
        } else {
            console.log("Document not ingested. Opening initial modal...");
            createInitialModal();
        }
    })();
}