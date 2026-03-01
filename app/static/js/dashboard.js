const socket = io();

let currentChatUser = null;
let pendingAttachment = null;
const onlineFriends = new Set();
const MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024;

const messagesContainer = document.getElementById("messages");
const messageInput = document.getElementById("messageInput");
const chatWith = document.getElementById("chatWith");
const friendsList = document.getElementById("friendsList");
const groupsList = document.getElementById("groupsList");
const pendingList = document.getElementById("pendingList");
const outgoingList = document.getElementById("outgoingList");
const feedbackText = document.getElementById("feedbackText");
const statusText = document.getElementById("statusText");

const imageInput = document.getElementById("imageInput");
const audioInput = document.getElementById("audioInput");
const videoInput = document.getElementById("videoInput");

const friendSearchForm = document.getElementById("friendSearchForm");
friendSearchForm.addEventListener("submit", (event) => {
    event.preventDefault();
    sendFriendRequest();
});

socket.on("friends_online", (users) => {
    onlineFriends.clear();
    users.forEach((u) => onlineFriends.add(u));
    loadFriends();
});

socket.on("friend_presence", (payload) => {
    if (payload.online) onlineFriends.add(payload.username);
    else onlineFriends.delete(payload.username);
    loadFriends();
});

socket.on("chat_error", (data) => showFeedback(data.message, true));

socket.on("chat_history", (history) => {
    messagesContainer.innerHTML = "";
    history.forEach((msg) => addMessage(msg, msg.from === window.currentUser));
    scrollToBottom();
});

socket.on("private_message", (msg) => {
    if (msg.from === currentChatUser || msg.to === currentChatUser) {
        addMessage(msg, msg.from === window.currentUser);
        scrollToBottom();
    }
    if (msg.from !== window.currentUser) triggerNotification();
});

async function loadFriends() {
    const res = await fetch("/api/friends");
    const data = await res.json();

    friendsList.innerHTML = "";
    if (data.friends.length === 0) {
        friendsList.innerHTML = '<div class="empty-text">Sem amigos ainda. Adicione alguém pelo campo acima.</div>';
    }

    data.friends.forEach((friend) => {
        const item = document.createElement("div");
        item.className = "friend-item";
        item.innerHTML = `
            <div class="user-meta" data-user="${friend.username}">
                <img class="avatar-sm" src="/static/${friend.profile_image}" alt="avatar">
                <span>@${friend.username}</span>
            </div>
            <span class="status-dot ${onlineFriends.has(friend.username) ? "online" : ""}"></span>
        `;
        item.querySelector(".user-meta").onclick = () => startChat(friend.username);
        friendsList.appendChild(item);
    });

    pendingList.innerHTML = "";
    if (data.pending.length === 0) {
        pendingList.innerHTML = '<div class="empty-text">Sem solicitações pendentes.</div>';
    }

    data.pending.forEach((pending) => {
        const row = document.createElement("div");
        row.className = "pending-item";
        row.innerHTML = `
            <div class="user-meta">
                <img class="avatar-sm" src="/static/${pending.profile_image}" alt="avatar">
                <span>@${pending.username}</span>
            </div>
            <div>
                <button class="mini-btn accept" data-action="accept">✓</button>
                <button class="mini-btn reject" data-action="reject">✕</button>
            </div>
        `;
        row.querySelector('[data-action="accept"]').onclick = () => respondRequest(pending.username, "accept");
        row.querySelector('[data-action="reject"]').onclick = () => respondRequest(pending.username, "reject");
        pendingList.appendChild(row);
    });

    outgoingList.innerHTML = "";
    if ((data.outgoing || []).length === 0) {
        outgoingList.innerHTML = '<div class="empty-text">Nenhuma solicitação enviada.</div>';
    }

    (data.outgoing || []).forEach((pending) => {
        const row = document.createElement("div");
        row.className = "pending-item";
        row.innerHTML = `
            <div class="user-meta">
                <img class="avatar-sm" src="/static/${pending.profile_image}" alt="avatar">
                <span>@${pending.username}</span>
            </div>
            <div class="empty-text">Aguardando</div>
        `;
        outgoingList.appendChild(row);
    });
}

async function loadGroups() {
    const res = await fetch("/api/groups");
    const data = await res.json();
    groupsList.innerHTML = "";

    if (!data.groups || data.groups.length === 0) {
        groupsList.innerHTML = '<div class="empty-text">Nenhum grupo. O admin pode criar e te adicionar.</div>';
        return;
    }

    data.groups.forEach((group) => {
        const row = document.createElement("div");
        row.className = "friend-item";
        row.innerHTML = `<div><strong>👥 ${group.name}</strong><br><small>${group.role} ${group.muted ? '- silenciado' : ''}</small></div>`;
        groupsList.appendChild(row);
    });
}

async function loadStatus() {
    const res = await fetch("/api/status");
    const data = await res.json();
    statusText.textContent = `Status: ${data.status || "Sem status"}`;
}

