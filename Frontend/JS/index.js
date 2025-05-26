let arrow_up = document.getElementById('arrow-up');
let arrow_down = document.getElementById('arrow-down');
let arrow_left = document.getElementById('arrow-left');
let arrow_right = document.getElementById('arrow-right');

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
arrow_trigger();