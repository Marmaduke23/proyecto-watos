document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("searchInput");
    const tableBody = document.getElementById("tableBody");
    const autocomplete = document.getElementById("autocomplete");
    const recommendationsDiv = document.getElementById("recommendations");
    const searchBtn = document.getElementById("searchBtn");

    // --------------------------
    // Filtros
    // --------------------------
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

        // Restaurante
        const restaurants = [...new Set(allItems.map(i => i.company))].sort();
        restaurants.forEach(r => {
            const op = document.createElement("option");
            op.value = r;
            op.textContent = r;
            filterRestaurant.appendChild(op);
        });

        // Categoría
        const categories = [...new Set(allItems.map(i => i.category))].sort();
        categories.forEach(c => {
            const op = document.createElement("option");
            op.value = c;
            op.textContent = c;
            filterCategory.appendChild(op);
        });
    }
    initFilters();



    // --------------------------
    // Función general de filtrado avanzado
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

            if (seals === "sin" && p.seals && p.seals.length > 0) return false;
            if (seals === "con" && (!p.seals || p.seals.length === 0)) return false;

            return true;
        });
    }


    // --------------------------
    // Autocompletado mientras escribes
    // --------------------------
    input.addEventListener("input", () => {
        const query = input.value.toLowerCase();
        if (!query) {
            autocomplete.innerHTML = "";
            return;
        }
        const matches = allItems
            .filter(p => p.name.toLowerCase().includes(query))
            .slice(0, 5);
        showAutocomplete(matches);
    });

    function showAutocomplete(items) {
        autocomplete.innerHTML = "";
        items.forEach(p => {
            const el = document.createElement("a");
            el.className = "list-group-item list-group-item-action";
            el.textContent = p.name;
            el.addEventListener("click", () => {
                input.value = p.name;
                autocomplete.innerHTML = "";
                searchBtn.click(); // ejecuta búsqueda automáticamente
            });
            autocomplete.appendChild(el);
        });
    }

    // --------------------------
    // Click en botón Buscar
    // --------------------------
    searchBtn.addEventListener("click", async () => {
        let query = input.value.trim().toLowerCase();

        // Filtrar primero por nombre
        let filtered = allItems.filter(p =>
            p.name.toLowerCase().includes(query)
        );

        // Aplicar filtros avanzados (restaurante, categoría, rangos, sellos)
        filtered = applyFilters(filtered);

        // Renderizar tabla filtrada
        renderTable(filtered);

        // Habilitar selección de filas
        enableTableSelection();

        // Recomendaciones desde el backend
        if (filtered.length > 0) {
            await fetchRecommendations(filtered[0].name);
        } else {
            recommendationsDiv.innerHTML = "";
        }

        // Limpiar autocompletado
        autocomplete.innerHTML = "";
    });

    // --------------------------
    // Renderizar tabla
    // --------------------------
    function renderTable(items) {
        tableBody.innerHTML = items.map(p => `
            <tr>
                <td>${p.company}</td>
                <td>${p.name}</td>
                <td>${p.category}</td>
                <td>${p.calories}</td>
                <td>${p.protein}</td>
                <td>${p.fat}</td>
                <td>${p.carbs}</td>
                <td>
                    ${p.seals && p.seals.length > 0 
                        ? p.seals.map(s => `<span class="badge bg-danger text-white">${s}</span>`).join(" ")
                        : `<span class="text-muted">—</span>`
                    }
                </td>
            </tr>
        `).join("");
    }

    // --------------------------
    // Click en fila → busca automáticamente
    // --------------------------
    function enableTableSelection() {
        tableBody.addEventListener("dblclick", (e) => {
            const row = e.target.closest("tr");
            if (!row) return;

            const nameCell = row.querySelector("td:nth-child(2)");
            if (nameCell) {
                input.value = nameCell.textContent;
                autocomplete.innerHTML = "";
                searchBtn.click();
            }
        });
    }

    // --------------------------
    // Recomendaciones desde backend
    // --------------------------
    async function fetchRecommendations(nombre) {
        try {
            const response = await fetch(`/recomendar?nombre=${encodeURIComponent(nombre)}`);
            const data = await response.json(); // { plato_base: "...", recomendaciones: [...] }
            renderRecommendations(data.recomendaciones);
        } catch (err) {
            console.error("Error al obtener recomendaciones:", err);
        }
    }

    function renderRecommendations(recommendations) {
        recommendationsDiv.innerHTML = recommendations.map(r => `
            <div class="col-md-4 mb-3">
                <div class="card card-hover h-100 p-3 recommendation-card" data-name="${r.name}">
                    <h5 class="card-title text-success fw-bold">${r.name}</h5>
                    <p class="card-text">${r.company}</p>

                    <div class="d-flex flex-wrap gap-2 mb-2">
                        <span class="badge bg-warning text-dark">Cal: ${r.calories}</span>
                        <span class="badge bg-info text-dark">Prot: ${r.protein}g</span>
                        <span class="badge bg-danger text-white">Grasa: ${r.fat}g</span>
                        <span class="badge bg-secondary text-white">Carbs: ${r.carbs}g</span>
                    </div>

                    <!-- nuevos nutrientes -->
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

        // click en tarjetas → nueva búsqueda
        document.querySelectorAll(".recommendation-card").forEach(card => {
            card.addEventListener("click", () => {
                const name = card.getAttribute("data-name");
                input.value = name;
                autocomplete.innerHTML = "";
                searchBtn.click();
            });
        });
    }


    // Inicializa click en filas existentes al cargar
    enableTableSelection();
});
