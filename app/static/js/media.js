function handleFile(inputElement, eventName) {
    inputElement.addEventListener("change", function () {
        const file = this.files[0];
        if (!file) return;

        // Limite de 5MB
        if (file.size > 5 * 1024 * 1024) {
            alert("Arquivo muito grande (máx 5MB)");
            this.value = "";
            return;
        }

        const reader = new FileReader();
        reader.onload = function (e) {
            socket.emit(eventName, {
                username: username,
                data: e.target.result
            });
        };

        reader.readAsDataURL(file);
        this.value = ""; // limpa o input
    });
}

handleFile(document.getElementById("imageInput"), "image");
handleFile(document.getElementById("audioInput"), "audio");
handleFile(document.getElementById("videoInput"), "video");