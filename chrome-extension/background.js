chrome.action.onClicked.addListener((tab) => {
    // When the extension icon is clicked, send a message to the content script in the active tab
    if (tab.id) {
        chrome.tabs.sendMessage(tab.id, { type: 'openChatModal' });
    }
});

/**
 * Configuration management
 * The backend URL is retrieved from the manifest. Custom fields in manifest are accessible,
 * but we provide a fallback for local development.
 */
const getBackendUrl = () => {
    // Custom keys like 'backend_url' are disallowed in Manifest V3.
    // We define the URL here directly. For a professional setup, 
    // you might swap this using a build tool or an environment flag.
    const PRODUCTION_URL = 'https://gem-reader-backend-649289288067.asia-south1.run.app';
    return PRODUCTION_URL;
};

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message?.type === 'sendWebhook' && message.url) {
        const endpoint = new URL('/ingest/pdf', getBackendUrl());
        endpoint.searchParams.append('train', 'false');

        fetch(endpoint.toString(), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ url: message.url })
        })
        .then((response) => {
            if (!response.ok) {
                throw new Error(`${response.status} ${response.statusText}`);
            }
            return response.json(); // Changed to return JSON response
        })
        .then((data) => sendResponse({ success: true, data: data })) // Send data back to content.js
        .catch((error) => {
            console.error('Background webhook request failed:', error);
            sendResponse({ success: false, error: error.message });
        });

        return true; // Keep the message channel open for async response
    } else if (message?.type === 'sendChatQuery' && message.query) {
        const endpoint = new URL('/generate', getBackendUrl());

        fetch(endpoint.toString(), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                queries: [message.query],
                url: message.pdfUrl // Optional: allows backend to filter by the current PDF
            })
        })
        .then((response) => {
            if (!response.ok) {
                throw new Error(`${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then((data) => {
            const answer = data.results && data.results.length > 0 ? data.results[0].answer : "No answer found.";
            sendResponse({ success: true, answer: answer });
        })
        .catch((error) => {
            console.error('Chat generation request failed:', error);
            sendResponse({ success: false, error: error.message });
        });

        return true; // Keep the message channel open for async response
    } else if (message?.type === 'getChatHistory' && message.url) {
        const endpoint = new URL('/chat/history', getBackendUrl());
        endpoint.searchParams.append('url', message.url);

        fetch(endpoint.toString())
        .then((response) => {
            if (!response.ok) {
                throw new Error(`${response.status} ${response.statusText}`);
            }
            return response.json();
        })
        .then((data) => {
            sendResponse(data);
        })
        .catch((error) => {
            console.error('Chat history fetch failed:', error);
            sendResponse({ success: false, error: error.message });
        });

        return true; // Keep the message channel open for async response
    }
});