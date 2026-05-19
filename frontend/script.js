/* ═══════════════════════════════════════════════
   MONITOREO DE PÁRAMOS — script.js
   Lógica Flask original + efectos NASA bioluminiscente
   ═══════════════════════════════════════════════ */

// ── Chart.js globals ──────────────────────────────
let chartTempHumedad = null;
let chartSuelo = null;
let estacionActual = null;
let intervaloActualizacion = null;

// ── Gauge canvas refs ─────────────────────────────
const GAUGE_COLOR = {
    cyan:   { track: '#0a2a3a', fill: '#00ffe7', glow: 'rgba(0,255,231,.6)' },
    green:  { track: '#0a2a1a', fill: '#39ff14', glow: 'rgba(57,255,20,.6)' },
    purple: { track: '#1a0a2a', fill: '#bf5fff', glow: 'rgba(191,95,255,.6)' },
};

// ══════════════════════════════════════════════════
// PARTICLES
// ══════════════════════════════════════════════════
(function initParticles() {
    const canvas = document.getElementById('particles-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let W, H, particles;

    function resize() {
        W = canvas.width  = window.innerWidth;
        H = canvas.height = window.innerHeight;
    }

    function makeParticle() {
        return {
            x: Math.random() * W,
            y: Math.random() * H,
            r: Math.random() * 1.2 + .3,
            dx: (Math.random() - .5) * .3,
            dy: -(Math.random() * .4 + .1),
            alpha: Math.random() * .5 + .1,
            color: Math.random() < .7 ? '#00ffe7' : Math.random() < .5 ? '#39ff14' : '#bf5fff',
        };
    }

    function spawnParticles() {
        particles = Array.from({ length: 120 }, makeParticle);
    }

    function draw() {
        ctx.clearRect(0, 0, W, H);
        for (const p of particles) {
            ctx.save();
            ctx.globalAlpha = p.alpha;
            ctx.shadowColor = p.color;
            ctx.shadowBlur  = 6;
            ctx.fillStyle   = p.color;
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
            ctx.fill();
            ctx.restore();

            p.x += p.dx;
            p.y += p.dy;
            p.alpha -= .0008;

            if (p.y < 0 || p.alpha <= 0) Object.assign(p, makeParticle(), { y: H + 5, alpha: Math.random() * .5 + .1 });
        }
        requestAnimationFrame(draw);
    }

    resize();
    spawnParticles();
    draw();
    window.addEventListener('resize', () => { resize(); spawnParticles(); });
})();

// ══════════════════════════════════════════════════
// CLOCK
// ══════════════════════════════════════════════════
(function initClock() {
    const clockEl    = document.getElementById('clock');
    const dateLineEl = document.getElementById('dateLine');
    const DAYS  = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
    const MONTHS = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];

    function tick() {
        const now = new Date();
        const hh = String(now.getHours()).padStart(2,'0');
        const mm = String(now.getMinutes()).padStart(2,'0');
        const ss = String(now.getSeconds()).padStart(2,'0');
        clockEl.textContent = `${hh}:${mm}:${ss}`;
        dateLineEl.textContent =
            `${DAYS[now.getDay()]}, ${now.getDate()} ${MONTHS[now.getMonth()]} ${now.getFullYear()}`;
    }
    tick();
    setInterval(tick, 1000);
})();

