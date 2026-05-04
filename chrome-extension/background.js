chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message?.type === 'sendWebhook' && message.url) {
        const webhook = 'http://localhost:5000/ingest/pdf?train=false';

        fetch(webhook, {
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
        const generateUrl = 'http://localhost:5000/generate';

        fetch(generateUrl, {
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
    }
});