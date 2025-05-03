var client_id = Date.now();
var ws = new WebSocket(`ws://localhost:8000/ws/${client_id}`);

ws.onmessage = function (event) {
    console.log("Received message: ", event.data);
    let ws_message_processor = new WSMessageProcessor(ws);
    ws_message_processor.processMessage(event);
};

/**
 * Strategy pattern context class
 * @class
 */
class WSMessageProcessor{
    /**
     * @constructor
     * @param {WebSocket} ws - The WebSocket instance
     */
    constructor(ws) {
        this.ws = ws;
        /**
         * Concrete strategy
         * @type {AbsGamePhaseHandler}
         */
        this.handler = new AbsGamePhaseHandler();
    }

    /**
     *
     * @param {MessageEvent} event
     */
    processMessage(event){
        let data = JSON.parse(event.data);
        let keys = Object.keys(data);
        let key1 = keys[0];
        switch (key1) {
            case "LOG":
                this.handler = new LogsHandler(data[key1]);
                break;
            case "NEW_PLAYER":
                let player = data[key1]["player"];
                if (player["id"] === client_id)
                    this.handler = new NewSelfHandler(player);
                else
                    this.handler = new NewPlayerHandler(player);
                break;
            case "TURN_HIGHLIGHT":
                this.handler = new TurnHighlightHandler(data[key1]);
                break;
            case "TURN_RESULT":
                this.handler = new TurnResultHandler(data[key1]);
                break;
            case "POT":
                this.handler = new PotHandler(data[key1]);
                break;
            case "TURN_REQUEST":
                this.handler = new TurnRequestHandler(data[key1]);
                break;
            case "IS_READY":
                this.handler = new IsReadyHandler(data[key1]);
                break;
            case "COMMUNITY_CARDS":
                this.handler = new CommunityCardsHandler(data[key1]);
                break;
            case "PRE_START":
                this.handler = new PreStartHandler(data[key1]);
                break;
            case "PRE_FLOP_SB":
                this.handler = new PreFlopSBHandler(data[key1]);
                break;
            case "PRE_FLOP_BB":
                this.handler = new PreFlopBBHandler(data[key1]);
                break;
            case "POCKET_CARDS":
                this.handler = new PocketCardsHandler(data[key1]);
                break;
            default:
                this.handler = new LogsHandler("Unknown state");
                break;
        }
        this.handler.handle();
    }
}

/**
 * Abstract strategy class
 * @class
 */
class AbsGamePhaseHandler {
    constructor(args) {
        this.args = args;
    }

    handle() {
        throw new Error("Must be implemented by subclasses")
    }
}

/**
 * Concrete strategy class, extends abstract strategy class
 * @class
 */
class LogsHandler extends AbsGamePhaseHandler{
    handle(){
        let message = this.args;
        let game_logs = document.getElementById("game_logs");
        let log_message = document.createElement("li");
        log_message.textContent = message;
        game_logs.appendChild(log_message);
    }
}

class NewPlayerHandler extends AbsGamePhaseHandler{
    handle(){
        let player = this.args;
        let player_div = CreatePlayer(player);
        let playersContainer = document.getElementById("players"); // Target the correct container
        playersContainer.appendChild(player_div);
    }
}

class NewSelfHandler extends AbsGamePhaseHandler{
    handle(){
        let player = this.args;
        let player_div = CreatePlayer(player);
        let playersContainer = document.getElementById("players"); // Target the correct container
        playersContainer.appendChild(player_div);

        // Show ready button (This logic remains the same)
        document.getElementById("ready_button").style.display = "flex";
    }
}

