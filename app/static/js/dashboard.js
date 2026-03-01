const socket = io();

let currentChatUser = null;
let pendingAttachment = null;

const usersList = document.getElementById("usersList");
const messagesContainer = document.getElementById("messages");
const chatWith = document.getElementById("chatWith");
const messageInput = document.getElementById("messageInput");

const imageInput = document.getElementById("imageInput");
const audioInput = document.getElementById("audioInput");
const videoInput = document.getElementById("videoInput");

const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024;

socket.on("online_users", function(users) {
    usersList.innerHTML = "";

    users.forEach(user => {
        if (user === window.currentUser) return;

        const div = document.createElement("button");
        div.className = "user-item";
        div.innerText = "@" + user;

        div.onclick = function() {
            startChat(user);
        };

        usersList.appendChild(div);
    });
});

socket.on("chat_history", function(history) {
    messagesContainer.innerHTML = "";
    history.forEach(payload => {
        const isMine = payload.from === window.currentUser;
        addMessage(payload, isMine);
    });
    scrollToBottom();
});

socket.on("private_message", function(data) {
    const fromActiveChat = data.from === currentChatUser || data.to === currentChatUser;

    if (fromActiveChat) {
        addMessage(data, data.from === window.currentUser);
        scrollToBottom();
    }

    if (data.from !== window.currentUser) {
        triggerNotification();
    }
});

function startChat(user) {
    currentChatUser = user;
    chatWith.innerText = "Conversando com @" + user;
    socket.emit("start_chat", { to: user });
    messageInput.focus();
}

function sendMessage() {
    const message = messageInput.value.trim();

    if (!currentChatUser) {
        alert("Selecione um usuário para iniciar o chat privado.");
        return;
    }

    if (!message && !pendingAttachment) {
        return;
    }

    const payload = {
        to: currentChatUser,
        message: message,
        media: pendingAttachment
    };

    socket.emit("private_message", payload);

    messageInput.value = "";
    pendingAttachment = null;
    clearFileInputs();
}

function addMessage(payload, sent) {
    const msgDiv = document.createElement("div");
    msgDiv.className = "message " + (sent ? "sent" : "received");

    if (payload.message) {
        const text = document.createElement("p");
        text.className = "message-text";
        text.innerText = payload.message;
        msgDiv.appendChild(text);
    }

    if (payload.media) {
        msgDiv.appendChild(renderMedia(payload.media));
    }

    const meta = document.createElement("small");
    meta.className = "message-meta";
    meta.innerText = sent ? "Você" : "@" + payload.from;
    msgDiv.appendChild(meta);

    messagesContainer.appendChild(msgDiv);
}

function renderMedia(media) {
    if (media.type === "image") {
        const img = document.createElement("img");
        img.src = media.data;
        img.alt = media.name || "Imagem";
        img.className = "media-item";
        return img;
    }

    if (media.type === "video") {
        const video = document.createElement("video");
        video.src = media.data;
        video.controls = true;
        video.className = "media-item";
        return video;
    }

    if (media.type === "audio") {
        const audio = document.createElement("audio");
        audio.src = media.data;
        audio.controls = true;
        audio.className = "media-item";
        return audio;
    }

    const fallback = document.createElement("a");
    fallback.href = media.data;
    fallback.innerText = media.name || "Arquivo";
    fallback.target = "_blank";
    return fallback;
}

document.getElementById("imageBtn").addEventListener("click", () => imageInput.click());
document.getElementById("audioBtn").addEventListener("click", () => audioInput.click());
document.getElementById("videoBtn").addEventListener("click", () => videoInput.click());

document.getElementById("sendBtn").addEventListener("click", sendMessage);

messageInput.addEventListener("keydown", event => {
    if (event.key === "Enter") {
        sendMessage();
    }
});

imageInput.addEventListener("change", () => prepareAttachment(imageInput.files[0], "image"));
audioInput.addEventListener("change", () => prepareAttachment(audioInput.files[0], "audio"));
videoInput.addEventListener("change", () => prepareAttachment(videoInput.files[0], "video"));

function prepareAttachment(file, type) {
    if (!file) return;

    if (file.size > MAX_FILE_SIZE_BYTES) {
        alert("Arquivo muito grande. Limite de 5MB.");
        clearFileInputs();
        return;
    }

    const reader = new FileReader();
    reader.onload = () => {
        pendingAttachment = {
            type: type,
            name: file.name,
            data: reader.result
        };
        messageInput.placeholder = `Arquivo pronto: ${file.name}`;
        messageInput.focus();
    };
    reader.readAsDataURL(file);
}

function clearFileInputs() {
    imageInput.value = "";
    audioInput.value = "";
    videoInput.value = "";
    messageInput.placeholder = "Digite sua mensagem...";
}

function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function triggerNotification() {
    vibratePhone();
    playNotificationSound();
}

function vibratePhone() {
    if ("vibrate" in navigator) {
        navigator.vibrate([120, 80, 120]);
    }
}

function playNotificationSound() {
    const context = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = context.createOscillator();
    const gainNode = context.createGain();

    oscillator.type = "sine";
    oscillator.frequency.value = 880;

    oscillator.connect(gainNode);
    gainNode.connect(context.destination);

    gainNode.gain.setValueAtTime(0.0001, context.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.15, context.currentTime + 0.02);
    gainNode.gain.exponentialRampToValueAtTime(0.0001, context.currentTime + 0.28);

    oscillator.start(context.currentTime);
    oscillator.stop(context.currentTime + 0.3);
}
