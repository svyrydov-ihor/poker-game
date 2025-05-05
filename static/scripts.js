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
            case "SHOWDOWN_WINNERS":
                this.handler = new ShowdownWinnersHandler(data[key1]);
                break;
            case "SHOWDOWN_LOSERS":
                this.handler = new ShowdownLosersHandler(data[key1]);
                break;
            case "PLAY_AGAIN":
                this.handler = new PlayAgainHandler(data[key1]);
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
        let playersContainer = document.getElementById("players");
        playersContainer.appendChild(player_div);
    }
}

class NewSelfHandler extends AbsGamePhaseHandler{
    handle(){
        let player = this.args;
        let player_div = CreatePlayer(player);
        let playersContainer = document.getElementById("players");
        playersContainer.appendChild(player_div);

        document.getElementById("ready_button").style.display = "flex";
    }
}

function CreatePlayer(player) {
    let id = player["id"];
    let name = player["name"];
    let balance = player["balance"];

    let player_div = document.createElement("div");
    player_div.id = id + "_div";
    player_div.classList.add("player_div_default");

    // Container for player info (Name, Balance)
    let info_div = document.createElement("div");
    info_div.className = "player_info";

    let player_name = document.createElement("p");
    player_name.id = id + "_name";
    player_name.className = "player_name";

    player_name.textContent = `Player ${name}${id === client_id ? ' (You)' : ''}`;
    info_div.appendChild(player_name);

    let player_balance = document.createElement("p");
    player_balance.id = id + "_balance";
    player_balance.className = "player_balance";
    player_balance.textContent = `Balance: $${balance}`;
    info_div.appendChild(player_balance);

    player_div.appendChild(info_div);

    // Container for game state elements (Dealer, Turn status/Cards)
    let state_div = document.createElement("div");
    state_div.className = "player_state";

    let status_container = document.createElement("div"); // Container for top row (Dealer, Turn)
    status_container.className = "player_status_container";

    let dealer_chip = document.createElement("span");
    dealer_chip.textContent = "(D)";
    dealer_chip.className = "dealer_chip";
    dealer_chip.id = id + "_dealer";
    dealer_chip.style.display = "none";
    status_container.appendChild(dealer_chip);

    let turn_status = document.createElement("span");
    turn_status.id = id + "_turn";
    turn_status.className = "turn_status";
    status_container.appendChild(turn_status);

    state_div.appendChild(status_container);

    // Pocket Cards Container
    let cards_container = document.createElement("div");
    cards_container.className = "player_cards_container";

    let card_0 = document.createElement("div");
    card_0.id = id + "_card_0";
    cards_container.appendChild(card_0);

    let card_1 = document.createElement("div");
    card_1.id = id + "_card_1";
    cards_container.appendChild(card_1);

    state_div.appendChild(cards_container);

    player_div.appendChild(state_div);

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
    const playerDivs = Array.from(playersContainer.children).filter(el => el.id.endsWith('_div'));

    // Clear existing absolute positioning before recalculating
    playerDivs.forEach(div => {
        div.style.position = 'absolute';
        div.style.top = '';
        div.style.left = '';
        div.style.transform = '';
    });

    const numPlayers = orderedPlayerIds.length;
    if (numPlayers === 0) return;

    const radiusX = tableContainer.offsetWidth / 2 - 60; // Horizontal radius
    const radiusY = tableContainer.offsetHeight / 2 - 40; // Vertical radius
    const centerX = tableContainer.offsetWidth / 2;
    const centerY = tableContainer.offsetHeight / 2;

    // Find the index of the current user in the ordered list
    let userIndex = orderedPlayerIds.findIndex(id => id === client_id);
    if (userIndex === -1) {
        console.error("Current user not found in ordered list!");
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

        playerDiv.style.position = 'absolute';
        playerDiv.classList.remove("player_div_default");
        playerDiv.style.width = '100px';
        playerDiv.style.justifyContent = '';

        // Calculate angle, x, y
        const angle = (index * angleStep) + angleOffset;
        const x = centerX + radiusX * Math.cos(angle) - (playerDiv.offsetWidth / 2);
        const y = centerY + radiusY * Math.sin(angle) - (playerDiv.offsetHeight / 2);

        // Apply the position
        playerDiv.style.left = `${x}px`;
        playerDiv.style.top = `${y}px`;
    });

     // Position buttons below user
     const selfButtons = document.getElementById('self_buttons');
     const userDiv = document.getElementById(`${client_id}_div`);
     if (userDiv && selfButtons) {
         selfButtons.style.position = 'absolute';
         selfButtons.style.bottom = '-50px';
         selfButtons.style.left = '50%';
         selfButtons.style.transform = 'translateX(-50%)';
         selfButtons.style.zIndex = '10';
     }

}