async function sendFriendRequest() {
    const input = document.getElementById("friendSearch");
    const username = input.value.trim().replace(/^@/, "");
    if (!username) {
        showFeedback("Digite um username para adicionar.", true);
        return;
    }

    const res = await fetch("/api/friends/request", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username }),
    });

    const data = await res.json();
    showFeedback(data.message, !res.ok);
    if (res.ok) input.value = "";
    loadFriends();
}

async function respondRequest(username, action) {
    const res = await fetch("/api/friends/respond", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, action }),
    });
    const data = await res.json();
    showFeedback(data.message, !res.ok);
    loadFriends();
}

function showFeedback(message, isError = false) {
    feedbackText.textContent = message;
    feedbackText.classList.toggle("error", isError);
}

function startChat(username) {
    currentChatUser = username;
    chatWith.innerText = `Conversando com @${username}`;
    socket.emit("start_chat", { to: username });
}

function sendMessage() {
    const text = messageInput.value.trim();
    if (!currentChatUser) return showFeedback("Escolha um amigo na lista para iniciar o chat.", true);
    if (!text && !pendingAttachment) return;

    socket.emit("private_message", {
        to: currentChatUser,
        message: text,
        media: pendingAttachment,
    });

    messageInput.value = "";
    pendingAttachment = null;
    clearFileInputs();
}

function addMessage(payload, sent) {
    const node = document.createElement("div");
    node.className = `message ${sent ? "sent" : "received"}`;

    if (payload.message) {
        const p = document.createElement("p");
        p.textContent = payload.message;
        node.appendChild(p);
    }

    if (payload.media) node.appendChild(renderMedia(payload.media));

    const meta = document.createElement("small");
    meta.className = "message-meta";
    meta.textContent = sent ? "Você" : `@${payload.from}`;
    node.appendChild(meta);

    messagesContainer.appendChild(node);
}

function renderMedia(media) {
    if (media.type === "image") {
        const i = document.createElement("img");
        i.className = "media-item";
        i.src = media.data;
        return i;
    }
    if (media.type === "video") {
        const v = document.createElement("video");
        v.className = "media-item";
        v.controls = true;
        v.src = media.data;
        return v;
    }
    if (media.type === "audio") {
        const a = document.createElement("audio");
        a.className = "media-item";
        a.controls = true;
        a.src = media.data;
        return a;
    }
    if (media.type === "profile") {
        const span = document.createElement("div");
        span.innerText = `🔗 Perfil compartilhado: @${media.username}`;
        return span;
    }
    const fallback = document.createElement("a");
    fallback.href = media.data;
    fallback.textContent = media.name || "Arquivo";
    return fallback;
}

function prepareAttachment(file, type) {
    if (!file) return;
    if (file.size > MAX_FILE_SIZE_BYTES) {
        showFeedback("Arquivo maior que 5MB", true);
        clearFileInputs();
        return;
    }
    const reader = new FileReader();
    reader.onload = () => {
        pendingAttachment = { type, name: file.name, data: reader.result };
        showFeedback(`Mídia pronta para envio: ${file.name}`);
    };
    reader.readAsDataURL(file);
}

function clearFileInputs() {
    imageInput.value = "";
    audioInput.value = "";
    videoInput.value = "";
}

function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function triggerNotification() {
    if ("vibrate" in navigator) navigator.vibrate([100, 60, 100]);
}

document.getElementById("sendBtn").addEventListener("click", sendMessage);
messageInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendMessage();
});

document.getElementById("imageBtn").onclick = () => imageInput.click();
document.getElementById("audioBtn").onclick = () => audioInput.click();
document.getElementById("videoBtn").onclick = () => videoInput.click();

imageInput.addEventListener("change", () => prepareAttachment(imageInput.files[0], "image"));
audioInput.addEventListener("change", () => prepareAttachment(audioInput.files[0], "audio"));
videoInput.addEventListener("change", () => prepareAttachment(videoInput.files[0], "video"));

document.getElementById("shareProfileBtn").onclick = () => {
    if (!currentChatUser) return showFeedback("Escolha um amigo para compartilhar perfil.", true);
    socket.emit("private_message", {
        to: currentChatUser,
        message: "",
        media: { type: "profile", username: window.currentUser },
    });
};

document.getElementById("statusBtn").onclick = async () => {
    const text = prompt("Digite seu novo status:");
    if (!text) return;
    const res = await fetch("/api/status", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
    });
    const data = await res.json();
    showFeedback(data.message, !res.ok);
    loadStatus();
};

document.getElementById("storyBtn").onclick = async () => {
    const content = prompt("Digite seu story:");
    if (!content) return;
    const res = await fetch("/api/stories", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content }),
    });
    const data = await res.json();
    showFeedback(data.message, !res.ok);
};

document.getElementById("videoCallBtn").onclick = () => {
    if (!currentChatUser) return showFeedback("Escolha um amigo para iniciar chamada.", true);
    const room = [window.currentUser, currentChatUser].sort().join("-");
    const callUrl = `${window.location.origin}/call/${room}`;
    navigator.clipboard?.writeText(callUrl);
    showFeedback("Link de chamada gerado e copiado. Envie ao contato.");
};

loadFriends();
loadGroups();
loadStatus();
