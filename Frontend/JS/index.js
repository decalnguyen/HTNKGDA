let arrow_up = document.getElementById('arrow-up');
let arrow_down = document.getElementById('arrow-down');
let arrow_left = document.getElementById('arrow-left');
let arrow_right = document.getElementById('arrow-right');
let button_change = document.getElementById("button-change");
let button_text = document.getElementById("button-text");

function arrow_trigger(){
    arrow_up.addEventListener('click',()=>{
        alert("Arrow up picked");
    });
    arrow_down.addEventListener('click',()=>{
        alert("Arrow down picked");
    });
    arrow_left.addEventListener('click',()=>{
        alert("Arrow left picked");
    });
    arrow_right.addEventListener('click',()=>{
        alert("Arrow right picked");
    });
}
function RotateUp(){
  arrow_up .addEventListener("click", () => {
    fetch("http://localhost:8000/rotate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ direction: "rotate-up" }),
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
      console.error("Error sending direction up: ", error);
    });
  });
}
function RotateDown(){
  arrow_down .addEventListener("click", () => {
    fetch("http://localhost:8000/rotate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ direction: "rotate-down" }),
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
  arrow_left .addEventListener("click", () => {
    fetch("http://localhost:8000/rotate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ direction: "rotate-left" }),
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
  arrow_right .addEventListener("click", () => {
    fetch("http://localhost:8000/rotate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ direction: "rotate-right" }),
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

const ws = new WebSocket("ws://localhost:8000/ws/image");

let currentStatus = "No Fire";
let blink = false;

const statusTextEl = document.getElementById("button-text");
const statusContainer = document.getElementById("fire-status");

// Hàm nhấp nháy định kỳ
setInterval(() => {
    blink = !blink;

    if (currentStatus === "Fire Detected") {
        statusContainer.style.backgroundColor = blink ? "#ff0000" : "#880000";
        statusTextEl.style.color = "white";
    } else {
        statusContainer.style.backgroundColor = blink ? "#00cc00" : "#006600";
        statusTextEl.style.color = "white";
    }
}, 500); // 500ms = 0.5s

// Khi nhận được WebSocket message, chỉ cập nhật trạng thái hiện tại
ws.onmessage = function (event) {
    currentStatus = event.data;
    console.log("Trạng thái nhận được:", currentStatus);
    statusTextEl.textContent = currentStatus;
};


RotateUp();
RotateDown();
RotateLeft();
RotateRight();
