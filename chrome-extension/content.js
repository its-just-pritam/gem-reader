// Constants
let modalShown = false;
let botEnabled = true; // This can be toggled based on user preferences

// Function to check if the current page is a PDF
function isPDF() {
    return window.location.href.includes(".pdf") ||
           document.contentType === "application/pdf" ||
           window.location.pathname.endsWith('.pdf');
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
    modal.id = "deep-reader-popup";
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
        <div style="margin-bottom: 10px; font-weight: bold; color: #333;">DeepReader: PDF! 📖</div>
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
    document.getElementById('init-eb-yes').onclick = async () => {
        await sendPdfUrlToWebhook(window.location.href);
        alert("Started Analysis..."); // Replace with your logic
        modal.remove();
    };
    document.getElementById('init-eb-no').onclick = () => modal.remove();
}

// Function to create and inject the follow-up modal
function showFollowUpModal() {
    const modal = document.createElement('div');
    modal.id = "deep-reader-followup";
    modal.style.cssText = `
        position: fixed;
        bottom: 30px;
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
        <div style="margin-bottom: 10px; font-weight: bold; color: #333;">DeepReader: Deep Dive detected! 📚</div>
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
        alert("Analyzing..."); // Replace with your logic
        modal.remove();
    };
    document.getElementById('followup-eb-no').onclick = () => modal.remove();
}

// Main initialization
if (isPDF()) {
    console.log("PDF detected. Tracking scroll depth...");
    createInitialModal();

    setTimeout(() => {
        if (!modalShown) {
            modalShown = true;
            const initialModal = document.getElementById('deep-reader-popup');
            if (initialModal) initialModal.remove();
            showFollowUpModal();
        }
    }, 60000);
}