function CreatePlayer(player) {
    let id = player["id"];
    let name = player["name"];
    let balance = player["balance"];

    let player_div = document.createElement("div");
    player_div.id = id + "_div";
    player_div.classList.add("player_div_default"); // Add class for default styling

    // Container for player info (Name, Balance)
    let info_div = document.createElement("div");
    info_div.className = "player_info"; // Use class for styling

    let player_name = document.createElement("p");
    player_name.id = id + "_name";
    player_name.className = "player_name"; // Use class for styling
    // *** FIX: Use backticks (`) for template literal evaluation ***
    player_name.textContent = `Player ${name}${id === client_id ? ' (You)' : ''}`;
    info_div.appendChild(player_name);

    let player_balance = document.createElement("p");
    player_balance.id = id + "_balance";
    player_balance.className = "player_balance"; // Use class for styling
    player_balance.textContent = `Balance: $${balance}`;
    info_div.appendChild(player_balance);

    player_div.appendChild(info_div); // Add info container

    // Container for game state elements (Dealer, Turn status/Cards)
    let state_div = document.createElement("div");
    state_div.className = "player_state"; // Use class for styling

    // --- Dealer Chip and Turn Status ---
    let status_container = document.createElement("div"); // Container for top row (Dealer, Turn)
    status_container.className = "player_status_container";

    let dealer_chip = document.createElement("span"); // Use span for inline display
    dealer_chip.textContent = "(D)";
    dealer_chip.className = "dealer_chip"; // Use class for styling
    dealer_chip.id = id + "_dealer";
    dealer_chip.style.display = "none"; // Initially hidden
    status_container.appendChild(dealer_chip);

    let turn_status = document.createElement("span"); // Use span
    turn_status.id = id + "_turn";
    turn_status.className = "turn_status"; // Use class for styling
    status_container.appendChild(turn_status);

    state_div.appendChild(status_container); // Add status container to state div

    // --- Pocket Cards Container ---
    let cards_container = document.createElement("div");
    cards_container.className = "player_cards_container"; // New class for card row

    let card_0 = document.createElement("div"); // Use span
    card_0.id = id + "_card_0";
    cards_container.appendChild(card_0); // Add card to cards container

    let card_1 = document.createElement("div"); // Use span
    card_1.id = id + "_card_1";
    cards_container.appendChild(card_1); // Add card to cards container

    state_div.appendChild(cards_container); // Add cards container to state div

    player_div.appendChild(state_div); // Add state container

    return player_div;
}

class IsReadyHandler extends AbsGamePhaseHandler{
    handle() {
        let data = this.args;
        let player_id = data["player_id"];
        let is_ready = data["is_ready"];

        let player_turn = document.getElementById(player_id + "_turn");
        if (is_ready) {
            player_turn.textContent = "✅";
        } else{
            player_turn.textContent = "❌";
        }
    }
}

