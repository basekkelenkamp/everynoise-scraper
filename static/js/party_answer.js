document.addEventListener("DOMContentLoaded", function() {

    const end = document.getElementById('end');
    console.log(end)

    if (end === null) {
        console.log('Start timer!')

        const seconds = 15;
        const interval = 30;
        const steps = (seconds * 1000) / interval;

        const loadingBar = document.createElement('div');
        loadingBar.style.width = '0%';
        loadingBar.style.height = '5px';
        loadingBar.style.background = '#0073ff';
        loadingBar.style.position = 'fixed';
        loadingBar.style.bottom = '0';
        loadingBar.style.left = '0';
        document.body.appendChild(loadingBar);

        let width = 0;
        const timer = setInterval(function() {
            if (width >= 100) {
                clearInterval(timer);
                redirectWithPost('guess');
            } else {
                width += 100 / steps; 
                loadingBar.style.width = width + '%';
            }
        }, interval);
    }

    if (end !== null) {
        console.log('End of the game!')
    
        // Get the first li element
        const firstLi = document.querySelector('li');
    
        if (firstLi) {
            // Set the initial border style with a transparent color
            firstLi.style.border = '5px solid transparent';
    
            // Create a keyframe animation to alternate the border color
            const keyframes = `
                @keyframes dashedBorder {
                    0%, 100% { border-color: transparent; }
                    50% { border-color: green; }
                }
            `;
    
            // Append the keyframes to the document's styles
            const styleSheet = document.createElement('style');
            styleSheet.type = 'text/css';
            styleSheet.innerHTML = keyframes;
            document.head.appendChild(styleSheet);
    
            // Apply the animation to the first li element
            firstLi.style.animation = 'dashedBorder 0.8s linear infinite';
        }
    }
        

    function redirectWithPost(url) {
        console.log("redirect with post");
    
        // Create a form dynamically
        const form = document.createElement('form');
        form.method = 'post';
        form.action = url;
    
        document.body.appendChild(form);
        form.submit();
    }


});