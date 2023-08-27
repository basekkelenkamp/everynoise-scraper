document.addEventListener("DOMContentLoaded", function() {

    const partyCode = document.getElementById('party-code').value;
    const pusherKey = document.getElementById('pusher-key').value;

    const playerId = document.getElementById("player-id").value
    const roundId = document.getElementById("round-id").value
    const guess = document.getElementById("guess").value
    const isHost = document.getElementById('is-host').value === 'True' ? true : false;
    const totalPlayers = parseInt(document.getElementById("total-players").value)

    console.log(playerId, guess, isHost)
    console.log("totalPlayers", totalPlayers)

    let pWaitingPlayers = document.querySelector(".waiting-players")

    const pusher = new Pusher(pusherKey, {
        cluster: 'eu',
        authEndpoint: '/pusher/auth'
    });

    const channel = pusher.subscribe(`presence-${partyCode}`)

    let playersWaiting = 0;
    let roundReadyTimeout;
    let forceStartAfterSeconds = 120;

    // When self joins
    channel.bind("pusher:subscription_succeeded", (members) => {
        console.log("pusher:subscription_succeeded")

        playersWaiting = members.count
        pWaitingPlayers.textContent = `Waiting for ${totalPlayers - playersWaiting} player(s)`
        
        if (playersWaiting === totalPlayers && isHost) {
            roundReadyState();
        } else if (isHost) {
            // Start the 120-second timer
            roundReadyTimeout = setTimeout(() => {
                roundReadyState();
            }, forceStartAfterSeconds * 1000);
        }
        });

    // When another player joins
    channel.bind('pusher:member_added', (member) => {
        console.log('pusher:member_added', member.id)

        playersWaiting += 1
        pWaitingPlayers.textContent = `Waiting for ${totalPlayers - playersWaiting} player(s)`

        if (playersWaiting === totalPlayers && isHost) {
            clearTimeout(roundReadyTimeout);
            roundReadyState();
            }

    });

    channel.bind('client-end-round', (data) => {
        console.log('client-end-round')
        redirectWithPost('party_round_answer', data.data)
    });


    function roundReadyState() {
        fetch('/get_round_party_data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                roundId: roundId,

             })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })        
        .then(data => {
            channel.trigger('client-end-round', {
                data: data
            });

            setTimeout(function() {
                redirectWithPost('party_round_answer', data);
            }, 500);

        })
        .catch(error => {
            console.error("Error fetching round data:", error.message);
            console.log("Full error:", error);
            });
    }

    function redirectWithPost(url, data) {
        console.log("redirect with post");
        console.log(data);
    
        // Create a form dynamically
        const form = document.createElement('form');
        form.method = 'post';
        form.action = url;
    
        // Add the 'answer' data
        const answerInput = document.createElement('input');
        answerInput.type = 'hidden';
        answerInput.name = 'answer';
        answerInput.value = data.answer;
        form.appendChild(answerInput);
    
        // Add the player data as hidden inputs with IDs based on player names
        for (const player of data.players) {
            const playerName = player.player_name;  // Extract player's name
            const playerData = player;
    
            for (const key in playerData) {
                if (playerData.hasOwnProperty(key)) {
                    const input = document.createElement('input');
                    input.type = 'hidden';
                    input.name = `${playerName}.${key}`;
                    input.value = playerData[key];
                    form.appendChild(input);
                }
            }
        }
    
        document.body.appendChild(form);
        form.submit();
    }
});