class PreStartHandler extends AbsGamePhaseHandler{
    handle() {
        let data = this.args;
        let prev_dealer = data["prev_dealer"]["id"];
        let curr_dealer = data["curr_dealer"]["id"];
        let orderedPlayerIds = data["ordered_player_ids"];

        const tableContainer = document.getElementById('poker_table_container');
        tableContainer.classList.add('game-started');
        const communityCardsContainer = document.getElementById('community_cards');
        communityCardsContainer.style.display="flex"
        communityCardsContainer.innerHTML = '';
        for (let i = 0; i < 5; i++) {
            let placeholder = document.createElement('div');
            placeholder.classList.add('community-card-placeholder');

            placeholder.id = `community_card_${i}`;
            communityCardsContainer.appendChild(placeholder);
        }

        // Hide/show dealer chips
        let prev_dealer_chip = document.getElementById(prev_dealer + "_dealer");
        if (prev_dealer_chip) prev_dealer_chip.style.display = "none";
        let curr_dealer_chip = document.getElementById(curr_dealer + "_dealer");
        if (curr_dealer_chip) curr_dealer_chip.style.display = "inline-block";

        // Clear any lingering "ready" status from player divs
        orderedPlayerIds.forEach(id => {
             const turnStatus = document.getElementById(id + "_turn");
             if (turnStatus && (turnStatus.textContent === '✅' || turnStatus.textContent === '❌')) {
                 turnStatus.textContent = '';
             }
             const card0 = document.getElementById(id + "_card_0");
             const card1 = document.getElementById(id + "_card_1");
             if(card0) card0.textContent = ''; card0.style.display = 'none';
             if(card1) card1.textContent = ''; card1.style.display = 'none';
             let turn = document.getElementById(id + "_turn");
             turn.textContent = '';
        });

        // Hide ready button
        let ready_button = document.getElementById("ready_button");
        ready_button.style.display = "none";

        // Call the arrangement function
        arrangePlayersInCircle(orderedPlayerIds);

        let logs = new LogsHandler("Pre-flop 🃏");
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

        for (let i = 0; i < cards.length && i < 2; i++) {
            let cardElement = document.getElementById(client_id + "_card_" + i);
            if (cardElement) {
                 cardElement.textContent = cards[i]["suit"] + cards[i]["rank"];
                 cardElement.className = "card-display"
                 cardElement.style.display = 'inline-flex';
            }
        }

         for (let i = cards.length; i < 2; i++) {
             let cardElement = document.getElementById(client_id + "_card_" + i);
             if (cardElement) {
                 cardElement.textContent = '';
                 cardElement.style.display = 'none';
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
                        sendTurn(option, to_call);
                    }
                };
            }
        });

    }
    /**
     * Show a slider for setting the raise amount and a submit button
     * @param {number} prev_raise - Minimum bet amount
     */
    showRaiseSlider(prev_raise) {
        let player_balance_element = document.getElementById(`${client_id}_balance`);
        let player_balance = parseInt(player_balance_element.textContent.replace("Balance: $", ""));

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
        slider.min = prev_raise.toString(); // Minimum value is previous raise
        slider.max = player_balance.toString(); // Maximum value is player's balance
        slider.step = "5" // Just for convenience
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
            let raise_amount = parseInt(slider.value); // Get the slider value as an integer, for convenience
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
        let action = data["action"];
        let amount = data["amount"];

        document.getElementById(player["id"] + "_balance").textContent = "Balance: $" + player["balance"];
        let turn_str = action.charAt(0) + action.toString().toLowerCase().slice(1, action.length) + " $" + amount;

        let msg_end = ""
        switch (action) {
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
                turn_str = action.charAt(0) + action.toString().toLowerCase().slice(1, action.length)
                break;
            default:
                msg_end = " unknown action"
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
                cardPlaceholder.classList.remove('community-card-placeholder');
                cardPlaceholder.classList.add('card-display');
                cardPlaceholder.textContent = cards[i]["suit"] + cards[i]["rank"];
            }
        }
    }
}

const HandNames = Object.freeze({
    0: "High Card",
    1: "One Pair",
    2: "Two Pairs",
    3: "Three of a Kind",
    4: "Straight",
    5: "Flush",
    6: "Full House",
    7: "Four of a Kind",
    8: "Straight Flush",
    9: "Royal Flush",
});

class ShowdownWinnersHandler extends AbsGamePhaseHandler{
    handle(){
        let data = this.args;
        let winners = data["winners"];
        winners.forEach(winner => {
            let balance_element = document.getElementById(winner["winner"]["id"] + "_balance");
            balance_element.textContent = "Balance: $" + winner["winner"]["balance"];
            let i=0
            winner["pocket_cards"].forEach(card => {
                let card_element = document.getElementById(winner["winner"]["id"] + "_card_" + i);
                card_element.textContent = card["suit"] + card["rank"];
                i+=1
            })
            let turn_element = document.getElementById(winner["winner"]["id"] + "_turn");
            turn_element.textContent = HandNames[winner["hand"]] + " winner";
        })
    }
}

class ShowdownLosersHandler extends AbsGamePhaseHandler{
    handle() {
        let data = this.args;
        let losers = data["losers"];
        losers.forEach(loser => {
            let i=0
            loser["pocket_cards"].forEach(card => {
                let card_element = document.getElementById(loser["player"]["id"] + "_card_" + i);
                card_element.textContent = card["suit"] + card["rank"];
                i+=1
            })
            let turn_element = document.getElementById(loser["player"]["id"] + "_turn");
            turn_element.textContent = HandNames[loser["hand"]];
        })
    }
}

class PlayAgainHandler extends AbsGamePhaseHandler{
    handle() {
        let ready_button = document.getElementById("ready_button");
        ready_button.className = "not-ready";
        ready_button.style.display = "flex";
    }
}