const socket = io();

let currentChatUser = null;

socket.on("online_users", function(users) {
    const list = document.getElementById("usersList");
    list.innerHTML = "";

    users.forEach(user => {
        if(user === window.currentUser) return;

        const div = document.createElement("div");
        div.className = "user-item";
        div.innerText = "@" + user;

        div.onclick = function() {
            startChat(user);
        };

        list.appendChild(div);
    });
});

socket.on("private_message", function(data) {
    if(data.from === currentChatUser || data.to === currentChatUser) {
        addMessage(data.message, data.from === window.currentUser);
    }
});

function startChat(user) {
    currentChatUser = user;
    document.getElementById("chatWith").innerText = "Conversando com @" + user;
    document.getElementById("messages").innerHTML = "";

    socket.emit("start_chat", { to: user });
}

function sendMessage() {
    const input = document.getElementById("messageInput");
    const message = input.value;

    if(!message || !currentChatUser) return;

    socket.emit("private_message", {
        to: currentChatUser,
        message: message
    });

    addMessage(message, true);
    input.value = "";
}

function addMessage(text, sent) {
    const msgDiv = document.createElement("div");
    msgDiv.className = "message " + (sent ? "sent" : "received");
    msgDiv.innerText = text;

    document.getElementById("messages").appendChild(msgDiv);
}