function arrangePlayersInCircle(orderedPlayerIds) {
    const playersContainer = document.getElementById('players');
    const tableContainer = document.getElementById('poker_table_container');
    const playerDivs = Array.from(playersContainer.children).filter(el => el.id.endsWith('_div')); // Get only player divs

    // Clear existing absolute positioning before recalculating
    playerDivs.forEach(div => {
        div.style.position = 'absolute'; // Ensure it's absolute
        div.style.top = '';
        div.style.left = '';
        div.style.transform = ''; // Reset transform
    });

    const numPlayers = orderedPlayerIds.length;
    if (numPlayers === 0) return;

    const radiusX = tableContainer.offsetWidth / 2 - 60; // Horizontal radius (adjust 60 based on player div width)
    const radiusY = tableContainer.offsetHeight / 2 - 40; // Vertical radius (adjust 40 based on player div height)
    const centerX = tableContainer.offsetWidth / 2;
    const centerY = tableContainer.offsetHeight / 2;

    // Find the index of the current user in the ordered list
    let userIndex = orderedPlayerIds.findIndex(id => id === client_id);
    if (userIndex === -1) {
        console.error("Current user not found in ordered list!");
        // Fallback or default arrangement if user not found?
        // For now, let's just proceed, user might be spectator or issue exists
        userIndex = 0; // Default to first player if issue
    }

    // Calculate the angle step
    const angleStep = (2 * Math.PI) / numPlayers;

    // Calculate the angle offset needed to place the user at the bottom (approx 90 degrees or PI/2 radians)
    // The starting angle (angle = 0) is typically the rightmost point (3 o'clock).
    // We want the userIndex to be at 90 degrees (PI/2).
    const userTargetAngle = Math.PI / 2;
    const userCurrentAngle = userIndex * angleStep;
    const angleOffset = userTargetAngle - userCurrentAngle;

    orderedPlayerIds.forEach((playerId, index) => {
        const playerDiv = document.getElementById(`${playerId}_div`);
        if (!playerDiv) {
            console.warn(`Player div not found for ID: ${playerId}`);
            return; // Skip if div doesn't exist
        }

        // --- >>> Ensure position is absolute <<< ---
        playerDiv.style.position = 'absolute';
        // --- >>> Ensure it overrides default styles <<< ---
        playerDiv.classList.remove("player_div_default"); // Optional: remove default class if styles conflict
        playerDiv.style.width = '100px'; // Re-apply width for circle if needed
        playerDiv.style.justifyContent = ''; // Reset justify-content if needed

        // ... (calculate angle, x, y) ...
        const angle = (index * angleStep) + angleOffset;
        const x = centerX + radiusX * Math.cos(angle) - (playerDiv.offsetWidth / 2);
        const y = centerY + radiusY * Math.sin(angle) - (playerDiv.offsetHeight / 2);


        // Apply the position
        playerDiv.style.left = `${x}px`;
        playerDiv.style.top = `${y}px`;

        // Optional: Rotate player divs to face the center (can look cluttered)
        // const rotation = angle * (180 / Math.PI) + 90; // Adjust rotation angle
        // playerDiv.style.transform = `rotate(${rotation}deg)`;

        console.log(`Positioned player <span class="math-inline">\{playerId\} at \(</span>{x.toFixed(1)}, ${y.toFixed(1)}) angle ${ (angle * 180/Math.PI).toFixed(1)}deg`);
    });

     // --- Position Buttons Below User ---
     // This part might need refinement based on your exact layout.
     // It assumes the user's div is now positioned correctly.
     const selfButtons = document.getElementById('self_buttons');
     const userDiv = document.getElementById(`${client_id}_div`);
     if (userDiv && selfButtons) {
        // Option 1: Place buttons relative to the table container, fixed bottom
         selfButtons.style.position = 'absolute'; // Or relative if table container allows overflow
         selfButtons.style.bottom = '-50px'; // Adjust as needed, below the container
         selfButtons.style.left = '50%';
         selfButtons.style.transform = 'translateX(-50%)';
         selfButtons.style.zIndex = '10'; // Ensure buttons are clickable

        // Option 2: Dynamically position below the userDiv (more complex if table size changes)
        // selfButtons.style.position = 'absolute';
        // selfButtons.style.top = `${userDiv.offsetTop + userDiv.offsetHeight + 10}px`; // 10px gap
        // selfButtons.style.left = `${userDiv.offsetLeft + (userDiv.offsetWidth / 2) - (selfButtons.offsetWidth / 2)}px`; // Center below user
     }

}

class PreStartHandler extends AbsGamePhaseHandler{
    handle() {
        let data = this.args;
        let prev_dealer = data["prev_dealer"]["id"];
        let curr_dealer = data["curr_dealer"]["id"];
        let orderedPlayerIds = data["ordered_player_ids"]; // Get the ordered list

        // Add class to the container to trigger CSS change
        const tableContainer = document.getElementById('poker_table_container');
        tableContainer.classList.add('game-started');
        const communityCardsContainer = document.getElementById('community_cards');
        communityCardsContainer.style.display="flex"
        communityCardsContainer.innerHTML = ''; // Clear any previous cards
        for (let i = 0; i < 5; i++) {
            let placeholder = document.createElement('div');
            placeholder.classList.add('community-card-placeholder');
            // Add specific IDs if needed later for targeting individual cards
            placeholder.id = `community_card_${i}`;
            communityCardsContainer.appendChild(placeholder);
        }

        // Hide/show dealer chips (existing logic)
        let prev_dealer_chip = document.getElementById(prev_dealer + "_dealer");
        if (prev_dealer_chip) prev_dealer_chip.style.display = "none";
        let curr_dealer_chip = document.getElementById(curr_dealer + "_dealer");
        if (curr_dealer_chip) curr_dealer_chip.style.display = "inline-block"; // Or "flex" if it's a block

        // Clear any lingering "ready" status from player divs
        orderedPlayerIds.forEach(id => {
             const turnStatus = document.getElementById(id + "_turn");
             if (turnStatus && (turnStatus.textContent === '✅' || turnStatus.textContent === '❌')) {
                 turnStatus.textContent = ''; // Clear ready checkmark
             }
             const card0 = document.getElementById(id + "_card_0");
             const card1 = document.getElementById(id + "_card_1");
             if(card0) card0.textContent = ''; card0.style.display = 'none';
             if(card1) card1.textContent = ''; card1.style.display = 'none';
        });

        // Hide ready button (existing logic)
        let ready_button = document.getElementById("ready_button");
        ready_button.style.display = "none";

        // Call the arrangement function (ensure it sets absolute position)
        arrangePlayersInCircle(orderedPlayerIds); // This function should ensure style.position = 'absolute'

        // Log game start (existing logic)
        let logs = new LogsHandler("Pre-flop🎴");
        logs.handle();
    }
}

