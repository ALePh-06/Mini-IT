document.getElementById('login').addEventListener('input', function() {
    const ID = document.getElementById('ID').value.trim();
    const password = document.getElementById('password').value.trim();
    const LoginButton = document.getElementById('LoginButton');
    
    // Enable the button if both fields have values
    if (ID && password) {
        LoginButton.disabled = false;
    } else {
        LoginButton.disabled = true;
    }
});

document.getElementById('SignUp').addEventListener('input', function() {
    const password = document.getElementById('password').value.trim();
    const ConfirmPassword = document.getElementById("confirmPassword").value;
    const SignUpButton = document.getElementById('SignUpButton');
    
    // Enable the button if both fields have values
    if (password !== ConfirmPassword) {
        SignUpButton.disabled = true;
    } else {
        SignUpButton.disabled = false;
    }
});