document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("searchInput");
    const tableBody = document.getElementById("tableBody");
    const searchBtn = document.getElementById("searchBtn");
    const autocomplete = document.getElementById("autocomplete");
    const recommendationsDiv = document.getElementById("recommendations");

    // Filtros
    const filterRestaurant = document.getElementById("filterRestaurant");
    const filterCategory   = document.getElementById("filterCategory");
    const filterSeals      = document.getElementById("filterSeals");
    const filterMinCal  = document.getElementById("filterMinCal");
    const filterMaxCal  = document.getElementById("filterMaxCal");
    const filterMinProt = document.getElementById("filterMinProt");
    const filterMaxProt = document.getElementById("filterMaxProt");
    const filterMinFat  = document.getElementById("filterMinFat");
    const filterMaxFat  = document.getElementById("filterMaxFat");
    const filterMinCarb = document.getElementById("filterMinCarbs");
    const filterMaxCarb = document.getElementById("filterMaxCarbs");

    // --------------------------
    // Inicializar filtros dinámicos
    // --------------------------
    function initFilters() {
        const restaurants = [...new Set(allItems.map(i => i.company))].sort();
        filterRestaurant.innerHTML = "";
        filterRestaurant.appendChild(new Option("Todos", ""));
        restaurants.forEach(r => filterRestaurant.appendChild(new Option(r, r)));

        const categories = [...new Set(allItems.map(i => i.category))].sort();
        filterCategory.innerHTML = "";
        filterCategory.appendChild(new Option("Todas", ""));
        categories.forEach(c => filterCategory.appendChild(new Option(c, c)));

        const allSeals = [...new Set(allItems.flatMap(i => i.seals || []))].sort();
        filterSeals.innerHTML = "";
        filterSeals.appendChild(new Option("Todos", ""));
        filterSeals.appendChild(new Option("Ninguno", "none"));
        allSeals.forEach(s => filterSeals.appendChild(new Option(s, s)));
    }
    initFilters();

    // --------------------------
    // Función de filtrado avanzado
    // --------------------------
    function applyFilters(list) {
        const rest = filterRestaurant.value;
        const cat  = filterCategory.value;
        const seals = filterSeals.value;

        const minCal = Number(filterMinCal.value || 0);
        const maxCal = Number(filterMaxCal.value || Infinity);
        const minProt = Number(filterMinProt.value || 0);
        const maxProt = Number(filterMaxProt.value || Infinity);
        const minFat = Number(filterMinFat.value || 0);
        const maxFat = Number(filterMaxFat.value || Infinity);
        const minCarb = Number(filterMinCarb.value || 0);
        const maxCarb = Number(filterMaxCarb.value || Infinity);

        return list.filter(p => {
            if (rest && p.company !== rest) return false;
            if (cat && p.category !== cat) return false;
            if (p.calories < minCal || p.calories > maxCal) return false;
            if (p.protein  < minProt || p.protein  > maxProt) return false;
            if (p.fat      < minFat  || p.fat      > maxFat) return false;
            if (p.carbs    < minCarb || p.carbs    > maxCarb) return false;

            if (seals === "none") {
                if (p.seals && p.seals.length > 0) return false;
            } else if (seals) {
                if (!p.seals || !p.seals.includes(seals)) return false;
            }

            return true;
        });
    }

    // --------------------------
    // Renderizar tabla
    // --------------------------
    function renderTable(items) {
        const table = document.getElementById("menuTable");
        const thead = table.querySelector("thead");
        tableBody.innerHTML = "";

        if (!items || items.length === 0) return;

        // Columnas fijas en el orden deseado
        const columns = [
            "company", "name", "category",
            "calories", "protein", "fat", "carbs",
            "saturatedFat", "sodium", "sugars",
            "seals"
        ];

        // Renderizar cabecera
        thead.innerHTML = "<tr>" + columns.map(c => `<th>${c.charAt(0).toUpperCase() + c.slice(1)}</th>`).join("") + "</tr>";

        // Renderizar filas
        tableBody.innerHTML = items.map(item => {
            return `<tr>` + columns.map(col => {
                const value = item[col];
                if (Array.isArray(value)) {
                    return `<td>${value.map(v => `<span class="badge bg-danger text-white">${v}</span>`).join(" ")}</td>`;
                } else if (value === null || value === undefined || value === "") {
                    return `<td><span class="text-muted">—</span></td>`;
                } else {
                    return `<td>${value}</td>`;
                }
            }).join("") + `</tr>`;
        }).join("");
    }

    // --------------------------
    // Autocompletado
    // --------------------------
    input.addEventListener("input", () => {
        const query = input.value.toLowerCase();
        autocomplete.innerHTML = "";
        if (!query) return;
        const matches = allItems.filter(p => p.name.toLowerCase().includes(query)).slice(0, 5);
        matches.forEach(p => {
            const a = document.createElement("a");
            a.className = "list-group-item list-group-item-action";
            a.textContent = p.name;
            a.addEventListener("click", () => {
                input.value = p.name;
                autocomplete.innerHTML = "";
                searchBtn.click();
            });
            autocomplete.appendChild(a);
        });
    });

    // --------------------------
    // Botón Buscar
    // --------------------------
    searchBtn.addEventListener("click", async () => {
        const query = input.value.trim().toLowerCase();
        let filtered = allItems.filter(p => p.name.toLowerCase().includes(query));
        filtered = applyFilters(filtered);
        renderTable(filtered);

        if (filtered.length > 0) await fetchRecommendations(filtered[0].name);
        else recommendationsDiv.innerHTML = "";
        autocomplete.innerHTML = "";
    });

    // --------------------------
    // Doble click fila → búsqueda rápida
    // --------------------------
    tableBody.addEventListener("dblclick", e => {
        const row = e.target.closest("tr");
        if (!row) return;
        const nameCell = row.querySelector("td:nth-child(2)");
        if (nameCell) {
            input.value = nameCell.textContent;
            searchBtn.click();
        }
    });

    // --------------------------
    // Recomendaciones
    // --------------------------
    async function fetchRecommendations(nombre) {
        try {
            const res = await fetch(`/recomendar?nombre=${encodeURIComponent(nombre)}`);
            const data = await res.json();
            renderRecommendations(data.recomendaciones);
        } catch (err) {
            console.error("Error al obtener recomendaciones:", err);
        }
    }

    function renderRecommendations(recommendations) {
        recommendationsDiv.innerHTML = recommendations.map(r => `
            <div class="col-md-4 mb-3">
                <div class="card card-hover h-100 p-3" data-name="${r.name}">
                    <h5 class="card-title text-success fw-bold">${r.name}</h5>
                    <p class="card-text">${r.company}</p>
                    <div class="d-flex flex-wrap gap-2 mb-2">
                        <span class="badge bg-warning text-dark">Cal: ${r.calories}</span>
                        <span class="badge bg-info text-dark">Prot: ${r.protein}g</span>
                        <span class="badge bg-danger text-white">Grasa: ${r.fat}g</span>
                        <span class="badge bg-secondary text-white">Carbs: ${r.carbs}g</span>
                    </div>
                    <div class="small mb-2 text-muted">
                        Azúcares: ${r.sugars}g<br>
                        Grasa Saturada: ${r.saturatedFat}g<br>
                        Sodio: ${r.sodium}mg
                    </div>
                    <div>
                        ${r.seals && r.seals.length > 0 
                            ? r.seals.map(s => `<span class="badge bg-danger text-white">${s}</span>`).join(" ")
                            : `<span class="text-muted">Sin sellos</span>`
                        }
                    </div>
                </div>
            </div>
        `).join("");

        document.querySelectorAll(".card-hover").forEach(card => {
            card.addEventListener("click", () => {
                input.value = card.getAttribute("data-name");
                searchBtn.click();
            });
        });
    }

    // Render inicial
    renderTable(allItems);
});
