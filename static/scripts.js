var client_id = Date.now();
var ws = new WebSocket(`ws://localhost:8000/ws/${client_id}`);

ws.onmessage = function (event) {
    console.log("Received message: ", event.data);
    let data = JSON.parse(event.data);
    let keys = Object.keys(data);
    let key1 = keys[0];
    let handler = new AbsGamePhaseHandler();
    switch (key1) {
        case "LOG":
            handler = new LogsHandler(data[key1]);
            break;
        case "NEW_PLAYER":
            let player = data[key1]["player"];
            if (player["id"] === client_id)
                handler = new NewSelfHandler(player);
            else
                handler = new NewPlayerHandler(player);
            break;
        case "PRE_START":
            handler = new PreStartHandler(data[key1]);
            break;
        case "PRE_FLOP_SB":
            handler = new PreFlopSBHandler(data[key1]);
            break;
        case "PRE_FLOP_BB":
            handler = new PreFlopBBHandler(data[key1]);
            break;
        case "POCKET_CARDS":
            handler = new PocketCardsHandler(data[key1]);
            break;
        case "TURN":
            break;
        default:
            handler = new LogsHandler("Unknown state");
            break;
    }
    handler.handle();
};

class AbsGamePhaseHandler {
    constructor(args) {
        this.args = args;
    }

    handle() {
        throw new Error("Must be implemented by subclasses")
    }
}

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
        console.log("args:", this.args);
        let player = this.args;
        let player_div = CreatePlayer(player);
        let players = document.getElementById("players");

        if (players.children.length > 0){
            players.insertBefore(player_div, players.lastElementChild);
        }
        else{
            players.appendChild(player_div);
        }
    }
}

class NewSelfHandler extends AbsGamePhaseHandler{
    handle(){
        console.log("args self:", this.args);
        let player = this.args;
        let player_div = CreatePlayer(player)
        let players = document.getElementById("players");
        players.appendChild(player_div);

        document.getElementById("ready_button").style.display = "flex";
    }
}

function CreatePlayer(player) {
    let id = player["id"];
    let name = player["name"];
    let balance = player["balance"];

    let player_div = document.createElement("div");
    player_div.style.display = "flex";
    player_div.id = id + "_div";

    let info_div = document.createElement("div");
    info_div.style.display = "flex";
    info_div.style.flexDirection = "column"; // Name and balance stack vertically


    let player_name = document.createElement("p");
    if (id === client_id){
        player_name.textContent = "Player " + name + " (You): ";
    }
    else{
        player_name.textContent = "Player " + name + ": ";
    }
    player_name.className = "row";
    info_div.appendChild(player_name);

    // Create player balance element
    let player_balance = document.createElement("p");
    player_balance.textContent = "Balance: $" + balance; // Add balance text
    player_balance.id = id + "_balance";
    player_balance.style.fontWeight = "normal";
    player_balance.style.fontSize = "15px";
    player_balance.style.margin = "-15px 0 10px 0";
    info_div.appendChild(player_balance); // Add balance to info_div

    // Append info_div to player_div
    player_div.appendChild(info_div);

    let dealer_chip = document.createElement("p");
    dealer_chip.textContent = "(D)";
    dealer_chip.className = "row";
    dealer_chip.style.display = "none";
    dealer_chip.id = id + "_dealer";
    player_div.appendChild(dealer_chip);

    ["_turn", "_card_0", "_card_1"].forEach(suffix => {
        let element = document.createElement("p");
        element.textContent = "";
        element.className = "row";
        element.id = id + suffix;
        element.style.fontWeight = "normal"
        player_div.appendChild(element);
    })

    return player_div;
}

class PreStartHandler extends AbsGamePhaseHandler{
    handle(){
        let data = this.args;
        let prev_dealer = data["prev_dealer"]["id"]
        let curr_dealer = data["curr_dealer"]["id"]

        let prev_dealer_div = document.getElementById(prev_dealer + "_dealer");
        prev_dealer_div.style.display = "none";
        let curr_dealer_div = document.getElementById(curr_dealer + "_dealer");
        curr_dealer_div.style.display = "flex";

        let ready_button = document.getElementById("ready_button");
        ready_button.style.display = "none";
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

        let logs = new LogsHandler(player["name"] + ": big blind: $" + sb_amount);
        logs.handle();
    }
}

class PocketCardsHandler extends AbsGamePhaseHandler{
    handle() {
        let data = this.args;
        let cards = data["pocket_cards"];

        for (let i = 0; i < 2; i++) {
            let card_text = document.getElementById(client_id + "_card_" + i);
            card_text.textContent = cards[i]["suit"] + cards[i]["rank"];
        }
    }
}

class TurnHandler extends AbsGamePhaseHandler{
    handle() {

    }
}