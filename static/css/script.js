document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById("loginModal");
    const modalBg = document.getElementById("modalBackground");
    const closeBtn = document.getElementById("closeModal");
  
    const loginTriggers = document.querySelectorAll(".login-trigger");
  
    loginTriggers.forEach(link => {
      link.addEventListener("click", function (e) {
        e.preventDefault();
        modal.style.display = "block";
        modalBg.style.display = "block";
      });
    });
  
    closeBtn.addEventListener("click", () => {
      modal.style.display = "none";
      modalBg.style.display = "none";
    });
  
    modalBg.addEventListener("click", () => {
      modal.style.display = "none";
      modalBg.style.display = "none";
    });
  });
  