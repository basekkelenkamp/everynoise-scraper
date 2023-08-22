
function sanitizeInput(input) {
    return input.replace(/[^a-zA-Z0-9 !&*@?._\\|\/]/g, "");
}

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
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

document.addEventListener("DOMContentLoaded", function() {
    const readyToggleButton = document.querySelector('.ready-toggle-button');
    const playerNameInput = document.querySelector('.player-name-input');
    const playerSlotsContainer = document.querySelector('.player-slots-container');
    const warningMessage = document.querySelector('.warning-message');
    const selfPlayerSlotDiv = document.querySelector('.player-slot.self');
    const selfPlayerSlotInput = selfPlayerSlotDiv.querySelector('.player-name');
    

    function setReadyState(button) {
        button.classList.add('active');
        button.innerText = 'Ready';
        selfPlayerSlotDiv.classList.add('ready');
        playerNameInput.readOnly = true;
    
        selfPlayerSlotInput.value = sanitizeInput(playerNameInput.value.trim());
    
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
    const playerId = getCookie("player_id");

    console.log("player_id", playerId)
    const pusher = new Pusher(pusherKey, {
        cluster: 'eu',
        authEndpoint: '/pusher/auth'
    });

    const channel = pusher.subscribe(`presence-${partyCode}`);
    const CLIENTCHANGE_NAME = 'client-change';
    const UPDATEPLAYERS_NAME = 'client-all-player-slots-update';
    let justJoined = true


    // Current player joins the channel, receives a list of all other members. (triggers when joining)
    // channel.bind('pusher:subscription_succeeded', (members) => {
        // console.log('pusher:subscription_succeeded')
        // console.log("player_id:", playerId)
        // members.each((member) => {
        //     if (member.id !== playerId) {  // Exclude the current player
        //         console.log(member)
        //         addPlayerSlot(member.id)
        //     }
        // });
    // });

    // Triggers when a new player joins
    channel.bind('pusher:member_added', (member) => {
        addPlayerSlot(member.id)
        if (isHost) {
            broadcastAllPlayersInfo()
        }
    });

    // Triggers when a member leaves
    channel.bind('pusher:member_removed', (member) => {
        console.log("member removed!")
        removePlayerFromSlot(member.id);
    });

    // Handle a client change (name or ready status change)
    channel.bind(CLIENTCHANGE_NAME, (data) => {
        console.log(CLIENTCHANGE_NAME)
        if (data.playerId === playerId) return; // Ignore events triggered by ourselves

        updatePlayerSlot(data.playerId, data.playerName, data.status);
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
    
    function broadcastClientChange() {
        const playerName = sanitizeInput(playerNameInput.value.trim());
        const status = selfPlayerSlotDiv.classList.contains('ready') ? 'ready' : 'unready';
        
        channel.trigger(CLIENTCHANGE_NAME, {
            playerId: playerId,
            playerName: playerName,
            status: status
        });
    }

    function broadcastAllPlayersInfo() {
        const allPlayerSlots = Array.from(playerSlotsContainer.querySelectorAll('.player-slot:not(.empty)'));
        const data = allPlayerSlots.map(slot => ({
            id: slot.getAttribute('data-id'),
            name: slot.querySelector('.player-name').value,
            status: slot.classList.contains('ready') ? 'ready' : 'unready'
        }));

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
        console.log("updating player slot:");
        console.log(playerId_, playerName, status);
    
        // Find the player slot with the corresponding data-id
        const playerSlot = document.querySelector(`.player-slot[data-id="${playerId_}"]`);
    
        if (!playerSlot) {
            console.warn(`No player slot found for player ID: ${playerId_}`);
            return;
        }
    
        playerSlot.classList.add('player');
        const inputField = playerSlot.querySelector('.player-name');
        inputField.value = playerName;
    
        if (status === 'ready') {
            playerSlot.classList.add('ready');
        } else {
            playerSlot.classList.remove('ready');
        }
    
        sortPlayerSlots();
    }
        
});