// ══════════════════════════════════════════════════
// GAUGE DRAWING
// ══════════════════════════════════════════════════
function drawGauge(canvasId, value, max, colorKey) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    const R  = 56;
    const startAngle = Math.PI * 0.75;
    const endAngle   = Math.PI * 2.25;
    const pct = Math.min(Math.max(value / max, 0), 1);
    const fillEnd = startAngle + (endAngle - startAngle) * pct;
    const c = GAUGE_COLOR[colorKey] || GAUGE_COLOR.cyan;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Track
    ctx.beginPath();
    ctx.arc(cx, cy, R, startAngle, endAngle);
    ctx.strokeStyle = c.track;
    ctx.lineWidth = 10;
    ctx.lineCap = 'round';
    ctx.stroke();

    // Fill
    if (pct > 0) {
        ctx.save();
        ctx.shadowColor = c.glow;
        ctx.shadowBlur  = 18;
        ctx.beginPath();
        ctx.arc(cx, cy, R, startAngle, fillEnd);
        ctx.strokeStyle = c.fill;
        ctx.lineWidth = 10;
        ctx.lineCap = 'round';
        ctx.stroke();
        ctx.restore();
    }

    // Tick marks
    for (let i = 0; i <= 10; i++) {
        const angle = startAngle + (endAngle - startAngle) * (i / 10);
        const outer = R + 14;
        const inner = R + 8;
        ctx.beginPath();
        ctx.moveTo(cx + Math.cos(angle) * inner, cy + Math.sin(angle) * inner);
        ctx.lineTo(cx + Math.cos(angle) * outer, cy + Math.sin(angle) * outer);
        ctx.strokeStyle = i <= pct * 10 ? c.fill : c.track;
        ctx.lineWidth = 1.5;
        ctx.stroke();
    }
}

function updateGauges(temp, suelo) {
    // Temp gauge: 0-30°C
    if (temp !== null && !isNaN(temp)) {
        drawGauge('gaugeTemp', temp, 30, 'cyan');
        document.getElementById('gv-temp').textContent = parseFloat(temp).toFixed(1);
        const gb = document.getElementById('gb-temp');
        if (temp < 5) { gb.textContent = 'FRÍO'; gb.className = 'gauge-badge badge-quality'; }
        else if (temp > 20) { gb.textContent = 'CALIENTE'; gb.className = 'gauge-badge badge-quality'; }
        else { gb.textContent = 'NORMAL'; gb.className = 'gauge-badge badge-normal'; }
    }
    // Suelo gauge: 0-100%
    if (suelo !== null && !isNaN(suelo)) {
        drawGauge('gaugeSuelo', suelo, 100, 'green');
        document.getElementById('gv-suelo').textContent = suelo;
        const gs = document.getElementById('gb-suelo');
        if (suelo < 30) { gs.textContent = 'SECO'; gs.className = 'gauge-badge badge-quality'; }
        else if (suelo > 85) { gs.textContent = 'SATURADO'; gs.className = 'gauge-badge badge-quality'; }
        else { gs.textContent = 'ÓPTIMO'; gs.className = 'gauge-badge badge-optimo'; }
    }
    // Calidad siempre 98.3
    drawGauge('gaugeCalidad', 98.3, 100, 'purple');
}

// Draw initial gauges at 0
drawGauge('gaugeTemp',    0,    30,  'cyan');
drawGauge('gaugeSuelo',   0,   100, 'green');
drawGauge('gaugeCalidad', 98.3, 100, 'purple');

// ══════════════════════════════════════════════════
// CHART.JS — dark bioluminiscente theme
// ══════════════════════════════════════════════════
Chart.defaults.color = '#2a5a6a';
Chart.defaults.font.family = "'Share Tech Mono', monospace";
Chart.defaults.font.size = 10;

function chartDefaults(color) {
    return {
        borderColor: color,
        backgroundColor: color.replace(')', ',.08)').replace('rgb', 'rgba').replace('#', 'rgba(').replace(/([a-f0-9]{2})/gi, (m) => parseInt(m,16)+',').slice(0,-1),
        tension: 0.4,
        fill: true,
        pointRadius: 2,
        pointHoverRadius: 5,
        pointBorderColor: color,
        pointBackgroundColor: color,
    };
}

