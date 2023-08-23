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

    // When self joins
    channel.bind("pusher:subscription_succeeded", (members) => {
        console.log("pusher:subscription_succeeded")

        playersWaiting = members.count
        pWaitingPlayers.textContent = `Waiting for ${totalPlayers - playersWaiting} player(s)`
        
        if (playersWaiting === totalPlayers && isHost) {
            roundReadyState()
        }
    });

    // When another player joins
    channel.bind('pusher:member_added', (member) => {
        console.log('pusher:member_added', member.id)

        playersWaiting += 1
        pWaitingPlayers.textContent = `Waiting for ${totalPlayers - playersWaiting} player(s)`

        if (playersWaiting === totalPlayers && isHost) {
            roundReadyState()
        }

    });

    channel.bind('client-end-round', (data) => {
        console.log('client-end-round')
        console.log(data)

        redirectWithPost('party_round_answer', data)
    });


    function roundReadyState() {
        let playersRoundData = null

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
            console.log(data)
            playersRoundData = data
        })
        .catch(error => {
            console.error("Error fetching round data:", error.message);
            console.log("Full error:", error);
            });


        channel.trigger('client-end-round', {
            data: playersRoundData
        });

    }

    function redirectWithPost(url, data) {
        console.log("redirect with post")

        // Create a form dynamically
        const form = document.createElement('form');
        form.method = 'post';
        form.action = url;
    
        // Add the data to the form
        for (const key in data) {
            if (data.hasOwnProperty(key)) {
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = key;
                input.value = data[key];
                form.appendChild(input);
            }
        }
    
        // Append the form to the body and submit it
        document.body.appendChild(form);
        // form.submit();
    }
});