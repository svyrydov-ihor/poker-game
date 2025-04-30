async function readyButtonClick(button) {
    let is_ready = true
    if (button.classList.contains("not-ready")) {
        // If currently not ready, switch to ready
        button.classList.remove("not-ready");
        button.classList.add("ready");
        is_ready = true;
    } else {
        // If currently ready (or no class yet), switch to not ready
        button.classList.remove("ready");
        button.classList.add("not-ready");
        is_ready = false;
    }
    await fetch(`http://127.0.0.1:8000/player-ready/${client_id}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({"is_player_ready": is_ready})
        });
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