function initCharts() {
    const gridColor = 'rgba(0,255,231,.05)';
    const scaleOpts = {
        grid: { color: gridColor, drawBorder: false },
        ticks: { color: '#2a5a6a' },
    };

    const ctx1 = document.getElementById('graficaTempHumedad').getContext('2d');
    chartTempHumedad = new Chart(ctx1, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Temperatura (°C)',
                    data: [],
                    borderColor: '#00ffe7',
                    backgroundColor: 'rgba(0,255,231,.07)',
                    tension: 0.4, fill: true,
                    pointRadius: 2, pointBackgroundColor: '#00ffe7',
                },
                {
                    label: 'Humedad Aire (%)',
                    data: [],
                    borderColor: '#39ff14',
                    backgroundColor: 'rgba(57,255,20,.06)',
                    tension: 0.4, fill: true,
                    pointRadius: 2, pointBackgroundColor: '#39ff14',
                }
            ]
        },
        options: {
            responsive: true,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: {
                    position: 'top',
                    labels: { color: '#6ab8c8', boxWidth: 12, font: { family: "'Share Tech Mono'", size: 10 } }
                }
            },
            scales: {
                x: scaleOpts,
                y: scaleOpts,
            }
        }
    });

    const ctx2 = document.getElementById('graficaSuelo').getContext('2d');
    chartSuelo = new Chart(ctx2, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Humedad Suelo (%)',
                data: [],
                borderColor: '#f5c518',
                backgroundColor: 'rgba(245,197,24,.07)',
                tension: 0.4, fill: true,
                pointRadius: 2, pointBackgroundColor: '#f5c518',
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                    labels: { color: '#6ab8c8', boxWidth: 12, font: { family: "'Share Tech Mono'", size: 10 } }
                }
            },
            scales: {
                x: scaleOpts,
                y: { ...scaleOpts, min: 0, max: 100 }
            }
        }
    });
}

// ══════════════════════════════════════════════════
// API CALLS (lógica original intacta)
// ══════════════════════════════════════════════════
async function cargarEstaciones() {
    try {
        const response = await fetch('/api/estaciones');
        const estaciones = await response.json();

        const selector = document.getElementById('selector-estacion');
        selector.innerHTML = '<option value="">Seleccione una estación...</option>';

        estaciones.forEach(estacion => {
            const option = document.createElement('option');
            option.value = estacion.codigo;
            option.textContent = `${estacion.nombre} (${estacion.codigo})`;
            selector.appendChild(option);
        });

        if (estaciones.length > 0) {
            selector.value = estaciones[0].codigo;
            cambiarEstacion();
        }

        selector.addEventListener('change', cambiarEstacion);
    } catch (error) {
        console.error('Error cargando estaciones:', error);
    }
}

function cambiarEstacion() {
    const selector = document.getElementById('selector-estacion');
    estacionActual = selector.value;

    if (intervaloActualizacion) clearInterval(intervaloActualizacion);

    if (estacionActual) {
        actualizarTodo();
        intervaloActualizacion = setInterval(actualizarTodo, 5000);
    }
}

async function actualizarTodo() {
    if (!estacionActual) return;
    await Promise.all([
        actualizarUltimaLectura(),
        actualizarHistorico(),
        actualizarAlertas(),
        actualizarEstadisticas()
    ]);
}

