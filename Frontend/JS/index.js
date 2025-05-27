let arrow_up = document.getElementById('arrow-up');
let arrow_down = document.getElementById('arrow-down');
let arrow_left = document.getElementById('arrow-left');
let arrow_right = document.getElementById('arrow-right');
let buttonChange = document.getElementById("button-change");
let buttonText = document.getElementById("button-text");

function button_change_mode(){

  buttonChange.addEventListener("click", () => {
    const isAuto = buttonText.textContent === "Auto";

    if (isAuto) {
      // Đổi sang trắng + Control
      buttonChange.style.backgroundColor = "white";
      buttonText.textContent = "Control";
      buttonText.style.color = "#b12d2d"; // đổi màu chữ 
    } else {
      // Đổi lại đỏ + Auto
      buttonChange.style.backgroundColor = "#b12d2d";
      buttonText.textContent = "Auto";
      buttonText.style.color = "white";
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
button_change_mode();
// arrow_trigger();