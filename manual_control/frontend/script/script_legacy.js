function sendCommand(command, action) {
    fetch('/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: command, action: action }) // Send action type
    }).then(response => response.json())
      .then(data => console.log(data))
      .catch(error => console.error('Error:', error));
}

// Attach event listeners for each button
document.addEventListener("DOMContentLoaded", function() {
    const buttons = {
        forward: document.querySelector('.btn-forward'),
        left: document.querySelector('.btn-left'),
        stop: document.querySelector('.btn-stop'),
        right: document.querySelector('.btn-right'),
        backward: document.querySelector('.btn-backward')
    };

    Object.keys(buttons).forEach(direction => {
        buttons[direction].addEventListener("mousedown", function() {
            sendCommand(direction, "start"); // Send "start" when button is pressed
        });

        buttons[direction].addEventListener("mouseup", function() {
            sendCommand(direction, "stop"); // Send "stop" when button is released
        });

        // Also handle mobile touch events
        buttons[direction].addEventListener("touchstart", function(event) {
            event.preventDefault(); // Prevent accidental double events
            sendCommand(direction, "start");
        });

        buttons[direction].addEventListener("touchend", function() {
            sendCommand(direction, "stop");
        });
    });
});
