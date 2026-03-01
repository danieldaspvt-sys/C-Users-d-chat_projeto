function renderMedia(payload, type) {
    const div = document.createElement("div");
    div.classList.add("message");
    div.classList.add(payload.username === username ? "me" : "other");

    let element;

    if (type === "image") {
        element = document.createElement("img");
        element.src = payload.data;
        element.style.maxWidth = "200px";
        element.style.borderRadius = "10px";
    }

    if (type === "audio") {
        element = document.createElement("audio");
        element.controls = true;
        element.src = payload.data;
    }

    if (type === "video") {
        element = document.createElement("video");
        element.controls = true;
        element.width = 200;
        element.src = payload.data;
    }

    div.appendChild(element);

    const messages = document.getElementById("messages");
    messages.appendChild(div);
    messages.scrollTop = messages.scrollHeight;
}

socket.on("image", data => renderMedia(data, "image"));
socket.on("audio", data => renderMedia(data, "audio"));
socket.on("video", data => renderMedia(data, "video"));