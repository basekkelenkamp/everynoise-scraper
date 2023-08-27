
function sanitizeInput(input) {
    return input.replace(/[^a-zA-Z0-9 !&*@?._\\|\/]/g, "");
}

function sortPlayerSlots() {
    const container = document.querySelector('.player-slots-container');

    const slots = Array.from(container.querySelectorAll('.player-slot:not(.self)'));

    slots.sort((a, b) => {
        const aIsPlayer = a.classList.contains('player');
        const bIsPlayer = b.classList.contains('player');

        // Compare 'player' slots first based on their 'data-id'
        if (aIsPlayer && bIsPlayer) {
            return parseInt(a.getAttribute('data-id')) - parseInt(b.getAttribute('data-id'));
        }
        
        // If 'a' is a 'player' slot and 'b' is an 'empty' slot, 'a' should come first
        if (aIsPlayer) return -1;
        if (bIsPlayer) return 1;

        // If both 'a' and 'b' are 'empty' slots, sort based on the number in their placeholder
        const aNumber = parseInt(a.querySelector('.player-name').placeholder.split(' ')[1]);
        const bNumber = parseInt(b.querySelector('.player-name').placeholder.split(' ')[1]);
        return aNumber - bNumber;
    });

    slots.forEach(slot => container.appendChild(slot));
}

function getPlayerData() {
    const allPlayerSlots = Array.from(document.querySelector('.player-slots-container').querySelectorAll('.player-slot:not(.empty)'));
    
    let playersData = {};

    allPlayerSlots.forEach(slot => {
        const playerId = slot.getAttribute('data-id');
        const playerName = slot.querySelector('.player-name').value;
        playersData[playerId] = playerName;
    });

    return playersData;
}

