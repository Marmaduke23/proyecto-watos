document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("searchInput");
    const tableBody = document.getElementById("tableBody");
    const autocomplete = document.getElementById("autocomplete");
    const recommendationsDiv = document.getElementById("recommendations");
    const searchBtn = document.getElementById("searchBtn");

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
        const query = input.value.trim();
        if (!query) return;

        // Filtrar tabla localmente
        const filtered = allItems.filter(p => p.name.toLowerCase().includes(query.toLowerCase()));
        renderTable(filtered);

        // Re-activar click en filas
        enableTableSelection();

        // Obtener recomendaciones desde backend
        if (filtered.length > 0) {
            await fetchRecommendations(filtered[0].name);
        } else {
            recommendationsDiv.innerHTML = "";
        }

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
                <td>${p.calories}</td>
                <td>${p.protein}</td>
                <td>${p.fat}</td>
                <td>${p.carbs}</td>
            </tr>`).join("");
    }

    // --------------------------
    // Click en fila → busca automáticamente
    // --------------------------
    function enableTableSelection() {
        tableBody.addEventListener("click", (e) => {
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
        if (!recommendationsDiv) return;

        recommendationsDiv.innerHTML = recommendations.map(r => `
            <div class="col-md-4 mb-3">
                <div class="card card-hover h-100 p-3 recommendation-card" data-name="${r.name}">
                    <h5 class="card-title text-success fw-bold">${r.name}</h5>
                    <p class="card-text">${r.company}</p>
                    <div class="d-flex flex-wrap gap-2">
                        <span class="badge bg-warning text-dark">Cal: ${r.calories}</span>
                        <span class="badge bg-info text-dark">Prot: ${r.protein}g</span>
                        <span class="badge bg-danger text-white">Grasa: ${r.fat}g</span>
                        <span class="badge bg-secondary text-white">Carbs: ${r.carbs}g</span>
                    </div>
                </div>
            </div>
        `).join("");

        // --------------------------
        // Click en recomendación → busca automáticamente
        // --------------------------
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
