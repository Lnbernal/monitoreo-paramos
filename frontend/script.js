let chartTempHumedad = null;
let chartSuelo = null;
let estacionActual = null;
let intervaloActualizacion = null;

function initCharts() {
    const ctx1 = document.getElementById('graficaTempHumedad').getContext('2d');
    chartTempHumedad = new Chart(ctx1, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Temperatura (C)',
                    data: [],
                    borderColor: '#ff6b6b',
                    backgroundColor: 'rgba(255, 107, 107, 0.1)',
                    tension: 0.4,
                    fill: true
                },
                {
                    label: 'Humedad Aire (%)',
                    data: [],
                    borderColor: '#4dabf7',
                    backgroundColor: 'rgba(77, 171, 247, 0.1)',
                    tension: 0.4,
                    fill: true
                }
            ]
        },
        options: {
            responsive: true,
            interaction: { mode: 'index', intersect: false },
            plugins: { legend: { position: 'top' } }
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
                borderColor: '#51cf66',
                backgroundColor: 'rgba(81, 207, 102, 0.1)',
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { position: 'top' } },
            scales: { y: { min: 0, max: 100, title: { display: true, text: 'Humedad (%)' } } }
        }
    });
}

async function cargarEstaciones() {
    try {
        const response = await fetch('/api/estaciones');
        const estaciones = await response.json();
        
        const selector = document.getElementById('selector-estacion');
        selector.innerHTML = '<option value="">Seleccione una estacion...</option>';
        
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
    
    if (intervaloActualizacion) {
        clearInterval(intervaloActualizacion);
    }
    
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
            document.getElementById('temperatura').textContent = 
                data.temperatura ? data.temperatura.toFixed(1) : '--';
            document.getElementById('humedad-aire').textContent = 
                data.humedad_aire ? data.humedad_aire.toFixed(1) : '--';
            document.getElementById('humedad-suelo').textContent = 
                data.humedad_suelo !== null ? data.humedad_suelo : '--';
            
            if (data.fecha) {
                const fecha = new Date(data.fecha);
                document.getElementById('ultima-actualizacion').textContent = 
                    `Actualizado: ${fecha.toLocaleTimeString()}`;
            }
            
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
            
            document.getElementById('info-estacion').innerHTML = `
                <div class="info-card">
                    <h3>Estacion: ${data.estacion_nombre}</h3>
                    <p>Codigo: ${data.estacion_codigo}</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

async function actualizarHistorico() {
    try {
        const response = await fetch(`/api/historico/${estacionActual}?limite=50`);
        const data = await response.json();
        
        if (data.length > 0) {
            const labels = data.map(d => new Date(d.fecha).toLocaleTimeString());
            const temperaturas = data.map(d => d.temperatura);
            const humedadesAire = data.map(d => d.humedad_aire);
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
        console.error('Error:', error);
    }
}

async function actualizarAlertas() {
    try {
        const response = await fetch(`/api/alertas?estacion=${estacionActual}`);
        const data = await response.json();
        
        const container = document.getElementById('lista-alertas');
        if (data.length === 0) {
            container.innerHTML = '<div class="sin-alertas">No hay alertas activas</div>';
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
        console.error('Error:', error);
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
                    <div class="stat-label">Temperatura Promedio</div>
                    <div class="stat-value">${data.temperatura_promedio.toFixed(1)}C</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Temperatura Min / Max</div>
                    <div class="stat-value">${data.temperatura_minima.toFixed(1)} / ${data.temperatura_maxima.toFixed(1)}C</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Humedad Ambiente</div>
                    <div class="stat-value">${data.humedad_promedio.toFixed(1)}%</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Humedad Suelo</div>
                    <div class="stat-value">${data.suelo_promedio}% (min: ${data.suelo_minimo}%)</div>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error:', error);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    cargarEstaciones();
});