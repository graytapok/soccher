function changeIcon() {
    const icon = document.getElementById("drop_icon");
    const styleMenu = document.querySelector(".menu").style;
    if (icon.classList.value === "fas fa-solid fa-bars") {
        let opacity = 0;
        icon.classList.remove("fas", "fa-solid", "fa-bars");
        icon.classList.add("fa-regular", "fa-circle-xmark", "fa-sm");
        styleMenu.opacity = opacity;
        styleMenu.display = "block";
        setInterval(() => {
            if (opacity < 0.99) {
                opacity += 0.33;
                styleMenu.opacity = opacity;
            } else {
                return;
            };
        }, 10);
    } else {
        let opacity = 0.99;
        icon.classList.remove("fa-regular", "fa-circle-xmark", "fa-sm");
        icon.classList.add("fas", "fa-solid", "fa-bars");
        styleMenu.opacity = opacity;
        setInterval(() => {
            if (opacity > 0) {
                opacity -= 0.33;
                styleMenu.opacity = opacity;
            } else {
                return;
            };
        }, 10);
        styleMenu.display = "none";
    }
    icon.style.width = "22px";
};

logOutHideMenu = function() {
    const logoutMenu = document.querySelector(".logout_container");
    logoutMenu.style.opacity = "1";
    logoutMenu.style.display = "none";
    
}

logOutShowMenu = function() {
    let opacity = 0;
    const logoutMenu = document.querySelector(".logout_container");
    logoutMenu.style.opacity = "0";
    logoutMenu.style.display = "flex";
    setInterval(() => {
        if (opacity != 1) {
            opacity += 0.1;
            logoutMenu.style.opacity = opacity;
        } else {
            return;
        };
    }, 10);
};