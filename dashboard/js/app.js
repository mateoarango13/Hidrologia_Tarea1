document.addEventListener('DOMContentLoaded', () => {
    // 1. Manejo del Tema (Oscuro/Claro)
    const themeToggle = document.querySelector('.theme-toggle');
    const rootElement = document.documentElement;
    const body = document.body;
    
    // Obtener colores del tema actual para Plotly
    const getThemeColors = () => {
        const isLight = rootElement.getAttribute('data-theme') === 'light';
        return {
            bg: 'transparent',
            text: isLight ? '#475569' : '#94a3b8',
            grid: isLight ? 'rgba(0,0,0,0.05)' : 'rgba(255,255,255,0.05)',
            primary: '#3b82f6',
            secondary: '#10b981',
            accent: '#f59e0b'
        };
    };

    themeToggle.addEventListener('click', () => {
        const currentTheme = rootElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';
        rootElement.setAttribute('data-theme', newTheme);
        themeToggle.innerHTML = newTheme === 'light' ? '<i class="fa-solid fa-moon"></i>' : '<i class="fa-solid fa-sun"></i>';
        
        // Redibujar gráficos con el nuevo tema
        renderAllCharts();
    });

    // 2. Navegación por pestañas (Sidebar)
    const navButtons = document.querySelectorAll('.nav-btn:not(.disabled)');
    const views = document.querySelectorAll('.view');
    const pageTitle = document.getElementById('current-page-title');

    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            // Actualizar botones
            navButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Actualizar título
            pageTitle.textContent = btn.querySelector('span').textContent;

            // Mostrar vista
            const targetId = btn.getAttribute('data-target');
            views.forEach(v => {
                v.classList.remove('active');
                if (v.id === targetId) {
                    v.classList.add('active');
                }
            });

            // Forzar resize de plotly (soluciona bugs de renderizado en tabs ocultos)
            window.dispatchEvent(new Event('resize'));
        });
    });

    // 3. Renderizado de Gráficos (Plotly)
    const renderAllCharts = () => {
        if (!window.dashboardData) {
            console.warn("No se encontró dashboardData. Ejecuta el script de Python para generarlo.");
            return;
        }
        
        const colors = getThemeColors();
        const baseLayout = {
            paper_bgcolor: colors.bg,
            plot_bgcolor: colors.bg,
            font: { family: 'Inter, sans-serif', color: colors.text },
            margin: { t: 20, r: 20, l: 50, b: 50 },
            xaxis: { gridcolor: colors.grid, zerolinecolor: colors.grid },
            yaxis: { gridcolor: colors.grid, zerolinecolor: colors.grid },
            autosize: true
        };

        const data = window.dashboardData;

        // === HOME: Disponibilidad (Heatmap) ===
        if (data.disponibilidad) {
            Plotly.newPlot('chart-disponibilidad', [{
                z: data.disponibilidad.z, // matriz de meses
                x: data.disponibilidad.x, // años
                y: data.disponibilidad.y, // meses (Ene-Dic)
                type: 'heatmap',
                colorscale: [[0, colors.grid], [1, colors.primary]],
                showscale: false
            }], {
                ...baseLayout,
                yaxis: { ...baseLayout.yaxis, autorange: 'reversed' }
            }, {responsive: true});
        }

        // === ROL A: Ciclo Anual ===
        if (data.cicloAnual) {
            Plotly.newPlot('chart-ciclo-anual', [
                {
                    x: data.cicloAnual.meses,
                    y: data.cicloAnual.precip,
                    name: 'Precipitación (mm)',
                    type: 'bar',
                    marker: { color: colors.primary, opacity: 0.8 },
                    yaxis: 'y1'
                },
                {
                    x: data.cicloAnual.meses,
                    y: data.cicloAnual.caudal,
                    name: 'Caudal (m³/s)',
                    type: 'scatter',
                    mode: 'lines+markers',
                    line: { color: colors.secondary, width: 3 },
                    marker: { size: 8 },
                    yaxis: 'y2'
                }
            ], {
                ...baseLayout,
                yaxis: { title: 'Precipitación (mm)', gridcolor: colors.grid },
                yaxis2: { title: 'Caudal (m³/s)', overlaying: 'y', side: 'right', showgrid: false },
                legend: { orientation: 'h', y: 1.1 }
            }, {responsive: true});
        }

        // === ROL A: Histograma Precipitación ===
        if (data.histPrecip) {
            Plotly.newPlot('chart-hist-precip', [{
                x: data.histPrecip.x, // bins
                y: data.histPrecip.y, // conteo
                type: 'bar',
                marker: { color: colors.primary }
            }], {
                ...baseLayout,
                xaxis: { title: 'Precipitación Mensual (mm)' },
                yaxis: { title: 'Frecuencia (Meses)' }
            }, {responsive: true});
        }

        // === ROL B: Scatter IMERG vs CR2MET ===
        if (data.scatterImerg) {
            // Ejemplo de scatter coloreado por estación
            Plotly.newPlot('chart-scatter-imerg', data.scatterImerg.traces.map(trace => ({
                x: trace.x, // CR2MET
                y: trace.y, // IMERG
                mode: 'markers',
                name: trace.name,
                marker: { size: 6, opacity: 0.7 }
            })).concat([{ // Linea 1:1
                x: [0, Math.max(...data.scatterImerg.maxVal)],
                y: [0, Math.max(...data.scatterImerg.maxVal)],
                mode: 'lines',
                name: '1:1',
                line: { color: colors.text, dash: 'dash' }
            }]), {
                ...baseLayout,
                xaxis: { title: 'CR2MET (Observado) mm' },
                yaxis: { title: 'IMERG (Satélite) mm' }
            }, {responsive: true});
        }

        // === ROL B: Validación Temporal ===
        if (data.validacionTemporal) {
            Plotly.newPlot('chart-validacion-temporal', [
                {
                    x: data.validacionTemporal.fechas,
                    y: data.validacionTemporal.observado,
                    name: 'Observado',
                    type: 'scatter',
                    line: { color: colors.primary, width: 1 }
                },
                {
                    x: data.validacionTemporal.fechas,
                    y: data.validacionTemporal.modelado,
                    name: 'Modelado (Anomalías)',
                    type: 'scatter',
                    line: { color: colors.accent, width: 1.5 }
                }
            ], {
                ...baseLayout,
                xaxis: { title: 'Fecha' },
                yaxis: { title: 'Caudal (m³/s)' },
                legend: { orientation: 'h', y: 1.1 }
            }, {responsive: true});
        }

        // Renderizar Tablas
        if (data.tablaSintesisA) {
            const container = document.getElementById('tabla-sintesis-rol-a');
            let html = '<table class="custom-table"><thead><tr>';
            data.tablaSintesisA.headers.forEach(h => html += `<th>${h}</th>`);
            html += '</tr></thead><tbody>';
            data.tablaSintesisA.rows.forEach(row => {
                html += '<tr>';
                row.forEach(cell => html += `<td>${cell}</td>`);
                html += '</tr>';
            });
            html += '</tbody></table>';
            container.innerHTML = html;
        }
    };

    // Inicializar
    setTimeout(renderAllCharts, 100);
    window.addEventListener('resize', renderAllCharts);
});