class PreFlopSBHandler extends AbsGamePhaseHandler{
    handle() {
        let data = this.args;
        let sb_amount = data["sb_amount"];
        let player = data["player"];

        let turn = document.getElementById(player["id"] + "_turn");
        turn.textContent = "Small blind: $" + sb_amount;
        let balance = document.getElementById(player["id"] + "_balance");
        balance.textContent = "Balance: $" + player["balance"];

        let logs = new LogsHandler(player["name"] + ": small blind: $" + sb_amount);
        logs.handle();
    }
}

class PreFlopBBHandler extends AbsGamePhaseHandler{
    handle() {
        let data = this.args;
        let bb_amount = data["bb_amount"];
        let player = data["player"];

        let turn = document.getElementById(player["id"] + "_turn");
        turn.textContent = "Big blind: $" + bb_amount;
        let balance = document.getElementById(player["id"] + "_balance");
        balance.textContent = "Balance: $" + player["balance"];

        let logs = new LogsHandler(player["name"] + ": big blind: $" + bb_amount);
        logs.handle();
    }
}

class PocketCardsHandler extends AbsGamePhaseHandler{
    handle() {
        let data = this.args;
        let cards = data["pocket_cards"];

        // Update the text content of the card elements
        for (let i = 0; i < cards.length && i < 2; i++) { // Iterate through received cards (max 2)
            let cardElement = document.getElementById(client_id + "_card_" + i);
            if (cardElement) {
                 // Set text content (e.g., "♥️A", "♠️K")
                 // You might want different styling for suit and rank later
                 cardElement.textContent = cards[i]["suit"] + cards[i]["rank"];
                 cardElement.className = "card-display"
                 cardElement.style.display = 'inline-flex';
            }
        }
         // Optional: Hide card elements if fewer than 2 cards are dealt (e.g., game reset)
         for (let i = cards.length; i < 2; i++) {
             let cardElement = document.getElementById(client_id + "_card_" + i);
             if (cardElement) {
                 cardElement.textContent = ''; // Clear text
                 cardElement.style.display = 'none'; // Hide unused card slots
             }
         }
    }
}

class TurnRequestHandler extends AbsGamePhaseHandler{
    handle() {
        let data = this.args;
        let player_bet = data["player_bet"];
        let prev_bet = data["prev_bet"];
        let prev_raise = data["prev_raise"];
        let options = data["options"];

        let to_call = prev_bet - player_bet;

        if (options.includes("CALL")) {
            let call_button = document.getElementById("call_button");
            call_button.textContent = "Call $" + to_call;
            call_button.style.display = "flex";
        }

        options.forEach(option => {
            let option_str = option.toString().toLowerCase();
            let button = document.getElementById(option_str + "_button");

            if (button) {
                button.style.display = "flex";
                button.onclick = () => {
                    if (option_str === "raise") {
                        this.showRaiseSlider(prev_raise);
                    } else {
                        sendTurn(option, to_call); // Handle other options like Call, Fold, Check
                    }
                };
            }
        });

    }
    /**
     * Show a slider for setting the raise amount and a submit button.
     * @param {number} prev_raise - Minimum bet amount.
     */
    showRaiseSlider(prev_raise) {
        // Get player's balance from their balance element
        let player_balance_element = document.getElementById(`${client_id}_balance`);
        let player_balance = parseInt(player_balance_element.textContent.replace("Balance: $", "")); // Parse the balance as an integer

        // Ensure player_balance is valid
        if (isNaN(player_balance)) {
            console.error("Error: Unable to determine player's balance.");
            return;
        }

        // Remove any existing slider container to prevent duplication
        let existing_slider = document.getElementById("raise_slider_container");
        if (existing_slider) existing_slider.remove();

        // Create a container for the slider and submit button
        let slider_container = document.createElement("div");
        slider_container.id = "raise_slider_container";
        slider_container.style.display = "flex";
        slider_container.style.flexDirection = "column";
        slider_container.style.marginTop = "10px";

        // Create the slider input
        let slider = document.createElement("input");
        slider.type = "range";
        slider.min = prev_raise.toString(); // Minimum value is the `bet`
        slider.max = player_balance.toString(); // Maximum value is player's balance
        slider.step = "5"
        slider.value = prev_raise.toString(); // Default starting value is the `bet`
        slider.id = "raise_slider";

        // Create a label to display the current slider value
        let slider_label = document.createElement("p");
        slider_label.id = "slider_value_label";
        slider_label.textContent = `Raise Amount: $${slider.value}`; // Display initial slider value

        slider.oninput = function () {
            slider_label.textContent = `Raise Amount: $${slider.value}`; // Update label when slider value changes
        };

        // Create the "Submit Bet" button
        let submit_button = document.createElement("button");
        submit_button.textContent = "Submit Bet";
        submit_button.style.marginTop = "10px";

        // Define the behavior for the submit button
        submit_button.onclick = () => {
            let raise_amount = parseInt(slider.value); // Get the slider value as an integer
            if (raise_amount >= prev_raise && raise_amount <= player_balance) {
                sendTurn("RAISE", raise_amount); // Send the raise amount
                slider_container.remove(); // Remove the slider UI after submission
            } else {
                console.error("Invalid raise amount.");
            }
        };

        // Append elements to the container
        slider_container.appendChild(slider_label);
        slider_container.appendChild(slider);
        slider_container.appendChild(submit_button);

        // Add the slider container to the DOM, below the buttons
        let buttons_div = document.getElementById("self_buttons");
        buttons_div.appendChild(slider_container);
    }

}

