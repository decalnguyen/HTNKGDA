let arrow_up = document.getElementById('arrow-up');
let arrow_down = document.getElementById('arrow-down');
let arrow_left = document.getElementById('arrow-left');
let arrow_right = document.getElementById('arrow-right');
let button_change = document.getElementById("button-change");
let button_text = document.getElementById("button-text");

function button_change_mode(){

  button_change.addEventListener("click", () => {
    const isAuto = button_text.textContent === "Auto";

    if (isAuto) {
      // Đổi sang trắng + Control
      button_change.style.backgroundColor = "white";
      button_text.textContent = "Control";
      button_text.style.color = "#b12d2d"; // đổi màu chữ 
    } else {
      // Đổi lại đỏ + Auto
      button_change.style.backgroundColor = "#b12d2d";
      button_text.textContent = "Auto";
      button_text.style.color = "white";
    }
  });
}
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
function ChangeMode(){
  button_change.addEventListener("click", () => {
    fetch("http://localhost:8000/change_mode", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      }
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
      console.error("Error changing mode :", error);
    });
  });
}
button_change_mode();
// arrow_trigger();
RotateUp();
RotateDown();
RotateLeft();
RotateRight();
ChangeMode();