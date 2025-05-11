document.querySelector("#login").addEventListener("submit", function(event) {
    let username = document.getElementById("username").value.trim();
    let password = document.getElementById("password").value.trim();

    if (!username || !password) {
        alert("Please enter both username and password.");
        event.preventDefault();
    }
});