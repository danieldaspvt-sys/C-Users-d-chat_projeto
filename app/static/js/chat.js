// Conexão socket
var socket = io({ transports: ["websocket"] });

var activeUser = null;

// Iniciar conversa digitando @usuario
function startChatFromInput() {
    const input = document.getElementById("msg");
    const value = input.value.trim();

    if (value.startsWith("@")) {
        const username = value.substring(1);

        if (!username) return;

        activeUser = username;

        socket.emit("start_chat", { to: username });

        document.getElementById("messages").innerHTML = "";
        input.value = "";
    }
}

// Enviar mensagem privada
function sendMsg() {
    const input = document.getElementById("msg");
    const msg = input.value.trim();

    if (!msg) return;

    // Se começar com @, inicia conversa
    if (msg.startsWith("@")) {
        startChatFromInput();
        return;
    }

    if (!activeUser) {
        alert("Digite @usuario para iniciar conversa.");
        return;
    }

    socket.emit("private_message", {
        to: activeUser,
        message: msg
    });

    input.value = "";
}

// Receber histórico
socket.on("chat_history", function(history) {
    const messagesDiv = document.getElementById("messages");
    messagesDiv.innerHTML = "";

    history.forEach(msg => {
        renderMessage(msg.from, msg.message);
    });
});

// Receber mensagem privada
socket.on("private_message", function(data) {
    renderMessage(data.from, data.message);
});

// Renderizar mensagem
function renderMessage(sender, message) {
    const messagesDiv = document.getElementById("messages");

    const div = document.createElement("div");
    div.classList.add("message");

    if (sender === username) {
        div.classList.add("me");
    } else {
        div.classList.add("other");
    }

    div.innerText = sender + ": " + message;

    messagesDiv.appendChild(div);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// Enter envia mensagem
document.getElementById("msg").addEventListener("keypress", function(e) {
    if (e.key === "Enter") {
        sendMsg();
    }
});