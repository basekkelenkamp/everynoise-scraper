let audioPlayer = new Audio();
audioPlayer.crossOrigin = "anonymous";

let playing = false;
let artistUrl;
let context = new (window.AudioContext || window.webkitAudioContext)();
let analyser = context.createAnalyser();
let src;
let isVisualizerInitialized = false;

window.onload = function() {
    let d = document.getElementById("audioSelector");
    artistUrl = d.dataset.artisturl;
    console.log(artistUrl);
}

let volume = document.getElementById('volume-slider');
volume.addEventListener("input", function(e) {
    let minVolume = 0.01;  // To avoid Math.log(0)
    let maxVolume = 1;
    let scaledVolume = (e.currentTarget.value / 100) * (Math.log(maxVolume / minVolume)) + Math.log(minVolume);
    audioPlayer.volume = Math.exp(scaledVolume);
});

function audioHandler() {
    let play = document.getElementById("player-button");
    if (!playing) {
        playing = true;
        playMusic(artistUrl);
        play.src = 'static/images/pause.png';
        if (!isVisualizerInitialized) {
            initVisualizer();
            isVisualizerInitialized = true;
        }
    } else {
        playing = false;
        stopMusic();
        play.src = 'static/images/play.png';
    }
}

function playMusic(audio) {
    if (audio === null) {
        console.log("No preview available");
        return;
    }
    audioPlayer.pause();
    audioPlayer.src = audio;
    audioPlayer.load();
    audioPlayer.play();
    console.log("audio playing");
}

function stopMusic() {
    audioPlayer.pause();
    audioPlayer.src = "";
    console.log("audio stopped");
}

function initVisualizer() {
    src = context.createMediaElementSource(audioPlayer);
    var canvas = document.getElementById("visualizer");
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    var ctx = canvas.getContext("2d");

    src.connect(analyser);
    analyser.connect(context.destination);

    analyser.fftSize = 256;
    var bufferLength = analyser.frequencyBinCount;
    var dataArray = new Uint8Array(bufferLength);

    var WIDTH = canvas.width;
    var HEIGHT = canvas.height;
    var barWidth = (WIDTH / bufferLength) * 2.5;
    var barHeight;
    var x = 0;

    let startColor = randomRGB();
    let endColor = randomRGB();

    function renderFrame() {
        requestAnimationFrame(renderFrame);
        x = 0;
        
        ctx.clearRect(0, 0, WIDTH, HEIGHT);
    
        analyser.getByteFrequencyData(dataArray);
    
        for (var i = 0; i < bufferLength; i++) {
            barHeight = dataArray[i];
            let color = interpolateColor(startColor, endColor, i / bufferLength);
            ctx.fillStyle = `rgb(${color.r}, ${color.g}, ${color.b})`;
            ctx.fillRect(x, HEIGHT - barHeight, barWidth, barHeight);
            x += barWidth + 1;
        }
    }
    renderFrame();
}


function randomRGB() {
    return {
        r: Math.floor(Math.random() * 256),
        g: Math.floor(Math.random() * 256),
        b: Math.floor(Math.random() * 256)
    };
}

function interpolateColor(color1, color2, factor) {
    const r = Math.round(color1.r + (color2.r - color1.r) * factor);
    const g = Math.round(color1.g + (color2.g - color1.g) * factor);
    const b = Math.round(color1.b + (color2.b - color1.b) * factor);
    return { r, g, b };
}
