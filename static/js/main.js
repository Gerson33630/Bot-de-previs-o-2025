const jogos = [
    "aviator",
    "jetx",
    "rocketman",
    "spaceman",
    "navigator",
    "swimminator",
    "fashnator"
];

function iconePorStatus(status) {
    if(status.includes("ROS")) return "🌹";
    if(status.includes("ROXO")) return "🟣";
    if(status.includes("Proteja")) return "🔵";
    return "🔘";
}

function mostrarPopup(jogo, status, previsao) {
    let msg = `${jogo.toUpperCase()} - Previsão: ${previsao}x\nStatus: ${status}`;
    alert(msg);
}

async function carregarPrevisoes() {
    for(let jogo of jogos) {
        try {
            let res = await fetch(`/previsao/${jogo}`);
            let data = await res.json();
            const el = document.querySelector(`#${jogo} .previsao`);
            if(data.previsao) {
                const icone = iconePorStatus(data.status);
                el.textContent = `${icone} ${data.previsao}x - ${data.status}`;
                mostrarPopup(jogo, data.status, data.previsao);
            } else {
                el.textContent = "Sem dados suficientes para previsão.";
            }
        } catch(e) {
            console.error(`Erro ao carregar previsão de ${jogo}:`, e);
            document.querySelector(`#${jogo} .previsao`).textContent = "Erro ao carregar previsão.";
        }
    }
}

window.onload = () => {
    carregarPrevisoes();
    // Atualiza a cada 60 segundos
    setInterval(carregarPrevisoes, 60000);
};
