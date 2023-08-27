function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

document.addEventListener("DOMContentLoaded", function() {
    const partyCode = getCookie("party_code");

    if (partyCode) {
        console.log('Start timer!');
        const form = document.querySelector('.guess-form');

        const seconds = 90;
        const interval = 30;
        const steps = (seconds * 1000) / interval;

        // Create loading bar
        const loadingBar = document.createElement('div');
        loadingBar.style.width = '0%';
        loadingBar.style.height = '15px';
        loadingBar.style.background = '#0073ff';
        loadingBar.style.position = 'fixed';
        loadingBar.style.bottom = '0';
        loadingBar.style.left = '0';
        document.body.appendChild(loadingBar);

        // Create timer counter
        const timerCounter = document.createElement('div');
        timerCounter.style.position = 'fixed';
        timerCounter.style.bottom = '0';
        timerCounter.style.left = '0';
        timerCounter.style.zIndex = '2';  // To display above loadingBar
        timerCounter.style.fontSize = '75%'
        timerCounter.innerHTML = seconds;
        document.body.appendChild(timerCounter);

        let width = 0;
        let remainingSeconds = seconds;
        const timer = setInterval(function() {
            if (width >= 100) {
                clearInterval(timer);
                form.submit();
            } else {
                width += 100 / steps; 
                loadingBar.style.width = width + '%';
            }
        }, interval);

        // Timer to update second counter
        const secondTimer = setInterval(function() {
            if (remainingSeconds > 0) {
                remainingSeconds--;
                timerCounter.innerHTML = remainingSeconds + 's';
            } else {
                clearInterval(secondTimer);
            }
        }, 1000);
    }
});