async function actualizarUltimaLectura() {
    try {
        const response = await fetch(`/api/ultima-lectura?estacion=${estacionActual}`);
        const data = await response.json();

        if (!data.error) {
            const temp  = data.temperatura  ? parseFloat(data.temperatura).toFixed(1) : '--';
            const aire  = data.humedad_aire ? parseFloat(data.humedad_aire).toFixed(1) : '--';
            const suelo = data.humedad_suelo !== null ? data.humedad_suelo : '--';

            document.getElementById('temperatura').textContent   = temp;
            document.getElementById('humedad-aire').textContent  = aire;
            document.getElementById('humedad-suelo').textContent = suelo;

            // Update gauges
            updateGauges(parseFloat(temp), parseFloat(suelo));

            // Station label
            if (data.estacion_codigo) {
                document.getElementById('station-id-label').textContent =
                    data.estacion_codigo.toUpperCase();
            }

            if (data.fecha) {
                const fecha = new Date(data.fecha);
                document.getElementById('ultima-actualizacion').textContent =
                    `Actualizado: ${fecha.toLocaleTimeString()}`;
            }

            // Alerta suelo
            const alertaSuelo = document.getElementById('alerta-suelo');
            if (data.humedad_suelo < 30) {
                alertaSuelo.textContent = 'SUELO SECO';
                alertaSuelo.className = 'alerta-suelo critico';
            } else if (data.humedad_suelo > 85) {
                alertaSuelo.textContent = 'SUELO SATURADO';
                alertaSuelo.className = 'alerta-suelo advertencia';
            } else {
                alertaSuelo.textContent = '';
                alertaSuelo.className = 'alerta-suelo';
            }

            // Info estación
            document.getElementById('info-estacion').innerHTML = `
                <div class="info-card">
                    <h3>Estación: ${data.estacion_nombre}</h3>
                    <p>Código: ${data.estacion_codigo}</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error lectura:', error);
    }
}

async function actualizarHistorico() {
    try {
        const response = await fetch(`/api/historico/${estacionActual}?limite=50`);
        const data = await response.json();

        if (data.length > 0) {
            const labels         = data.map(d => new Date(d.fecha).toLocaleTimeString());
            const temperaturas   = data.map(d => d.temperatura);
            const humedadesAire  = data.map(d => d.humedad_aire);
            const humedadesSuelo = data.map(d => d.humedad_suelo);

            chartTempHumedad.data.labels = labels;
            chartTempHumedad.data.datasets[0].data = temperaturas;
            chartTempHumedad.data.datasets[1].data = humedadesAire;
            chartTempHumedad.update();

            chartSuelo.data.labels = labels;
            chartSuelo.data.datasets[0].data = humedadesSuelo;
            chartSuelo.update();
        }
    } catch (error) {
        console.error('Error histórico:', error);
    }
}

async function actualizarAlertas() {
    try {
        const response = await fetch(`/api/alertas?estacion=${estacionActual}`);
        const data = await response.json();

        const container = document.getElementById('lista-alertas');
        if (data.length === 0) {
            container.innerHTML = '<div class="sin-alertas">✓ Sin alertas activas</div>';
            return;
        }

        container.innerHTML = data.map(alerta => `
            <div class="alerta-item ${alerta.nivel.toLowerCase()}">
                <div class="alerta-fecha">${new Date(alerta.fecha).toLocaleString()}</div>
                <div class="alerta-tipo">${alerta.tipo}</div>
                <div class="alerta-descripcion">${alerta.descripcion}</div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error alertas:', error);
    }
}

async function actualizarEstadisticas() {
    try {
        const response = await fetch(`/api/estadisticas/${estacionActual}`);
        const data = await response.json();

        if (!data.error) {
            document.getElementById('total-lecturas').textContent = data.total_lecturas;

            const container = document.getElementById('estadisticas');
            container.innerHTML = `
                <div class="stat-card">
                    <div class="stat-label">Temp. Promedio</div>
                    <div class="stat-value">${data.temperatura_promedio.toFixed(1)}°C</div>
                    <div class="stat-bar-wrap"><div class="stat-bar" style="width:${Math.min((data.temperatura_promedio/30)*100,100)}%;background:var(--cyan);box-shadow:0 0 6px var(--cyan)"></div></div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Temp. Min / Max</div>
                    <div class="stat-value" style="color:var(--green);text-shadow:0 0 10px var(--green)">
                        ${data.temperatura_minima.toFixed(1)} / ${data.temperatura_maxima.toFixed(1)}°C
                    </div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Humedad Ambiente</div>
                    <div class="stat-value" style="color:var(--yellow);text-shadow:0 0 10px var(--yellow)">${data.humedad_promedio.toFixed(1)}%</div>
                    <div class="stat-bar-wrap"><div class="stat-bar" style="width:${data.humedad_promedio}%;background:var(--yellow);box-shadow:0 0 6px var(--yellow)"></div></div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Humedad Suelo</div>
                    <div class="stat-value" style="color:var(--purple);text-shadow:0 0 10px var(--purple)">${data.suelo_promedio}% <small style="font-size:.6rem;color:var(--text-dim)">mín ${data.suelo_minimo}%</small></div>
                    <div class="stat-bar-wrap"><div class="stat-bar" style="width:${data.suelo_promedio}%;background:var(--purple);box-shadow:0 0 6px var(--purple)"></div></div>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error estadísticas:', error);
    }
}

// ══════════════════════════════════════════════════
// INIT
// ══════════════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    cargarEstaciones();
});