class TurnResultHandler extends AbsGamePhaseHandler{
    handle() {
        let data = this.args;
        let player = data["player"];
        let choice = data["choice"];
        let amount = data["amount"];

        document.getElementById(player["id"] + "_balance").textContent = "Balance: $" + player["balance"];
        let turn_str = choice.charAt(0) + choice.toString().toLowerCase().slice(1, choice.length) + " $" + amount;

        let msg_end = ""
        switch (choice) {
            case "CALL":
                msg_end = " called $" + amount;
                break;
            case "CHECK":
                msg_end = " checked";
                turn_str = "Check";
                break;
            case "RAISE":
                msg_end = " raised $" + amount;
                break;
            case "FOLD":
                msg_end = " folded";
                turn_str = choice.charAt(0) + choice.toString().toLowerCase().slice(1, choice.length)
                break;
            default:
                msg_end = " unknown choice"
                break;
        }

        document.getElementById(player["id"] + "_turn").textContent = turn_str;
        let logs = new LogsHandler(player["name"] + msg_end)
        logs.handle();
    }
}

class PotHandler extends AbsGamePhaseHandler{
    handle() {
        let data = this.args;
        let pot = data["pot"]

        let pot_element = document.getElementById("pot")
        pot_element.textContent = '$' + pot
    }
}

class TurnHighlightHandler extends AbsGamePhaseHandler{
    handle() {
        let data = this.args;
        let prev_player = data["prev_player"];
        let curr_player = data["curr_player"];

        let prev_player_name = document.getElementById(prev_player["id"] + "_name");
        prev_player_name.style.color = "black";

        if (curr_player === null)
            return;

        let curr_player_name = document.getElementById(curr_player["id"] + "_name");
        curr_player_name.style.color = "green";
    }
}

class CommunityCardsHandler extends AbsGamePhaseHandler{
    handle(){
        let data = this.args;
        let cards = data["cards"];

        let players_div = document.getElementById('players');
        for (let i=0; i<players_div.children.length; i++) {
            let name = players_div.children[i].id.split("_")[0]
            let turn_element = document.getElementById(name + "_turn");
            if (turn_element.textContent !== "Fold"){
                turn_element.textContent = "";
            }
        }

        for (let i = 0; i < cards.length; i++) {
            let cardPlaceholder = document.getElementById(`community_card_${i}`);
            if (cardPlaceholder) {
                cardPlaceholder.classList.remove('community-card-placeholder'); // Remove placeholder style
                cardPlaceholder.classList.add('card-display'); // Add actual card style
                cardPlaceholder.textContent = cards[i]["suit"] + cards[i]["rank"];
            }
        }
    }
}