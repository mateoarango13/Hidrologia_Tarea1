document.addEventListener('DOMContentLoaded', () => {
    // 1. Manejo del Tema (Oscuro/Claro)
    const themeToggle = document.querySelector('.theme-toggle');
    const rootElement = document.documentElement;
    
    // Obtener colores del tema actual para Plotly
    const getThemeColors = () => {
        const isLight = rootElement.getAttribute('data-theme') === 'light';
        return {
            bg: 'transparent',
            text: isLight ? '#475569' : '#94a3b8',
            grid: isLight ? 'rgba(0,0,0,0.06)' : 'rgba(255,255,255,0.06)',
            primary: '#3b82f6',
            secondary: '#10b981',
            accent: '#f59e0b',
            red: '#ef4444',
            purple: '#8b5cf6'
        };
    };

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const currentTheme = rootElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            rootElement.setAttribute('data-theme', newTheme);
            themeToggle.innerHTML = newTheme === 'light' ? '<i class="fa-solid fa-moon"></i>' : '<i class="fa-solid fa-sun"></i>';
            renderAllCharts();
        });
    }

    // 2. Navegación por pestañas (Sidebar)
    const navButtons = document.querySelectorAll('.nav-btn:not(.disabled)');
    const views = document.querySelectorAll('.view');
    const pageTitle = document.getElementById('current-page-title');

    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            navButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            if (pageTitle) {
                const label = btn.querySelector('span');
                if (label) pageTitle.textContent = label.textContent;
            }

            const targetId = btn.getAttribute('data-target');
            views.forEach(v => {
                v.classList.remove('active');
                if (v.id === targetId) {
                    v.classList.add('active');
                }
            });

            // Forzar resize de Plotly para tabs ocultos
            setTimeout(() => {
                window.dispatchEvent(new Event('resize'));
            }, 50);
        });
    });

    // 3. Renderizado de Gráficos (Plotly)
    const renderAllCharts = () => {
        if (!window.dashboardData) {
            console.warn("No se encontró window.dashboardData.");
            return;
        }

        if (typeof Plotly === 'undefined') {
            console.error("Plotly no está cargado. No se pueden renderizar los gráficos interactivos.");
            return;
        }
        
        const colors = getThemeColors();
        const baseLayout = {
            paper_bgcolor: colors.bg,
            plot_bgcolor: colors.bg,
            font: { family: 'Inter, system-ui, sans-serif', color: colors.text, size: 12 },
            margin: { t: 30, r: 25, l: 55, b: 50 },
            xaxis: { gridcolor: colors.grid, zerolinecolor: colors.grid },
            yaxis: { gridcolor: colors.grid, zerolinecolor: colors.grid },
            autosize: true
        };

        const data = window.dashboardData;

        // === HOME: Disponibilidad (Heatmap) ===
        if (data.disponibilidad && document.getElementById('chart-disponibilidad')) {
            Plotly.newPlot('chart-disponibilidad', [{
                z: data.disponibilidad.z,
                x: data.disponibilidad.x,
                y: data.disponibilidad.y,
                type: 'heatmap',
                colorscale: [[0, '#334155'], [1, '#3b82f6']],
                showscale: false,
                hoverongaps: false
            }], {
                ...baseLayout,
                yaxis: { ...baseLayout.yaxis, autorange: 'reversed' },
                xaxis: { ...baseLayout.xaxis, title: 'Año' }
            }, {responsive: true, displayModeBar: false});
        }

        // === ROL A: Ciclo Anual ===
        if (data.cicloAnual && document.getElementById('chart-ciclo-anual')) {
            Plotly.newPlot('chart-ciclo-anual', [
                {
                    x: data.cicloAnual.meses,
                    y: data.cicloAnual.precip,
                    name: 'Precipitación Local (mm/mes)',
                    type: 'bar',
                    marker: { color: colors.primary, opacity: 0.85 },
                    yaxis: 'y1'
                },
                {
                    x: data.cicloAnual.meses,
                    y: data.cicloAnual.caudal,
                    name: 'Caudal Medio (m³/s)',
                    type: 'scatter',
                    mode: 'lines+markers',
                    line: { color: colors.secondary, width: 3 },
                    marker: { size: 8 },
                    yaxis: 'y2'
                }
            ], {
                ...baseLayout,
                yaxis: { title: 'Precipitación (mm/mes)', gridcolor: colors.grid },
                yaxis2: { title: 'Caudal (m³/s)', overlaying: 'y', side: 'right', showgrid: false },
                legend: { orientation: 'h', y: 1.15, x: 0.1 }
            }, {responsive: true, displayModeBar: false});
        }

        // === ROL A: Histograma Precipitación Local vs IMERG ===
        if (data.histPrecip && document.getElementById('chart-hist-precip')) {
            const traces = [
                {
                    x: data.histPrecip.x,
                    y: data.histPrecip.y_local || data.histPrecip.y,
                    name: 'Referencia Local',
                    type: 'bar',
                    marker: { color: colors.primary, opacity: 0.75 }
                }
            ];
            if (data.histPrecip.y_imerg) {
                traces.push({
                    x: data.histPrecip.x,
                    y: data.histPrecip.y_imerg,
                    name: 'GPM IMERG',
                    type: 'bar',
                    marker: { color: colors.accent, opacity: 0.75 }
                });
            }
            Plotly.newPlot('chart-hist-precip', traces, {
                ...baseLayout,
                barmode: 'group',
                xaxis: { title: 'Precipitación Mensual (mm)' },
                yaxis: { title: 'Frecuencia (Meses)' },
                legend: { orientation: 'h', y: 1.15 }
            }, {responsive: true, displayModeBar: false});
        }

        // === ROL A: Impacto de la Megasequía (Subperiodos) ===
        if (data.subperiodos && document.getElementById('chart-subperiodos')) {
            Plotly.newPlot('chart-subperiodos', [
                {
                    x: data.subperiodos.meses,
                    y: data.subperiodos.r_1980_1999,
                    name: 'Escorrentía R (1980-1999)',
                    type: 'scatter',
                    mode: 'lines+markers',
                    line: { color: colors.primary, width: 2.5, dash: 'dot' },
                    marker: { size: 6 }
                },
                {
                    x: data.subperiodos.meses,
                    y: data.subperiodos.r_2000_2020,
                    name: 'Escorrentía R (2000-2020: Megasequía)',
                    type: 'scatter',
                    mode: 'lines+markers',
                    line: { color: colors.red, width: 3 },
                    marker: { size: 7 }
                }
            ], {
                ...baseLayout,
                xaxis: { title: 'Mes Calendario' },
                yaxis: { title: 'Lámina de Escorrentía (mm/mes)' },
                legend: { orientation: 'h', y: 1.15 }
            }, {responsive: true, displayModeBar: false});
        }

        // === ROL B: Scatter IMERG vs Local ===
        if (data.scatterImerg && document.getElementById('chart-scatter-imerg')) {
            const scatterTraces = data.scatterImerg.traces.map(trace => ({
                x: trace.x,
                y: trace.y,
                mode: 'markers',
                name: trace.name,
                marker: { size: 6, opacity: 0.75 }
            }));
            // Línea 1:1
            const maxVal = Math.max(...data.scatterImerg.maxVal);
            scatterTraces.push({
                x: [0, maxVal],
                y: [0, maxVal],
                mode: 'lines',
                name: 'Identidad 1:1',
                line: { color: '#94a3b8', dash: 'dash', width: 1.5 }
            });
            Plotly.newPlot('chart-scatter-imerg', scatterTraces, {
                ...baseLayout,
                xaxis: { title: 'Precipitación Local (mm/mes)' },
                yaxis: { title: 'Precipitación IMERG (mm/mes)' },
                legend: { orientation: 'h', y: 1.15 }
            }, {responsive: true, displayModeBar: false});
        }

        // === ROL B: Rezagos Lluvia-Caudal (Efecto Memoria Nival) ===
        if (data.rezagos && document.getElementById('chart-rezagos')) {
            const tracesRezagos = [
                {
                    x: data.rezagos.lags,
                    y: data.rezagos.r_local,
                    name: 'Pearson r (Anomalías P_local)',
                    type: 'scatter',
                    mode: 'lines+markers',
                    line: { color: colors.primary, width: 3 },
                    marker: { size: 8 }
                },
                {
                    x: data.rezagos.lags,
                    y: data.rezagos.rho_local,
                    name: 'Spearman rho (P_local)',
                    type: 'scatter',
                    mode: 'lines+markers',
                    line: { color: colors.secondary, width: 2, dash: 'dash' },
                    marker: { size: 6 }
                }
            ];
            if (data.rezagos.r_imerg && data.rezagos.r_imerg.length > 0) {
                tracesRezagos.push({
                    x: data.rezagos.lags,
                    y: data.rezagos.r_imerg,
                    name: 'Pearson r (IMERG)',
                    type: 'scatter',
                    mode: 'lines+markers',
                    line: { color: colors.accent, width: 2 },
                    marker: { size: 6 }
                });
            }
            Plotly.newPlot('chart-rezagos', tracesRezagos, {
                ...baseLayout,
                xaxis: { title: 'Rezago k (Meses)', dtick: 1 },
                yaxis: { title: 'Correlación Cruzada (r)' },
                legend: { orientation: 'h', y: 1.15 }
            }, {responsive: true, displayModeBar: false});
        }

        // === ROL B: Validación Temporal Fuera de Muestra ===
        if (data.validacionTemporal && document.getElementById('chart-validacion-temporal')) {
            Plotly.newPlot('chart-validacion-temporal', [
                {
                    x: data.validacionTemporal.fechas,
                    y: data.validacionTemporal.observado,
                    name: 'Caudal Observado Q (m³/s)',
                    type: 'scatter',
                    mode: 'lines',
                    line: { color: colors.primary, width: 1.5 }
                },
                {
                    x: data.validacionTemporal.fechas,
                    y: data.validacionTemporal.modelado,
                    name: 'Modelo de Anomalías con Rezago',
                    type: 'scatter',
                    mode: 'lines',
                    line: { color: colors.accent, width: 2 }
                }
            ], {
                ...baseLayout,
                xaxis: { title: 'Fecha (Meses de Evaluación Externa 2010-2020)' },
                yaxis: { title: 'Caudal Medio Mensual (m³/s)' },
                legend: { orientation: 'h', y: 1.15 }
            }, {responsive: true, displayModeBar: false});
        }

        // === ROL A: Tabla Síntesis ===
        if (data.tablaSintesisA && document.getElementById('tabla-sintesis-rol-a')) {
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

    // Renderizar al cargar
    setTimeout(renderAllCharts, 120);
    window.addEventListener('resize', renderAllCharts);
});
