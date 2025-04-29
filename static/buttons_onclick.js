async function readyButtonClick(button) {
    if (button.style.color === "red") {
        button.style.color = "green";
        await fetch(`http://127.0.0.1:8000/player-ready/${client_id}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({"is_player_ready": true})
        });
    } else {
        button.style.color = "red";
        await fetch(`http://127.0.0.1:8000/player-ready/${client_id}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({"is_player_ready": false})
        });
    }
}

function sendTurn(choice, amount=0) {
    ws.send(JSON.stringify({
        "TURN_RESPONSE": {"choice": choice, "amount": amount}
    }))

    let buttons = document.getElementById("self_buttons");
    console.log(buttons);
    Array.from(buttons.children).forEach(button => {
        button.style.display = "none";
    })
}