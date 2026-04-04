const searchInput = document.getElementById("searchInput");
const searchButton = document.getElementById("searchButton");
const searchResults = document.getElementById("searchResults");
const likedGamesContainer = document.getElementById("likedGames");
const recommendButton = document.getElementById("recommendButton");
const recommendationsContainer = document.getElementById("recommendations");
const similarGamesContainer = document.getElementById("similarGames");

let likedGames = [];

function truncateText(text, maxLength = 160) {
    if (!text) return "";
    return text.length > maxLength ? text.slice(0, maxLength) + "..." : text;
}

function renderLikedGames() {
    likedGamesContainer.innerHTML = "";

    if (likedGames.length === 0) {
        likedGamesContainer.innerHTML = "<p>Пока ничего не выбрано.</p>";
        return;
    }

    likedGames.forEach((title) => {
        const item = document.createElement("div");
        item.className = "selected-item";

        const span = document.createElement("span");
        span.textContent = title;

        const removeButton = document.createElement("button");
        removeButton.textContent = "Удалить";
        removeButton.onclick = () => {
            likedGames = likedGames.filter((gameTitle) => gameTitle !== title);
            renderLikedGames();
        };

        item.appendChild(span);
        item.appendChild(removeButton);
        likedGamesContainer.appendChild(item);
    });
}

function createGameCard(game, showAddButton = true) {
    const card = document.createElement("div");
    card.className = "game-card";

    const content = document.createElement("div");
    content.className = "game-card-content";

    const title = document.createElement("h3");
    title.textContent = game.name;

    const meta = document.createElement("div");
    meta.className = "game-meta";
    meta.textContent = `Жанры: ${game.genres || "Не указаны"}`;

    const rating = document.createElement("div");
    rating.className = "game-meta";
    rating.textContent = `Рейтинг: ${game.rating ?? "N/A"} | Отзывы: ${game.num_reviews ?? "N/A"}`;

    const description = document.createElement("div");
    description.className = "game-description";
    description.textContent = truncateText(game.short_description || "Описание отсутствует");

    const actions = document.createElement("div");
    actions.className = "card-actions";

    if (showAddButton) {
        const addButton = document.createElement("button");
        addButton.textContent = "В любимые";
        addButton.onclick = () => {
            if (!likedGames.includes(game.name)) {
                likedGames.push(game.name);
                renderLikedGames();
            }
        };
        actions.appendChild(addButton);
    }

    const similarButton = document.createElement("button");
    similarButton.textContent = "Похожие";
    similarButton.onclick = () => loadSimilarGames(game.name);
    actions.appendChild(similarButton);

    content.appendChild(title);
    content.appendChild(meta);
    content.appendChild(rating);
    content.appendChild(description);
    content.appendChild(actions);

    card.appendChild(content);

    return card;
}

async function searchGames() {
    const query = searchInput.value.trim();

    if (!query) {
        alert("Введите название игры");
        return;
    }

    try {
        const response = await fetch(`/games/search/?query=${encodeURIComponent(query)}`);
        const games = await response.json();

        searchResults.innerHTML = "";

        if (!games.length) {
            searchResults.innerHTML = "<p>Ничего не найдено.</p>";
            return;
        }

        games.forEach((game) => {
            const card = createGameCard(game, true);
            searchResults.appendChild(card);
        });
    } catch (error) {
        console.error(error);
        searchResults.innerHTML = "<p>Ошибка при поиске игр.</p>";
    }
}

async function loadRecommendations() {
    if (likedGames.length === 0) {
        alert("Сначала добавьте хотя бы одну любимую игру");
        return;
    }

    try {
        const response = await fetch("/recommendations", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                liked_titles: likedGames,
                top_k: 8
            })
        });

        const games = await response.json();

        recommendationsContainer.innerHTML = "";

        if (!games.length) {
            recommendationsContainer.innerHTML = "<p>Рекомендации не найдены.</p>";
            return;
        }

        games.forEach((game) => {
            const card = createGameCard(game, false);
            recommendationsContainer.appendChild(card);
        });
    } catch (error) {
        console.error(error);
        recommendationsContainer.innerHTML = "<p>Ошибка при получении рекомендаций.</p>";
    }
}

async function loadSimilarGames(title) {
    try {
        const response = await fetch("/games/similar", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                title: title,
                top_k: 6
            })
        });

        const games = await response.json();

        similarGamesContainer.innerHTML = "";

        if (!games.length) {
            similarGamesContainer.innerHTML = "<p>Похожие игры не найдены.</p>";
            return;
        }

        games.forEach((game) => {
            const card = createGameCard(game, true);
            similarGamesContainer.appendChild(card);
        });
    } catch (error) {
        console.error(error);
        similarGamesContainer.innerHTML = "<p>Ошибка при получении похожих игр.</p>";
    }
}

searchButton.addEventListener("click", searchGames);
recommendButton.addEventListener("click", loadRecommendations);

searchInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
        searchGames();
    }
});

renderLikedGames();