document.addEventListener("DOMContentLoaded", function() {
    const readyToggleButton = document.querySelector('.ready-toggle-button');
    const playerNameInput = document.querySelector('.player-name-input');
    const playerSlotsContainer = document.querySelector('.player-slots-container');
    const warningMessage = document.querySelector('.warning-message');
    const selfPlayerSlotDiv = document.querySelector('.player-slot.self');
    const selfPlayerSlotInput = selfPlayerSlotDiv.querySelector('.player-name');
    const submitButton = document.getElementById('submit_button');
    const partyForm = document.querySelector('.party-form');


    function setReadyState(button) {
        button.classList.add('active');
        button.innerText = 'Ready';
        selfPlayerSlotDiv.classList.add('ready');
        playerNameInput.readOnly = true;
    
        selfPlayerSlotInput.value = sanitizeInput(playerNameInput.value.trim());
    
        if (isHost) {
            selfPlayerSlotInput.value += " (host)"
        }
        if (warningMessage) {
            warningMessage.style.display = 'none';
        }
    }


    function setUnreadyState(button) {
        button.classList.remove('active');
        button.innerText = 'Not Ready';
        selfPlayerSlotDiv.classList.remove('ready');
        playerNameInput.readOnly = false;
    }

    function checkPlayerStatusForButton() {
        const allPlayerSlots = Array.from(playerSlotsContainer.querySelectorAll('.player-slot:not(.empty)'));
        
        if (allPlayerSlots.length > 1 && allPlayerSlots.length < 7) {
          const allPlayersReady = allPlayerSlots.every(slot => slot.classList.contains('ready'));
        
          if (allPlayersReady) {
            submitButton.disabled = false;
            submitButton.textContent = 'START GAME';
            submitButton.style.backgroundColor = 'white';
          } else {
            submitButton.disabled = true;
            submitButton.textContent = 'WAIT ON READY';
            submitButton.style.backgroundColor = 'gray';
          }
        } else {
          submitButton.disabled = true;
          submitButton.textContent = 'WAIT ON READY';
          submitButton.style.backgroundColor = 'gray';
        }
      }

    partyForm.addEventListener('submit', function(event) {
        console.log("submit button")
        event.preventDefault();
        const playerData = getPlayerData()
        if (isHost) {
            channel.trigger('client-start-game', {message: 'start'});
            startGame(playerData)
        }
    });

    readyToggleButton.addEventListener('click', function() {
        if (playerNameInput.value.trim() === '') {
            if (warningMessage) {
                warningMessage.style.display = 'block';
            }
            return;
        }

        if (this.classList.contains('active')) {
            setUnreadyState(this);
        } else {
            setReadyState(this);
        }
        
        broadcastClientChange()
    });


    if (playerNameInput) {
        playerNameInput.addEventListener('input', function() {
            setUnreadyState(readyToggleButton);
        });
    }

    /** PUSHER LOGIC **/

    const pusherKey = document.getElementById('pusher-key').value;
    const isHost = document.getElementById('is-host').value === 'True' ? true : false;
    const partyCode = document.getElementById('party_code').value;
    const playerId = document.getElementById('player-id').value;

    console.log("player_id", playerId)
    const pusher = new Pusher(pusherKey, {
        cluster: 'eu',
        authEndpoint: '/pusher/auth'
    });

    const channel = pusher.subscribe(`presence-${partyCode}`);
    const CLIENTCHANGE_NAME = 'client-change';
    const UPDATEPLAYERS_NAME = 'client-all-player-slots-update';
    let justJoined = true

    // Triggers when a new player joins
    channel.bind('pusher:member_added', (member) => {
        console.log('pusher:member_added')
        addPlayerSlot(member.id)
        if (isHost) {
            broadcastAllPlayersInfo()
            checkPlayerStatusForButton()
        }
    });

    // Triggers when a member leaves
    channel.bind('pusher:member_removed', (member) => {
        console.log("member removed!")
        removePlayerFromSlot(member.id);

        if (isHost) {
            checkPlayerStatusForButton()
        }
    });

    // Handle a client change (name or ready status change)
    channel.bind(CLIENTCHANGE_NAME, (data) => {
        console.log(CLIENTCHANGE_NAME)
        updatePlayerSlot(data.playerId, data.playerName, data.status);

        if (isHost) {
            checkPlayerStatusForButton()
        }
    });

    // Handle updates to all player slots
    channel.bind(UPDATEPLAYERS_NAME, (data) => {
        console.log(UPDATEPLAYERS_NAME)
        if (data.playerId === playerId) return;

        if (justJoined) {
            data.forEach(player => {
                addPlayerSlot(player.id)
                updatePlayerSlot(player.id, player.name, player.status);
            });
            justJoined = false
        }

    });

    // Starts game
    channel.bind('client-start-game', (data) => {
        console.log('client-start-game')

        setTimeout(function() {
            startGame();
        }, 500);
    });

    function startGame(playerData = null) {
        console.log("Game is starting!");

        fetch('/initialize_party', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                playerData: playerData
             })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })        
        .then(data => {
            let delay = 10

            if (isHost) {
                delay = 1000
            }
            if (data.redirect_url) {
                setTimeout(function() {
                    redirectWithPost(data.redirect_url);
                }, delay);    
            }
        })
        .catch(error => {
            console.error("Error starting the game:", error.message);
            console.log("Full error:", error);
            });
    
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
    
    function broadcastClientChange() {
        let playerName = sanitizeInput(playerNameInput.value.trim());
        const status = selfPlayerSlotDiv.classList.contains('ready') ? 'ready' : 'unready';
        
        if (isHost && !playerName.endsWith(" (host)")) {
            playerName += " (host)";
        }

        channel.trigger(CLIENTCHANGE_NAME, {
            playerId: playerId,
            playerName: playerName,
            status: status
        });
    }

    function broadcastAllPlayersInfo() {
        const allPlayerSlots = Array.from(playerSlotsContainer.querySelectorAll('.player-slot:not(.empty)'));
        const data = allPlayerSlots.map(slot => {
            let playerName = slot.querySelector('.player-name').value;
            if (isHost && slot.getAttribute('data-id') === playerId && !playerName.endsWith(" (host)")) {
                playerName += " (host)";
            }
            return {
                id: slot.getAttribute('data-id'),
                name: playerName,
                status: slot.classList.contains('ready') ? 'ready' : 'unready'
            };
        });
    
        // Broadcast this full state to all players
        channel.trigger(UPDATEPLAYERS_NAME, data);
    }

    function addPlayerSlot(playerId_) {
        if (playerId === playerId_) return;
        if (document.querySelector(`.player-slot[data-id="${playerId_}"]`)) return;

        // Find the first 'empty' player slot
        const emptySlot = document.querySelector('.player-slot.empty');

        if (!emptySlot) return;
    
        emptySlot.classList.remove('empty');
        emptySlot.classList.add('player');
        
        emptySlot.setAttribute('data-id', playerId_);
        
        sortPlayerSlots()
    }
    
    function removePlayerFromSlot(playerId_) {
        const playerSlot = document.querySelector(`.player-slot[data-id="${playerId_}"]`);
        const inputField = playerSlot.querySelector('.player-name');

        if (inputField.value.includes("(host)")) {
            window.location.href = '/party';
        }
        
        if (playerSlot) {
            // Revert the slot to an 'empty' state
            playerSlot.classList.remove('player', 'ready');
            playerSlot.classList.add('empty');
            playerSlot.removeAttribute('data-id');
            
            const inputField = playerSlot.querySelector('.player-name');
            inputField.value = inputField.getAttribute('placeholder');
        }

        sortPlayerSlots()
    }


    function updatePlayerSlot(playerId_, playerName, status) {
        if (playerId_ === playerId) return;    
        const playerSlot = document.querySelector(`.player-slot[data-id="${playerId_}"]`);
    
        if (!playerSlot) {
            console.warn(`No player slot found for player ID: ${playerId_}`);
            return;
        }
    
        playerSlot.classList.add('player');
        const inputField = playerSlot.querySelector('.player-name');
        inputField.value = playerName;
    
        if (isHost && playerId_ === playerId && !playerName.endsWith(" (host)")) {
            playerName += " (host)";
        }
        inputField.value = playerName;

        if (status === 'ready') {
            playerSlot.classList.add('ready');
        } else {
            playerSlot.classList.remove('ready');
        }
    
        sortPlayerSlots();
    }
        
});
