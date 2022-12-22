let audioPlayer = document.createElement('audio')
audioPlayer.id = 'audio'
audioPlayer.setAttribute("muted", "true")
document.body.appendChild(audioPlayer)

let playing = false

window.onload = function(){
    let d = document.getElementById("audioSelector")
    artistUrl = d.dataset.artisturl
    console.log(artistUrl)
}

function audioHandler() {
    console.log(artistUrl)
    let play = document.getElementById("player-button")
    if (!playing) {
        playing = true
        playMusic(artistUrl)
        play.src = 'static/images/pause.png'

    } else {
        playing = false
        stopMusic()
        play.src = 'static/images/play.png'
        }
}

function playMusic(audio) {
    if (audio === null) {
        console.log("No preview available")
        return
    }
    audioPlayer.pause()
    audioPlayer.src = audio
    audioPlayer.play()
    console.log("audio playing")
}

function stopMusic() {
    audioPlayer.pause()
    audioPlayer.src = ""
    console.log("audio stopped")
}