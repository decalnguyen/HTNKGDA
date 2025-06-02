let arrow_up = document.getElementById('arrow-up');
let arrow_down = document.getElementById('arrow-down');
let arrow_left = document.getElementById('arrow-left');
let arrow_right = document.getElementById('arrow-right');
let button_change = document.getElementById("button-change");
let button_text = document.getElementById("button-text");

const BASE_URL = window?.env?.BASE_URL || "http://localhost:8000";  // fallback if env not defined

function RotateUp(){
  arrow_up.addEventListener("click", () => {
    fetch(`${BASE_URL}/servo/control`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ code : 1}),
    })
    console.log(4,`${BASE_URL}`)
    .then((response) => {
      if (!response.ok) {
        throw new Error("Server error: " + response.statusText);
      }
      return response.json();
    })
    .then((data) => {
      console.log("Server responded:", data);
    })
    .catch((error) => {
      console.error("Error sending direction up: ", error);
    });
  });
}

function RotateDown(){
  arrow_down.addEventListener("click", () => {
    fetch(`${BASE_URL}/servo/control`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ code: 3}),
    })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Server error: " + response.statusText);
      }
      return response.json();
    })
    .then((data) => {
      console.log("Server responded:", data);
    })
    .catch((error) => {
      console.error("Error sending direction down: ", error);
    });
  });
}

function RotateLeft(){
  arrow_left.addEventListener("click", () => {
    fetch(`${BASE_URL}/servo/control`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ code: 4 }),
    })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Server error: " + response.statusText);
      }
      return response.json();
    })
    .then((data) => {
      console.log("Server responded:", data);
    })
    .catch((error) => {
      console.error("Error sending direction left:", error);
    });
  });
}

function RotateRight(){
  arrow_right.addEventListener("click", () => {
    fetch(`${BASE_URL}/servo/control`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({code: 2 }),
    })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Server error: " + response.statusText);
      }
      return response.json();
    })
    .then((data) => {
      console.log("Server responded:", data);
    })
    .catch((error) => {
      console.error("Error sending direction right:", error);
    });
  });
}

RotateUp();
RotateDown();
RotateLeft();
RotateRight();
