document.getElementById("calc-form").onsubmit = async function (event) {
    event.preventDefault();
    let formData = new FormData(event.target);
    let csrfToken = document.querySelector('input[name="csrfmiddlewaretoken"]').value;

    let response = await fetch("/calc/calculate/", {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken },
        body: formData
    });

    let textResponse = await response.text();
    try {
        let result = JSON.parse(textResponse);
        let resultsContainer = document.getElementById("results");
        resultsContainer.innerHTML = "";

        // Sort years in ascending order
        let sortedYears = Object.keys(result.results).sort((a, b) => a - b);

        for (const year of sortedYears) {
            const indices = result.results[year][year];
            let dropdown = document.createElement("div");
            dropdown.className = "dropdown";

            let header = document.createElement("div");
            header.className = "dropdown-header";
            header.innerHTML = `Year ${year} <span>▼</span>`;
            dropdown.appendChild(header);

            let content = document.createElement("div");
            content.className = "dropdown-content";

            for (const index in indices) {
                let value = indices[index].toFixed(4);
                let { className, explanation } = getColorClassification(index, value);

                let para = document.createElement("p");
                para.innerHTML = `<strong>${index}:</strong> <span class="${className}">${value}</span> - ${explanation}`;
                content.appendChild(para);
            }

            dropdown.appendChild(content);
            resultsContainer.appendChild(dropdown);

            // Add click event to toggle dropdown
            header.addEventListener("click", function () {
                content.style.display = content.style.display === "block" ? "none" : "block";
                header.innerHTML = `Year ${year} <span>${content.style.display === "block" ? "▲" : "▼"}</span>`;
            });
        }

        let graphContainer = document.getElementById("graph-container");
        let graphSelector = document.getElementById("graph-selector");
        graphContainer.innerHTML = "";
        graphSelector.innerHTML = "";

        if (result.graphs) {
            graphSelector.style.display = "block"; // Show the dropdown
            for (const [index, graphUrl] of Object.entries(result.graphs)) {
                let option = document.createElement("option");
                option.value = graphUrl;
                option.textContent = index;
                graphSelector.appendChild(option);
            }
            graphSelector.addEventListener("change", function () {
                let img = document.createElement("img");
                img.src = this.value;
                img.alt = "Selected Graph";
                img.style.width = "100%";
                img.style.height = "auto";

                graphContainer.innerHTML = "";
                graphContainer.appendChild(img);
            });
            graphSelector.dispatchEvent(new Event("change"));
        }
    } catch (error) {
        console.error("Error parsing JSON:", error);
        document.getElementById("results").innerText = "Error: Invalid JSON response from server.";
    }
};

function getColorClassification(index, value) {
    value = parseFloat(value);
    let thresholds = {
        "AWEI": [0, null],
        "EVI": [0.1, 0.2],
        "GCI": [1.5, 3.5],
        "LST": [283, 293, 313], // Updated to Kelvin thresholds
        "NDMI": [0, 0.3],
        "NDSI": [0.2, 0.4],
        "NDVI": [0.2, 0.6]
    };
    let limits = thresholds[index] || [0.3, 0.6];
    let explanation = "";

    if (index === "AWEI") {
        explanation = value > 0 ? "Indicates water presence." : "Indicates non-water areas.";
    } else if (index === "EVI") {
        explanation = value > 0.2 ? "Healthy vegetation." : "Bare land or non-vegetated surfaces.";
    } else if (index === "GCI") {
        explanation = value > 3.5 ? "High chlorophyll content, healthy vegetation." : "Low chlorophyll levels, stressed vegetation.";
    } else if (index === "LST") {
        if (value < 283) explanation = "Cold regions, snow, or high-altitude areas.";
        else if (value < 293) explanation = "Moderate climates, forests, and vegetation-covered areas.";
        else if (value > 313) explanation = "Hot deserts, bare soil, or urban heat islands.";
    } else if (index === "NDMI") {
        if (value > 0.3) explanation = "High vegetation water content (healthy vegetation).";
        else if (value >= 0) explanation = "Moderate moisture levels.";
        else explanation = "Dry vegetation or soil.";
    } else if (index === "NDSI") {
        explanation = value > 0.4 ? "Snow-covered areas." : "No snow or mixed land cover.";
    } else if (index === "NDVI") {
        if (value > 0.6) explanation = "Dense, healthy vegetation.";
        else if (value >= 0.2) explanation = "Moderate vegetation.";
        else explanation = "Sparse vegetation, bare soil, or non-vegetated surfaces.";
    }

    let className = "low";
    if (limits.length === 2) {
        if (value < limits[0]) className = "low";
        else if (value < limits[1]) className = "moderate";
        else className = "high";
    } else if (limits.length === 3) {
        if (value < limits[0]) className = "low";
        else if (value < limits[1]) className = "moderate";
        else if (value < limits[2]) className = "high";
        else className = "very-high";
    }

    return { className, explanation };
}