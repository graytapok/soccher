/**
 * 
 * @param {HTMLTableElement} table the table to sort
 * @param {number} column column to sort
 * @param {boolean} asc sorting increasing or decreasing
 */
function sortTableByColumn(table, column, asc = true) {
    const dirModifier = asc ? 1 : -1;
    const tBody = table.tBodies[0];
    const rows = Array.from(tBody.querySelectorAll("tr"));

    // Sort each Row
    const sortedRows = rows.sort((a, b) => {
        let aColTest = a.querySelector(`td:nth-child(${column+1})`).textContent.trim();
        let bColTest = b.querySelector(`td:nth-child(${column+1})`).textContent.trim();

        switch (column) {
            case 1:
                return aColTest > bColTest ? (1 * dirModifier) : (-1 * dirModifier);
            case 0:
            case 2:
            case 3:
            case 4:
                return parseFloat(aColTest) > parseFloat(bColTest) ? (1 * dirModifier) : (-1 * dirModifier);
        }
    });

    // Remove all existing Trs from the table
    while(tBody.firstChild) {
        tBody.removeChild(tBody.firstChild);
    };

    // Readd the newly sorted rows
    tBody.append(...sortedRows);

    // Remember how the column is currently sorted
    table.querySelectorAll("th").forEach(th => th.classList.remove("th-sort-asc", "th-sort-desc"));
    table.querySelector(`th:nth-child(${column+1})`).classList.toggle("th-sort-asc", asc);
    table.querySelector(`th:nth-child(${column+1})`).classList.toggle("th-sort-desc", !asc);
};

document.querySelectorAll(".ranking_table th").forEach(headerCell => {
    headerCell.addEventListener("click", () => {
        const tableElement = headerCell.parentElement.parentElement.parentElement;
        const headerIndex = Array.prototype.indexOf.call(headerCell.parentElement.children, headerCell);
        const currentIsAscending = headerCell.classList.contains("th-sort-asc");

        if ((headerIndex != 5 && headerIndex != 3) && currentIsAscending) {
            document.querySelectorAll(".fa-up-long").forEach(arrow => {
                arrow.style.color = "rgba(255, 255, 255, .5)";
            });
            document.querySelectorAll(".fa-down-long").forEach(arrow => {
                arrow.style.color = "rgba(255, 255, 255, .5)";
            });
            headerCell.querySelectorAll(".fa-up-long").forEach(arrow => {
                arrow.style.color = "rgb(255, 255, 255)";
            });
        } else if ((headerIndex != 5 && headerIndex != 3) && !currentIsAscending) {
            document.querySelectorAll(".fa-up-long").forEach(arrow => {
                arrow.style.color = "rgba(255, 255, 255, .5)";
            });
            document.querySelectorAll(".fa-down-long").forEach(arrow => {
                arrow.style.color = "rgba(255, 255, 255, .5)";
            });
            headerCell.querySelectorAll(".fa-down-long").forEach(arrow => {
                arrow.style.color = "rgb(255, 255, 255)";
            });
        };

        switch (headerIndex) {
            case 2:
                sortTableByColumn(tableElement, headerIndex, currentIsAscending);
            case 0:
            case 1:
            case 4:
                sortTableByColumn(tableElement, headerIndex, !currentIsAscending);
        };
    });
});


// Coloring the points
document.querySelectorAll("#diff_points").forEach(val => {
    const num = val.innerHTML.trim()
    if (num > 0) {
        val.style.color = "rgb(var(--green_button))";
    } else if (num < 0) {
        val.style.color = "rgb(var(--red_button))";
    } else {
        val.style.color = "rgba(255, 255, 255, 0.5)"
    };
});

// Coloring the ranking
document.querySelectorAll("#diff_ranking").forEach(val => {
    const num = val.innerHTML.trim();
    if (num > 0) {
        val.style.color = "rgb(var(--green_button))";
    } else if (num < 0) {
        val.style.color = "rgb(var(--red_button))";
    } else {
        val.style.color = "rgba(255, 255, 255, 0.5)";
    };
});