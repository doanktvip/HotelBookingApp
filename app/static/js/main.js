/* Các hàm javascript xử lý Thông báo */
let cachedAlertTemplate = null;

function getAlertTemplate() {
    if (cachedAlertTemplate !== null) return cachedAlertTemplate;
    const template = document.getElementById('alert-macro-template');
    cachedAlertTemplate = template ? template.innerHTML : '';
    return cachedAlertTemplate;
}

function buildAlertHtml(message, category, expires) {
    let rawHtml = getAlertTemplate();
    if (!rawHtml) return '';

    rawHtml = rawHtml.replace('__MSG_PLACEHOLDER__', message);
    rawHtml = rawHtml.replace('__CAT_PLACEHOLDER__', category);

    const tempWrap = document.createElement('div');
    tempWrap.innerHTML = rawHtml.trim();
    const alertElement = tempWrap.firstChild;

    if (expires) {
        alertElement.dataset.expires = expires;
    }

    return alertElement.outerHTML;
}

function setAlertTimer(alertEl) {
    if (alertEl.dataset.timer) return;

    const now = Date.now();
    let expires = alertEl.dataset.expires;

    if (!expires) {
        expires = now + 3000;
        alertEl.dataset.expires = expires;
    }

    const remainingTime = expires - now;

    if (remainingTime <= 0) {
        alertEl.remove();
    } else {
        const timer = setTimeout(function () {
            if (typeof bootstrap !== 'undefined') {
                const bsAlert = bootstrap.Alert.getOrCreateInstance(alertEl);
                bsAlert.close();
            } else {
                alertEl.remove();
            }
        }, remainingTime);
        alertEl.dataset.timer = timer;
    }
}

function initAutoCloseAlerts() {
    const alerts = document.querySelectorAll('.auto-hide-alert');
    alerts.forEach(setAlertTimer);
}

function loadSessionAlerts() {
    const pendingAlerts = JSON.parse(sessionStorage.getItem('staynow_alerts') || '[]');
    if (pendingAlerts.length === 0) return;

    const container = document.getElementById('alert-container');
    if (!container) return;

    const now = Date.now();
    let batchHtml = '';

    pendingAlerts.forEach(alert => {
        if (alert.expires && now < alert.expires) {
            batchHtml += buildAlertHtml(alert.message, alert.category, alert.expires);
        }
    });

    if (batchHtml !== '') {
        container.insertAdjacentHTML('beforeend', batchHtml);
        initAutoCloseAlerts();
    }

    sessionStorage.removeItem('staynow_alerts');
}

function showToastAlert(message, category = 'danger') {
    const container = document.getElementById('alert-container');
    if (!container) return;

    const expires = Date.now() + 3000;
    const alertHtml = buildAlertHtml(message, category, expires);

    container.insertAdjacentHTML('beforeend', alertHtml);
    const newAlert = container.lastElementChild;

    if (newAlert && newAlert.classList.contains('auto-hide-alert')) {
        setAlertTimer(newAlert);
    }
}

window.addEventListener('beforeunload', function () {
    const container = document.getElementById('alert-container');
    if (container) {
        const activeAlerts = [];
        const alerts = container.querySelectorAll('.auto-hide-alert');

        alerts.forEach(function(alertEl) {
            let category = 'info';
            alertEl.classList.forEach(c => {
                if (c.startsWith('alert-') && c !== 'alert-dismissible') {
                    category = c.replace('alert-', '');
                }
            });

            let message = '';
            const textEl = alertEl.querySelector('.alert-text');
            if (textEl) {
                message = textEl.textContent.trim();
            } else {
                alertEl.childNodes.forEach(node => {
                    if (node.nodeType === Node.TEXT_NODE) {
                        message += node.textContent;
                    }
                });
                message = message.trim();
            }

            const expires = alertEl.dataset.expires;
            activeAlerts.push({ message, category, expires });
        });

        if (activeAlerts.length > 0) {
            sessionStorage.setItem('staynow_alerts', JSON.stringify(activeAlerts));
        }
    }
});

document.addEventListener('DOMContentLoaded', function () {
    loadSessionAlerts();
    initAutoCloseAlerts();
});