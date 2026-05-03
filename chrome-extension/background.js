chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message?.type === 'sendWebhook' && message.url) {
        const webhook = 'https://webhook.site/c3426fc0-1d7d-4a91-8ab1-37c7a862e5af';

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
            return response.text();
        })
        .then(() => sendResponse({ success: true }))
        .catch((error) => {
            console.error('Background webhook request failed:', error);
            sendResponse({ success: false, error: error.message });
        });

        return true; // Keep the message channel open for async response
    }
});