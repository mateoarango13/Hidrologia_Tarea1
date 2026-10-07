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
    let selectedQPredictor = 'local';
    let selectedQMetric = 'mae';

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

    const number = (value, digits = 2) => Number(value).toFixed(digits);
    const blockLabels = ['bloque_1', 'bloque_2', 'bloque_3'];
    const blockNames = { bloque_1: 'B1', bloque_2: 'B2', bloque_3: 'B3' };
    const seasonColors = {
        Verano: '#e2a64c',
        Otoño: '#d97853',
        Invierno: '#56a9ba',
        Primavera: '#79a878'
    };

    const findBlockMetric = (task, predictorMatch, modelMatch, block) => {
        const rows = window.dashboardData?.metricasPorBloque || [];
        return rows.find(row => row.task === task &&
            String(row.predictor).toLowerCase().includes(predictorMatch.toLowerCase()) &&
            row.model === modelMatch && row.outer_fold === block);
    };

    const renderPrecipMetricsTable = () => {
        const container = document.getElementById('tabla-metricas-precip');
        const selectedModels = window.dashboardData?.modelosLluviaSeleccionados || [];
        const rows = blockLabels.map(block => {
            const raw = findBlockMetric('estimar_precipitacion_local', 'P_IMERG_mm', 'IMERG sin corrección', block);
            const corrected = findBlockMetric('estimar_precipitacion_local', 'P_IMERG_mm', 'Corrección seleccionada en ajuste', block);
            const selected = selectedModels.find(row => row.outer_fold === block);
            if (!raw || !corrected) return '';
            const parameters = selected ? `β₀ ${number(selected.intercept, 3)} · β₁ ${number(selected.slope, 3)}${selected.smearing_factor == null ? '' : ` · B ${number(selected.smearing_factor, 3)}`}` : '—';
            return `<tr><th>${blockNames[block]}</th><td>${raw.n}</td><td>${corrected.model_variant}</td><td>${parameters}</td><td>${number(raw.mae)}</td><td>${number(raw.rmse)}</td><td>${number(corrected.mae)}</td><td>${number(corrected.rmse)}</td></tr>`;
        }).join('');
        if (container) {
            container.innerHTML = `<table class="rb-data-table"><thead><tr><th>Bloque</th><th>n</th><th>Variante</th><th>Parámetros del ajuste</th><th>Crudo MAE</th><th>RMSE</th><th>Ajuste MAE</th><th>RMSE</th></tr></thead><tbody>${rows}</tbody></table>`;
        }
    };

    const renderQMetricsTable = () => {
        const container = document.getElementById('tabla-metricas-q');
        const predictor = selectedQPredictor === 'local' ? 'P_local_mm' : 'P_IMERG_mm';
        const lags = window.dashboardData?.rezagosSeleccionados || [];
        const rows = blockLabels.map(block => {
            const baseline = findBlockMetric('estimar_caudal', predictor, 'Climatología mensual Q', block);
            const linear = findBlockMetric('estimar_caudal', predictor, 'Regresión lineal Q~P(t)', block);
            const lagged = findBlockMetric('estimar_caudal', predictor, 'Regresión de anomalías con rezago', block);
            const lagRow = lags.find(row => String(row.predictor).includes(predictor) && row.outer_fold === block);
            if (!baseline || !linear || !lagged) return '';
            const coefficients = lagRow ? `${number(lagRow.anomaly_model_intercept, 3)} / ${number(lagRow.anomaly_model_slope, 4)}` : '—';
            return `<tr><th>${blockNames[block]}</th><td>${lagged.n}</td><td>${lagRow ? number(lagRow.candidate_lag_months, 0) : '—'} meses</td><td>${coefficients}</td><td>${number(baseline.mae)} / ${number(baseline.rmse)}</td><td>${number(linear.mae)} / ${number(linear.rmse)}</td><td>${number(lagged.mae)} / ${number(lagged.rmse)}</td></tr>`;
        }).join('');
        if (container) {
            container.innerHTML = `<table class="rb-data-table rb-q-table"><thead><tr><th>Bloque</th><th>n</th><th>k*</th><th>β₀ / β₁</th><th>Climatología<br>MAE / RMSE</th><th>Q~P(t)<br>MAE / RMSE</th><th>Anomalía rezagada<br>MAE / RMSE</th></tr></thead><tbody>${rows}</tbody></table>`;
        }
    };

    const renderQModelChart = () => {
        const rows = window.dashboardData?.metricasPorBloque || [];
        const predictor = selectedQPredictor === 'local' ? 'P_local_mm' : 'P_IMERG_mm';
        const models = [
            { name: 'Climatología mensual', match: 'Climatología mensual Q', color: '#83939a' },
            { name: 'Regresión contemporánea', match: 'Regresión lineal Q~P(t)', color: '#4f9d98' },
            { name: 'Anomalías con rezago', match: 'Regresión de anomalías con rezago', color: '#d97853' }
        ];
        const metricKey = selectedQMetric === 'bias' ? 'bias_pred_minus_obs' : selectedQMetric;
        const traces = models.map(model => ({
            x: blockLabels.map(block => blockNames[block]),
            y: blockLabels.map(block => {
                const row = findBlockMetric('estimar_caudal', predictor, model.match, block);
                return row ? Number(row[metricKey]) : null;
            }),
            name: model.name,
            type: 'bar',
            marker: { color: model.color },
            customdata: blockLabels.map(block => {
                const row = findBlockMetric('estimar_caudal', predictor, model.match, block);
                return row ? [row.n, row.test_start, row.test_end] : [];
            }),
            hovertemplate: '<b>%{x}</b><br>%{fullData.name}<br>Valor: %{y:.2f} m³/s<br>n=%{customdata[0]}<br>%{customdata[1]} a %{customdata[2]}<extra></extra>'
        }));
        const metricTitle = selectedQMetric === 'bias' ? 'Sesgo (predicción − observado), m³/s' : `${selectedQMetric.toUpperCase()} (m³/s)`;
        Plotly.newPlot('chart-model-q', traces, {
            ...baseChartLayout(),
            barmode: 'group',
            margin: { t: 12, r: 16, l: 58, b: 42 },
            xaxis: { ...baseChartLayout().xaxis, title: 'Bloque externo' },
            yaxis: { ...baseChartLayout().yaxis, title: metricTitle, zeroline: selectedQMetric === 'bias' },
            legend: { orientation: 'h', y: 1.14, x: 0, font: { size: 10 } }
        }, { responsive: true, displayModeBar: false });
    };

    const baseChartLayout = () => {
        const colors = getThemeColors();
        return {
            paper_bgcolor: 'transparent',
            plot_bgcolor: 'transparent',
            font: { family: 'Inter, system-ui, sans-serif', color: colors.text, size: 11 },
            margin: { t: 18, r: 16, l: 52, b: 44 },
            xaxis: { gridcolor: colors.grid, zerolinecolor: colors.grid, automargin: true },
            yaxis: { gridcolor: colors.grid, zerolinecolor: colors.grid, automargin: true },
            autosize: true
        };
    };

<<<<<<< HEAD
    const presentationSlides = [...document.querySelectorAll('#rb-exposition .rb-slide')];
    const presentationSteps = [...document.querySelectorAll('#rb-exposition .rb-slide-step')];
    let currentPresentationSlide = 0;
=======
    const raPresentationSlides = [...document.querySelectorAll('#ra-exposition .ra-slide')];
    const raPresentationSteps = [...document.querySelectorAll('.ra-slide-step')];
    let currentRaSlide = 0;
>>>>>>> 923b5326f3dec8d8b29766b6c8cc46e8dd637b22

    const setRaPresentationSlide = index => {
        currentRaSlide = Math.max(0, Math.min(raPresentationSlides.length - 1, index));
        raPresentationSlides.forEach((slide, slideIndex) => {
            const active = slideIndex === currentRaSlide;
            slide.hidden = !active;
            slide.classList.toggle('active', active);
        });
        raPresentationSteps.forEach((step, stepIndex) => {
            const active = stepIndex === currentRaSlide;
            step.classList.toggle('active', active);
            if (active) step.setAttribute('aria-current', 'step');
            else step.removeAttribute('aria-current');
        });
<<<<<<< HEAD
        document.getElementById('rb-slide-count').textContent = `${currentPresentationSlide + 1} / ${presentationSlides.length}`;
        document.querySelector('#rb-exposition .rb-present-prev').disabled = currentPresentationSlide === 0;
        document.querySelector('#rb-exposition .rb-present-next').innerHTML = currentPresentationSlide === presentationSlides.length - 1
=======
        document.getElementById('ra-slide-count').textContent = `${currentRaSlide + 1} / ${raPresentationSlides.length}`;
        document.querySelector('.ra-present-prev').disabled = currentRaSlide === 0;
        document.querySelector('.ra-present-next').innerHTML = currentRaSlide === raPresentationSlides.length - 1
            ? 'Volver al inicio <i class="fa-solid fa-rotate-left"></i>'
            : 'Siguiente <i class="fa-solid fa-arrow-right"></i>';
        window.dispatchEvent(new Event('resize'));
    };

    const setRoleAMode = mode => {
        const exposition = mode === 'exposition';
        if (exposition) setRaPresentationSlide(0);
        document.getElementById('ra-exposition').hidden = !exposition;
        document.getElementById('ra-analysis').hidden = exposition;
        document.querySelectorAll('.ra-mode-btn').forEach(button => {
            const active = button.dataset.raMode === mode;
            button.classList.toggle('active', active);
            button.setAttribute('aria-selected', String(active));
        });
        window.dispatchEvent(new Event('resize'));
    };

    document.querySelectorAll('.ra-mode-btn').forEach(button => {
        button.addEventListener('click', () => setRoleAMode(button.dataset.raMode));
    });
    raPresentationSteps.forEach((button, index) => button.addEventListener('click', () => setRaPresentationSlide(index)));
    document.querySelector('.ra-present-prev').addEventListener('click', () => setRaPresentationSlide(currentRaSlide - 1));
    document.querySelector('.ra-present-next').addEventListener('click', () => setRaPresentationSlide(currentRaSlide === raPresentationSlides.length - 1 ? 0 : currentRaSlide + 1));


    const rbPresentationSlides = [...document.querySelectorAll('#rb-exposition .rb-slide')];
    const rbPresentationSteps = [...document.querySelectorAll('#rb-exposition .rb-slide-step')];
    let currentRbSlide = 0;

    const setRbPresentationSlide = index => {
        currentRbSlide = Math.max(0, Math.min(rbPresentationSlides.length - 1, index));
        rbPresentationSlides.forEach((slide, slideIndex) => {
            const active = slideIndex === currentRbSlide;
            slide.hidden = !active;
            slide.classList.toggle('active', active);
        });
        rbPresentationSteps.forEach((step, stepIndex) => {
            const active = stepIndex === currentRbSlide;
            step.classList.toggle('active', active);
            if (active) step.setAttribute('aria-current', 'step');
            else step.removeAttribute('aria-current');
        });
        document.getElementById('rb-slide-count').textContent = `${currentRbSlide + 1} / ${rbPresentationSlides.length}`;
        document.querySelector('.rb-present-prev').disabled = currentRbSlide === 0;
        document.querySelector('.rb-present-next').innerHTML = currentRbSlide === rbPresentationSlides.length - 1
>>>>>>> 923b5326f3dec8d8b29766b6c8cc46e8dd637b22
            ? 'Volver al inicio <i class="fa-solid fa-rotate-left"></i>'
            : 'Siguiente <i class="fa-solid fa-arrow-right"></i>';
        window.dispatchEvent(new Event('resize'));
    };

    const setRoleBMode = mode => {
        const exposition = mode === 'exposition';
        if (exposition) setRbPresentationSlide(0);
        document.getElementById('rb-exposition').hidden = !exposition;
        document.getElementById('rb-analysis').hidden = exposition;
        document.querySelectorAll('.rb-mode-btn').forEach(button => {
            const active = button.dataset.rbMode === mode;
            button.classList.toggle('active', active);
            button.setAttribute('aria-selected', String(active));
        });
        window.dispatchEvent(new Event('resize'));
    };

    document.querySelectorAll('.rb-mode-btn').forEach(button => {
        button.addEventListener('click', () => setRoleBMode(button.dataset.rbMode));
    });
<<<<<<< HEAD
    presentationSteps.forEach((button, index) => button.addEventListener('click', () => setPresentationSlide(index)));
    document.querySelector('#rb-exposition .rb-present-prev').addEventListener('click', () => setPresentationSlide(currentPresentationSlide - 1));
    document.querySelector('#rb-exposition .rb-present-next').addEventListener('click', () => setPresentationSlide(currentPresentationSlide === presentationSlides.length - 1 ? 0 : currentPresentationSlide + 1));
=======
    rbPresentationSteps.forEach((button, index) => button.addEventListener('click', () => setRbPresentationSlide(index)));
    document.querySelector('.rb-present-prev').addEventListener('click', () => setRbPresentationSlide(currentRbSlide - 1));
    document.querySelector('.rb-present-next').addEventListener('click', () => setRbPresentationSlide(currentRbSlide === rbPresentationSlides.length - 1 ? 0 : currentRbSlide + 1));
    
>>>>>>> 923b5326f3dec8d8b29766b6c8cc46e8dd637b22
    document.addEventListener('keydown', event => {
        const expoAActive = document.getElementById('rol-a').classList.contains('active') && !document.getElementById('ra-exposition').hidden;
        const expoBActive = document.getElementById('rol-b').classList.contains('active') && !document.getElementById('rb-exposition').hidden;
        if ((!expoAActive && !expoBActive) || (event.target instanceof HTMLElement && ['INPUT', 'TEXTAREA', 'SELECT'].includes(event.target.tagName))) return;
        if (event.key === 'ArrowRight') {
            if (expoAActive) setRaPresentationSlide(currentRaSlide + 1);
            if (expoBActive) setRbPresentationSlide(currentRbSlide + 1);
        }
        if (event.key === 'ArrowLeft') {
            if (expoAActive) setRaPresentationSlide(currentRaSlide - 1);
            if (expoBActive) setRbPresentationSlide(currentRbSlide - 1);
        }
    });

    const renderHomeQuality = summary => {
        if (!summary) return;
        const integrity = document.getElementById('home-quality-integrity');
        const seriesContainer = document.getElementById('home-quality-series');
        const integrityItems = [
            `${summary.rows} registros mensuales`,
            `${summary.duplicateDates} fechas duplicadas`,
            `${summary.negativeHydrologyValues} valores negativos`
        ];
        if (integrity) {
            integrity.innerHTML = integrityItems.map(item => `<span><i class="fa-solid fa-circle-check" aria-hidden="true"></i>${item}</span>`).join('');
        }
        if (seriesContainer) {
            seriesContainer.innerHTML = summary.series.map((series, index) => {
                const missingLabel = series.missing === 0
                    ? 'Sin faltantes en cobertura'
                    : `${series.missing} ${series.missing === 1 ? 'mes ausente' : 'meses ausentes'}`;
                const period = `${series.coverageStart} — ${series.coverageEnd}`;
                return `<article class="quality-row quality-row-${index + 1}">
                    <div class="quality-row-heading">
                        <div><strong>${series.label}</strong><small>${period} · ${series.unit}</small></div>
                        <b>${series.completenessPct.toFixed(2)}%</b>
                    </div>
                    <div class="quality-track" role="progressbar" aria-label="Completitud de ${series.label}" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${series.completenessPct}"><span style="width:${series.completenessPct}%"></span></div>
                    <div class="quality-row-detail"><span>${series.available} de ${series.expected} meses con dato</span><span>${missingLabel}</span></div>
                </article>`;
            }).join('');
        }
    };

    // 3. Renderizado de Gráficos (Plotly)
    const renderAllCharts = () => {
        if (!window.dashboardData) {
            console.warn("No se encontró window.dashboardData.");
            return;
        }

        const data = window.dashboardData;
        renderHomeQuality(data.qualitySummary);

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

        // === ROL A: Ciclo Anual ===
        if (data.cicloAnual) {
            const traces = [
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
            ];
            const layout = {
                ...baseLayout,
                yaxis: { title: 'Precipitación (mm/mes)', gridcolor: colors.grid },
                yaxis2: { title: 'Caudal (m³/s)', overlaying: 'y', side: 'right', showgrid: false },
                legend: { orientation: 'h', y: 1.15, x: 0.1 }
            };
            if (document.getElementById('chart-ciclo-anual')) {
                Plotly.newPlot('chart-ciclo-anual', traces, layout, {responsive: true, displayModeBar: false});
            }
            if (document.getElementById('chart-ciclo-anual-expo')) {
                Plotly.newPlot('chart-ciclo-anual-expo', traces, { ...layout, margin: { t: 15, r: 40, l: 50, b: 30 } }, {responsive: true, displayModeBar: false});
            }
        }

        // === ROL A: Histograma Precipitación Local vs IMERG ===
        if (data.histPrecip) {
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
            const layout = {
                ...baseLayout,
                barmode: 'group',
                xaxis: { title: 'Precipitación Mensual (mm)' },
                yaxis: { title: 'Frecuencia (Meses)' },
                legend: { orientation: 'h', y: 1.15 }
            };
            if (document.getElementById('chart-hist-precip')) {
                Plotly.newPlot('chart-hist-precip', traces, layout, {responsive: true, displayModeBar: false});
            }
            if (document.getElementById('chart-hist-precip-expo')) {
                Plotly.newPlot('chart-hist-precip-expo', traces, { ...layout, margin: { t: 15, r: 15, l: 50, b: 40 } }, {responsive: true, displayModeBar: false});
            }
        }

        // === ROL A: Impacto de la Megasequía (Subperiodos) ===
        if (data.subperiodos) {
            const traces = [
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
            ];
            const layout = {
                ...baseLayout,
                xaxis: { title: 'Mes Calendario' },
                yaxis: { title: 'Lámina de Escorrentía (mm/mes)' },
                legend: { orientation: 'h', y: 1.15 }
            };
            if (document.getElementById('chart-subperiodos')) {
                Plotly.newPlot('chart-subperiodos', traces, layout, {responsive: true, displayModeBar: false});
            }
            if (document.getElementById('chart-subperiodos-expo')) {
                Plotly.newPlot('chart-subperiodos-expo', traces, { ...layout, margin: { t: 15, r: 15, l: 50, b: 40 } }, {responsive: true, displayModeBar: false});
            }
        }

        // === ROL B: Relaciones y concordancia ===
        const scatterPairs = data.scatterPairs || {};
        const pairCharts = [
            { key: 'precipitation', id: 'chart-scatter-imerg', xTitle: 'P local (mm/mes)', yTitle: 'IMERG (mm/mes)', identity: true },
            { key: 'localFlow', id: 'chart-scatter-local-flow', xTitle: 'P local (mm/mes)', yTitle: 'Q (m³/s)' },
            { key: 'imergFlow', id: 'chart-scatter-imerg-flow', xTitle: 'IMERG (mm/mes)', yTitle: 'Q (m³/s)' },
            { key: 'localRunoff', id: 'chart-scatter-local-runoff', xTitle: 'P local (mm/mes)', yTitle: 'R (mm/mes)' },
            { key: 'imergRunoff', id: 'chart-scatter-imerg-runoff', xTitle: 'IMERG (mm/mes)', yTitle: 'R (mm/mes)' }
        ];
        pairCharts.forEach(config => {
            const pair = scatterPairs[config.key];
            if (!pair || !document.getElementById(config.id)) return;
            const upper = pair.maxVal;
            const traces = pair.traces.map(trace => ({
                x: trace.x,
                y: trace.y,
                customdata: trace.date,
                type: 'scatter',
                mode: 'markers',
                name: trace.name,
                marker: { size: config.identity ? 6 : 5, opacity: 0.7, color: seasonColors[trace.name], line: { width: 0 } },
                hovertemplate: '%{customdata}<br>x: %{x:.1f}<br>y: %{y:.1f}<extra>%{fullData.name}</extra>'
            }));
            if (config.identity) {
                traces.push({
                    x: [0, upper], y: [0, upper], type: 'scatter', mode: 'lines', name: 'Identidad 1:1',
                    line: { color: '#e6e3d9', dash: 'dash', width: 1.5 }, hoverinfo: 'skip'
                });
            }
            const layout = {
                ...baseChartLayout(),
                margin: { t: 10, r: 12, l: 54, b: 48 },
                xaxis: { ...baseChartLayout().xaxis, title: config.xTitle },
                yaxis: { ...baseChartLayout().yaxis, title: config.yTitle },
                legend: config.identity ? { orientation: 'h', y: -0.24, x: 0, font: { size: 9 } } : { orientation: 'h', y: -0.28, x: 0, font: { size: 9 } }
            };
            if (config.identity) {
                layout.xaxis.range = [0, upper];
                layout.xaxis.constrain = 'domain';
                layout.yaxis.range = [0, upper];
                layout.yaxis.scaleanchor = 'x';
                layout.yaxis.scaleratio = 1;
                layout.yaxis.constrain = 'domain';
            }
            Plotly.newPlot(config.id, traces, layout, { responsive: true, displayModeBar: false });
        });

        // Resumen cuantitativo y tamaños de muestra por relación.
        const setPairSummary = (key, sampleId, statsId) => {
            const pair = scatterPairs[key];
            if (!pair) return;
            const sample = document.getElementById(sampleId);
            const stats = document.getElementById(statsId);
            if (sample) sample.textContent = `n = ${pair.n} · ${pair.periodStart}–${pair.periodEnd}`;
            if (stats) stats.textContent = `Pearson r ${number(pair.pearson, 3)} · Spearman ρ ${number(pair.spearman, 3)}`;
        };
        setPairSummary('precipitation', 'rb-sample-precip', null);
        setPairSummary('localFlow', 'rb-sample-local-q', 'rb-stat-local-q');
        setPairSummary('imergFlow', 'rb-sample-imerg-q', 'rb-stat-imerg-q');
        setPairSummary('localRunoff', 'rb-sample-local-r', 'rb-stat-local-r');
        setPairSummary('imergRunoff', 'rb-sample-imerg-r', 'rb-stat-imerg-r');
        const precip = scatterPairs.precipitation;
        if (precip) {
            document.getElementById('rb-correlation').textContent = `${number(precip.pearson, 3)} / ${number(precip.spearman, 3)}`;
            document.getElementById('rb-bias').textContent = `${number(precip.meanBias)} mm/mes`;
            document.getElementById('rb-mae-rmse').textContent = `${number(precip.mae)} / ${number(precip.rmse)} mm/mes`;
            document.getElementById('rb-pbias').textContent = `${number(precip.pbias)} %`;
            const intensityRow = (data.erroresGrupo || []).filter(row => row.group_type === 'cuartil_P_local').slice(-1)[0];
            if (intensityRow) {
                document.getElementById('rb-intensity-note').innerHTML = `<strong>Por intensidad</strong><span>En el cuartil más lluvioso, sesgo medio PI − PL: ${number(intensityRow.mean_bias_PI_minus_PL_mm_month)} mm/mes; RMSE ${number(intensityRow.rmse_mm_month)} mm/mes (n=${intensityRow.n}).</span>`;
            }
            if (data.mesesInfluyentesShare != null) {
                document.getElementById('rb-influential-note').textContent = `Los cinco mayores errores absolutos concentran ${number(data.mesesInfluyentesShare)} % de la suma de errores cuadrados; se mantienen en los resultados principales.`;
            }
        }

        if (precip && document.getElementById('chart-expo-precip')) {
            const upper = precip.maxVal;
            const traces = precip.traces.map(trace => ({
                x: trace.x,
                y: trace.y,
                name: trace.name,
                customdata: trace.date,
                type: 'scatter',
                mode: 'markers',
                marker: { color: seasonColors[trace.name], size: 5, opacity: 0.72 },
                hovertemplate: '%{customdata}<br>Local: %{x:.1f}<br>IMERG: %{y:.1f}<extra>%{fullData.name}</extra>'
            }));
            traces.push({
                x: [0, upper], y: [0, upper], name: 'Identidad 1:1', type: 'scatter', mode: 'lines',
                line: { color: '#e5e1d4', dash: 'dash', width: 1.5 }, hoverinfo: 'skip'
            });
            Plotly.newPlot('chart-expo-precip', traces, {
                ...baseChartLayout(),
                margin: { t: 10, r: 12, l: 52, b: 42 },
                xaxis: { ...baseChartLayout().xaxis, title: 'Local (mm/mes)', range: [0, upper], constrain: 'domain' },
                yaxis: { ...baseChartLayout().yaxis, title: 'IMERG (mm/mes)', range: [0, upper], constrain: 'domain', scaleanchor: 'x', scaleratio: 1 },
                legend: { orientation: 'h', y: -0.23, x: 0, font: { size: 9 } }
            }, { responsive: true, displayModeBar: false });

            document.getElementById('rb-expo-sample-p').textContent = `n=${precip.n} · ${precip.periodStart} a ${precip.periodEnd}`;
            document.getElementById('rb-expo-correlation').textContent = `${number(precip.pearson, 3)} / ${number(precip.spearman, 3)}`;
            document.getElementById('rb-expo-bias').textContent = `${number(precip.meanBias)} mm/mes`;
            document.getElementById('rb-expo-errors').textContent = `${number(precip.mae)} / ${number(precip.rmse)} mm/mes`;
            document.getElementById('rb-expo-extremes').textContent = `Los cinco errores mayores suman ${number(data.mesesInfluyentesShare)} % del error cuadrático total.`;
        }

        if (data.rezagos && document.getElementById('chart-expo-lag')) {
            const lagTraces = [
                { name: 'P local', y: data.rezagos.r_local, n: data.rezagos.n_local, color: '#d97853' },
                { name: 'IMERG', y: data.rezagos.r_imerg, n: data.rezagos.n_imerg, color: '#56a9ba' }
            ].filter(trace => trace.y?.length).map(trace => ({
                x: data.rezagos.lags,
                y: trace.y,
                customdata: trace.n,
                name: trace.name,
                type: 'scatter',
                mode: 'lines+markers',
                line: { color: trace.color, width: 2.5 },
                marker: { color: trace.color, size: 6 },
                hovertemplate: 'k=%{x} meses<br>Pearson r=%{y:.3f}<br>n=%{customdata}<extra>%{fullData.name}</extra>'
            }));
            Plotly.newPlot('chart-expo-lag', lagTraces, {
                ...baseChartLayout(),
                margin: { t: 12, r: 12, l: 52, b: 42 },
                xaxis: { ...baseChartLayout().xaxis, title: 'Precipitación previa, k (meses)', dtick: 2 },
                yaxis: { ...baseChartLayout().yaxis, title: 'Pearson r', range: [-0.05, 0.6], zeroline: true },
                legend: { orientation: 'h', y: -0.24, x: 0, font: { size: 9 } },
                shapes: [{ type: 'line', x0: 7, x1: 7, y0: 0, y1: 1, yref: 'paper', line: { color: '#e2a64c', dash: 'dot', width: 1.5 } }]
            }, { responsive: true, displayModeBar: false });
            const lagIndex = data.rezagos.lags.indexOf(7);
            document.getElementById('rb-expo-lag-local').textContent = `r=${number(data.rezagos.r_local[lagIndex], 3)} · n=${data.rezagos.n_local[lagIndex]}`;
            document.getElementById('rb-expo-lag-imerg').textContent = `r=${number(data.rezagos.r_imerg[lagIndex], 3)} · n=${data.rezagos.n_imerg[lagIndex]}`;
        }

        if (document.getElementById('chart-expo-model-q')) {
            const modelSeries = [
                { name: 'Climatología Q', predictor: 'P_local_mm', model: 'Climatología mensual Q', color: '#83939a' },
                { name: 'Anomalías · P local', predictor: 'P_local_mm', model: 'Regresión de anomalías con rezago', color: '#d97853' },
                { name: 'Anomalías · IMERG', predictor: 'P_IMERG_mm', model: 'Regresión de anomalías con rezago', color: '#56a9ba' }
            ];
            const traces = modelSeries.map(series => ({
                x: blockLabels.map(block => blockNames[block]),
                y: blockLabels.map(block => findBlockMetric('estimar_caudal', series.predictor, series.model, block)?.mae ?? null),
                customdata: blockLabels.map(block => {
                    const row = findBlockMetric('estimar_caudal', series.predictor, series.model, block);
                    return row ? [row.n, row.rmse] : [];
                }),
                name: series.name,
                type: 'bar',
                marker: { color: series.color },
                hovertemplate: '<b>%{x}</b><br>%{fullData.name}<br>MAE=%{y:.2f} m³/s<br>RMSE=%{customdata[1]:.2f} m³/s<br>n=%{customdata[0]}<extra></extra>'
            }));
            Plotly.newPlot('chart-expo-model-q', traces, {
                ...baseChartLayout(),
                barmode: 'group',
                margin: { t: 10, r: 10, l: 54, b: 42 },
                xaxis: { ...baseChartLayout().xaxis, title: 'Bloque de evaluación' },
                yaxis: { ...baseChartLayout().yaxis, title: 'MAE (m³/s)', rangemode: 'tozero' },
                legend: { orientation: 'h', y: -0.25, x: 0, font: { size: 9 } }
            }, { responsive: true, displayModeBar: false });
            blockLabels.forEach((block, index) => {
                const row = findBlockMetric('estimar_caudal', 'P_local_mm', 'Regresión de anomalías con rezago', block);
                document.getElementById(`rb-expo-n${index + 1}`).textContent = row ? row.n : '—';
            });
            const selectedLags = data.rezagosSeleccionados || [];
            const lagSequence = predictor => blockLabels.map(block => {
                const row = selectedLags.find(item => String(item.predictor).includes(predictor) && item.outer_fold === block);
                return row ? number(row.candidate_lag_months, 0) : '—';
            }).join(' / ');
            document.getElementById('rb-expo-lags-selected').textContent = `P local: ${lagSequence('P_local_mm')} meses · IMERG: ${lagSequence('P_IMERG_mm')} meses`;
        }

        renderPrecipMetricsTable();
        renderQMetricsTable();
        renderQModelChart();

        // === ROL B: Correlaciones de anomalías por rezago ===
        if (data.rezagos && document.getElementById('chart-rezagos')) {
            const lagTraces = [
                { y: data.rezagos.r_local, name: 'Pearson · P local', color: '#d97853', dash: 'solid' },
                { y: data.rezagos.rho_local, name: 'Spearman · P local', color: '#e2a64c', dash: 'dot' },
                { y: data.rezagos.r_imerg, name: 'Pearson · IMERG', color: '#56a9ba', dash: 'solid' },
                { y: data.rezagos.rho_imerg, name: 'Spearman · IMERG', color: '#79a878', dash: 'dot' }
            ].filter(trace => trace.y && trace.y.length).map(trace => ({
                x: data.rezagos.lags,
                y: trace.y,
                type: 'scatter',
                mode: 'lines+markers',
                name: trace.name,
                line: { color: trace.color, width: trace.dash === 'solid' ? 2.5 : 1.8, dash: trace.dash },
                marker: { size: trace.dash === 'solid' ? 6 : 5, color: trace.color },
                hovertemplate: 'k=%{x} meses<br>r/ρ=%{y:.3f}<extra>%{fullData.name}</extra>'
            }));
            Plotly.newPlot('chart-rezagos', lagTraces, {
                ...baseChartLayout(),
                margin: { t: 12, r: 18, l: 54, b: 48 },
                xaxis: { ...baseChartLayout().xaxis, title: 'Lluvia previa, t−k (meses)', dtick: 1 },
                yaxis: { ...baseChartLayout().yaxis, title: 'Correlación de anomalías', range: [-0.1, 0.65], zeroline: true },
                legend: { orientation: 'h', y: -0.28, x: 0, font: { size: 9 } },
                shapes: [{ type: 'line', x0: 7, x1: 7, y0: 0, y1: 1, yref: 'paper', line: { color: '#d97853', dash: 'dot', width: 1 } }]
            }, { responsive: true, displayModeBar: false });
        }

        // === ROL B: Predicción externa y residuos ===
        if (data.validacionTemporal && document.getElementById('chart-validacion-temporal')) {
            const validation = data.validacionTemporal;
            Plotly.newPlot('chart-validacion-temporal', [
                { x: validation.fechas, y: validation.observado, name: 'Q observado', type: 'scatter', mode: 'lines', line: { color: '#e8e5da', width: 1.7 } },
                { x: validation.fechas, y: validation.modeladoLocal, name: 'Modelo · P local', type: 'scatter', mode: 'lines', connectgaps: false, line: { color: '#d97853', width: 1.7 } },
                { x: validation.fechas, y: validation.modeladoImerg, name: 'Modelo · IMERG', type: 'scatter', mode: 'lines', connectgaps: false, line: { color: '#56a9ba', width: 1.7 } }
            ], {
                ...baseChartLayout(),
                margin: { t: 12, r: 18, l: 60, b: 50 },
                xaxis: { ...baseChartLayout().xaxis, title: 'Fecha de evaluación externa', type: 'date' },
                yaxis: { ...baseChartLayout().yaxis, title: 'Caudal medio mensual (m³/s)', rangemode: 'tozero' },
                legend: { orientation: 'h', y: 1.12, x: 0, font: { size: 10 } },
                shapes: [
                    { type: 'line', x0: '2013-01-01', x1: '2013-01-01', y0: 0, y1: 1, yref: 'paper', line: { color: '#94a3a0', dash: 'dot', width: 1 } },
                    { type: 'line', x0: '2016-01-01', x1: '2016-01-01', y0: 0, y1: 1, yref: 'paper', line: { color: '#94a3a0', dash: 'dot', width: 1 } }
                ]
            }, { responsive: true, displayModeBar: false });

            const residuals = validation.residuals || {};
            const residualColors = { local: '#d97853', imerg: '#56a9ba' };
            const residualNames = { local: 'P local', imerg: 'IMERG' };
            const residualTimeTraces = Object.entries(residuals).map(([key, values]) => ({
                x: values.date, y: values.residual, name: residualNames[key], type: 'scatter', mode: 'markers',
                marker: { color: residualColors[key], size: 5, opacity: 0.7 },
                hovertemplate: '%{x}<br>Residuo: %{y:.1f} m³/s<extra>%{fullData.name}</extra>'
            }));
            Plotly.newPlot('chart-residuo-tiempo', residualTimeTraces, {
                ...baseChartLayout(), xaxis: { ...baseChartLayout().xaxis, title: 'Fecha' },
                yaxis: { ...baseChartLayout().yaxis, title: 'Predicción − observado (m³/s)', zeroline: true },
                shapes: [{ type: 'line', x0: '2010-01-01', x1: '2020-04-01', y0: 0, y1: 0, line: { color: '#9aa8a5', dash: 'dot', width: 1 } }],
                legend: { orientation: 'h', y: 1.1, x: 0, font: { size: 9 } }
            }, { responsive: true, displayModeBar: false });

            const residualValueTraces = Object.entries(residuals).map(([key, values]) => ({
                x: values.predicted, y: values.residual, name: residualNames[key], type: 'scatter', mode: 'markers',
                customdata: values.date,
                marker: { color: residualColors[key], size: 5, opacity: 0.65 },
                hovertemplate: '%{customdata}<br>Estimado: %{x:.1f}<br>Residuo: %{y:.1f}<extra>%{fullData.name}</extra>'
            }));
            Plotly.newPlot('chart-residuo-prediccion', residualValueTraces, {
                ...baseChartLayout(), xaxis: { ...baseChartLayout().xaxis, title: 'Caudal estimado (m³/s)' },
                yaxis: { ...baseChartLayout().yaxis, title: 'Residuo (m³/s)', zeroline: true },
                shapes: [{ type: 'line', x0: 0, x1: 1, xref: 'paper', y0: 0, y1: 0, line: { color: '#9aa8a5', dash: 'dot', width: 1 } }],
                legend: { orientation: 'h', y: 1.1, x: 0, font: { size: 9 } }
            }, { responsive: true, displayModeBar: false });

            const residualMonthTraces = Object.entries(residuals).map(([key, values]) => ({
                x: values.month, y: values.residual, name: residualNames[key], type: 'box', boxpoints: 'outliers',
                marker: { color: residualColors[key], size: 4 }, line: { color: residualColors[key], width: 1.2 },
                hovertemplate: 'Mes %{x}<br>Residuo: %{y:.1f} m³/s<extra>%{fullData.name}</extra>'
            }));
            Plotly.newPlot('chart-residuo-mes', residualMonthTraces, {
                ...baseChartLayout(), boxmode: 'group',
                xaxis: { ...baseChartLayout().xaxis, title: 'Mes calendario', tickmode: 'array', tickvals: [1, 3, 5, 7, 9, 11], ticktext: ['Ene', 'Mar', 'May', 'Jul', 'Sep', 'Nov'] },
                yaxis: { ...baseChartLayout().yaxis, title: 'Residuo (m³/s)', zeroline: true },
                legend: { orientation: 'h', y: 1.1, x: 0, font: { size: 9 } }
            }, { responsive: true, displayModeBar: false });
        }

        renderRoleC(data.rolC);

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

    document.querySelectorAll('.rb-predictor-btn').forEach(button => {
        button.addEventListener('click', () => {
            selectedQPredictor = button.dataset.predictor;
            document.querySelectorAll('.rb-predictor-btn').forEach(item => {
                const active = item === button;
                item.classList.toggle('active', active);
                item.setAttribute('aria-selected', String(active));
            });
            renderQMetricsTable();
            renderQModelChart();
        });
    });

    document.querySelectorAll('.rb-metric-btn').forEach(button => {
        button.addEventListener('click', () => {
            selectedQMetric = button.dataset.metric;
            document.querySelectorAll('.rb-metric-btn').forEach(item => item.classList.toggle('active', item === button));
            renderQModelChart();
        });
    });


    // === ROL C: exposición de tendencias y Fourier ===
    const rcSlides = [...document.querySelectorAll('#rc-exposition .rc-slide')];
    const rcSteps = [...document.querySelectorAll('#rc-exposition .rc-step')];
    let rcCurrent = 0;
    const setRoleCSlide = index => {
        if (!rcSlides.length) return;
        rcCurrent = Math.max(0, Math.min(rcSlides.length - 1, index));
        rcSlides.forEach((slide, i) => {
            slide.hidden = i !== rcCurrent;
            slide.classList.toggle('active', i === rcCurrent);
        });
        rcSteps.forEach((step, i) => {
            step.classList.toggle('active', i === rcCurrent);
            if (i === rcCurrent) step.setAttribute('aria-current', 'step');
            else step.removeAttribute('aria-current');
        });
        document.getElementById('rc-slide-count').textContent = `${rcCurrent + 1} / ${rcSlides.length}`;
        document.querySelector('#rc-exposition .rc-present-prev').disabled = rcCurrent === 0;
        document.querySelector('#rc-exposition .rc-present-next').innerHTML = rcCurrent === rcSlides.length - 1
            ? 'Volver al inicio <i class="fa-solid fa-rotate-left"></i>'
            : 'Siguiente <i class="fa-solid fa-arrow-right"></i>';
        window.dispatchEvent(new Event('resize'));
    };
    if (rcSlides.length) {
        rcSteps.forEach((step, i) => step.addEventListener('click', () => setRoleCSlide(i)));
        document.querySelector('#rc-exposition .rc-present-prev').addEventListener('click', () => setRoleCSlide(rcCurrent - 1));
        document.querySelector('#rc-exposition .rc-present-next').addEventListener('click', () => setRoleCSlide(rcCurrent === rcSlides.length - 1 ? 0 : rcCurrent + 1));
        document.addEventListener('keydown', event => {
            if (!document.getElementById('rol-c').classList.contains('active')) return;
            if (event.target instanceof HTMLElement && ['INPUT', 'TEXTAREA', 'SELECT'].includes(event.target.tagName)) return;
            if (event.key === 'ArrowRight') setRoleCSlide(rcCurrent + 1);
            if (event.key === 'ArrowLeft') setRoleCSlide(rcCurrent - 1);
        });
    }

    const rcColors = { pl: '#56a9ba', q: '#d97853', pos: 'rgba(86, 169, 186, 0.55)', neg: 'rgba(217, 120, 83, 0.55)' };
    const setText = (id, text) => { const el = document.getElementById(id); if (el) el.textContent = text; };
    const signed = (value, digits = 1) => `${value > 0 ? '+' : value < 0 ? '−' : ''}${Math.abs(Number(value)).toFixed(digits)}`;
    const pText = p => (p < 0.001 ? 'p < 0.001' : `p = ${Number(p).toFixed(3)}`);
    const plotConfig = { responsive: true, displayModeBar: false };

    const renderRoleC = rc => {
        if (!rc || !document.getElementById('chart-rc-mensual')) return;
        const months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
        const h = rc.headline;
        setText('rc-q-ols', `${signed(h.Caudal_m3s.ols.pendiente)} m³/s/déc · ${pText(h.Caudal_m3s.ols.p)}`);
        setText('rc-p-ols', `${signed(h.P_local_mm.ols.pendiente)} mm/mes/déc · ${pText(h.P_local_mm.ols.p)}`);
        setText('rc-pi-ols', `${signed(h.P_IMERG_mm.ols.pendiente)} mm/mes/déc · ${pText(h.P_IMERG_mm.ols.p)}`);
        setText('rc-t-ols', `${signed(h.Temp_C.ols.pendiente, 2)} °C/déc · ${pText(h.Temp_C.ols.p)} (n.s.)`);

        // 01 · Pendientes mensuales relativas
        const monthlyTrace = (key, name, color, offset) => {
            const d = rc.monthlySlopes[key];
            return {
                x: months.map((_, i) => i + 1 + offset), y: d.pct, name, type: 'scatter', mode: 'markers',
                error_y: { type: 'data', symmetric: false, array: d.pctHigh.map((v, i) => v - d.pct[i]),
                    arrayminus: d.pct.map((v, i) => v - d.pctLow[i]), color, thickness: 2, width: 0 },
                marker: { size: 10, color, symbol: d.signifFdr.map(s => (s ? 'circle' : 'circle-open')), line: { width: 2, color } },
                customdata: d.abs.map((v, i) => [months[i], v, d.q[i]]),
                hovertemplate: `<b>${name} · %{customdata[0]}</b><br>%{y:.1f} % por década<br>Pendiente: %{customdata[1]:.2f} ${key === 'Caudal_m3s' ? 'm³/s' : 'mm/mes'} por década<br>q FDR = %{customdata[2]:.3f}<extra></extra>`
            };
        };
        Plotly.newPlot('chart-rc-mensual', [
            monthlyTrace('P_local_mm', 'Precipitación P_L', rcColors.pl, -0.14),
            monthlyTrace('Caudal_m3s', 'Caudal Q', rcColors.q, 0.14)
        ], {
            ...baseChartLayout(),
            xaxis: { ...baseChartLayout().xaxis, tickvals: months.map((_, i) => i + 1), ticktext: months },
            yaxis: { ...baseChartLayout().yaxis, title: '% de la media mensual por década', zeroline: true, zerolinewidth: 1.5 },
            legend: { orientation: 'h', y: 1.1, x: 0 },
            margin: { t: 26, r: 12, l: 62, b: 36 }
        }, plotConfig);

        // 02 · Tendencia frente a escalón
        const wyP = rc.waterYear.P_local_mm, wyQ = rc.waterYear.Caudal_m3s;
        setText('rc-pettitt', `${wyQ.stepYear} (${pText(wyQ.pPettitt)}) / ${wyP.stepYear} (${pText(wyP.pPettitt)})`);
        setText('rc-q-2009', `${signed(wyQ.until2009Slope)} m³/s/déc · ${pText(wyQ.until2009P)}`);
        setText('rc-p-2009', `${signed(wyP.until2009Slope)} mm/mes/déc · ${pText(wyP.until2009P)}`);
        setText('rc-aic', `${signed(wyQ.deltaAic, 2)} (Q) · ${signed(wyP.deltaAic, 2)} (P_L)`);
        const stepTraces = (wy, axis, unit, showLegend) => [
            { x: wy.years, y: wy.anomaly, type: 'bar', yaxis: axis, xaxis: 'x', showlegend: false,
              marker: { color: wy.anomaly.map(v => (v >= 0 ? rcColors.pos : rcColors.neg)) },
              hovertemplate: `Año hidrológico %{x}<br>Anomalía media: %{y:.1f} ${unit}<extra></extra>` },
            { x: wy.years, y: wy.trend, type: 'scatter', mode: 'lines', yaxis: axis, name: 'Tendencia lineal',
              line: { color: '#3b82f6', width: 2.5 }, showlegend: showLegend, hoverinfo: 'skip' },
            { x: wy.years, y: wy.step, type: 'scatter', mode: 'lines', yaxis: axis, name: 'Escalón (Pettitt)',
              line: { color: '#e2a64c', width: 2.5, shape: 'hv' }, showlegend: showLegend, hoverinfo: 'skip' }
        ];
        const base2 = baseChartLayout();
        Plotly.newPlot('chart-rc-salto', [
            ...stepTraces(wyP, 'y', 'mm/mes', true),
            ...stepTraces(wyQ, 'y2', 'm³/s', false)
        ], {
            ...base2,
            grid: { rows: 2, columns: 1, pattern: 'independent', roworder: 'top to bottom' },
            xaxis: { ...base2.xaxis, anchor: 'y2', range: [1979, 2020] },
            yaxis: { ...base2.yaxis, domain: [0.55, 1], title: 'P_L [mm/mes]', zeroline: true },
            yaxis2: { ...base2.yaxis, domain: [0, 0.45], title: 'Q [m³/s]', zeroline: true },
            legend: { orientation: 'h', y: 1.12, x: 0 },
            bargap: 0.15,
            margin: { t: 26, r: 12, l: 62, b: 36 }
        }, plotConfig);

        // 03 · Balance anual
        const b = rc.balance;
        setText('rc-balance-n', `${b.nPre} + ${b.nPost} años`);
        setText('rc-dpdr', `${signed(b.dPpct)} % / ${signed(b.dRpct)} %`);
        setText('rc-elast', `≈ ${Number(b.elasticity).toFixed(2)}`);
        setText('rc-resid', `${signed(b.residPre, 0)} → ${signed(b.residPost, 0)} mm/año`);
        const allYears = Array.from({ length: 40 }, (_, i) => 1980 + i);
        const byYear = arr => allYears.map(y => { const i = b.years.indexOf(y); return i >= 0 ? arr[i] : null; });
        const meanSeg = (value, from, to, color) => ({ x: [from, to], y: [value, value], type: 'scatter', mode: 'lines',
            line: { color, width: 2, dash: 'dash' }, showlegend: false, hovertemplate: `Media ${from}–${to}: ${value} mm/año<extra></extra>` });
        Plotly.newPlot('chart-rc-balance', [
            { x: allYears, y: byYear(b.P), name: 'Precipitación P_L', type: 'scatter', mode: 'lines+markers',
              line: { color: rcColors.pl, width: 2 }, marker: { size: 6 }, connectgaps: false,
              hovertemplate: 'Año %{x}<br>P = %{y:.0f} mm<extra></extra>' },
            { x: allYears, y: byYear(b.R), name: 'Escorrentía R', type: 'scatter', mode: 'lines+markers',
              line: { color: rcColors.q, width: 2 }, marker: { size: 6 }, connectgaps: false,
              hovertemplate: 'Año %{x}<br>R = %{y:.0f} mm<extra></extra>' },
            meanSeg(b.preP, 1980, 2009, rcColors.pl), meanSeg(b.postP, 2010, 2019, rcColors.pl),
            meanSeg(b.preR, 1980, 2009, rcColors.q), meanSeg(b.postR, 2010, 2019, rcColors.q)
        ], {
            ...baseChartLayout(),
            xaxis: { ...baseChartLayout().xaxis, title: 'Año hidrológico (abr–mar)' },
            yaxis: { ...baseChartLayout().yaxis, title: 'mm/año', rangemode: 'tozero' },
            shapes: [{ type: 'line', x0: 2009.5, x1: 2009.5, yref: 'paper', y0: 0, y1: 1, line: { color: '#94a3b8', width: 1, dash: 'dot' } }],
            annotations: [{ x: 2010, y: 1, yref: 'paper', text: 'Megasequía', showarrow: false, xanchor: 'left', font: { size: 10 } }],
            legend: { orientation: 'h', y: 1.1, x: 0 },
            margin: { t: 26, r: 12, l: 62, b: 44 }
        }, plotConfig);

        // 04 · Espectros
        const fr = rc.bandFractions;
        const ann = key => Math.round(100 * fr[key].anual);
        setText('rc-anual', `${ann('comun|Temp_C|C')} / ${ann('comun|P_IMERG_mm|C')} / ${ann('completo|Caudal_m3s|C')} / ${ann('completo|P_local_mm|C')} %`);
        setText('rc-interanual', `${Math.round(100 * fr['completo|P_local_mm|A'].interanual)} % / ${Math.round(100 * fr['completo|Caudal_m3s|A'].interanual)} %`);
        setText('rc-r1', `${rc.spectra.P_local_mm.r1.toFixed(2)} / ${rc.spectra.Caudal_m3s.r1.toFixed(2)}`);
        const spec = (key, name, color) => [
            { x: rc.spectra[key].f, y: rc.spectra[key].p, name, type: 'scatter', mode: 'lines', line: { color, width: 2.5 },
              hovertemplate: `${name}<br>f = %{x:.3f} ciclos/mes (periodo %{customdata:.1f} meses)<br>DEP/var = %{y:.2f}<extra></extra>`,
              customdata: rc.spectra[key].f.map(f => 1 / f) },
            { x: rc.spectra[key].f, y: rc.spectra[key].ar1, name: `AR(1) r₁=${rc.spectra[key].r1.toFixed(2)}`, type: 'scatter', mode: 'lines',
              line: { color, width: 1.5, dash: 'dash' }, hoverinfo: 'skip' }
        ];
        const base4 = baseChartLayout();
        Plotly.newPlot('chart-rc-espectro', [...spec('P_local_mm', 'Precipitación P_L', rcColors.pl), ...spec('Caudal_m3s', 'Caudal Q', rcColors.q)], {
            ...base4,
            xaxis: { ...base4.xaxis, title: 'Frecuencia [ciclos/mes]', range: [0, 0.5] },
            yaxis: { ...base4.yaxis, title: 'DEP / varianza', type: 'log' },
            shapes: [
                { type: 'rect', x0: 0, x1: 1 / 18, yref: 'paper', y0: 0, y1: 1, fillcolor: 'rgba(148,163,184,0.12)', line: { width: 0 } },
                { type: 'line', x0: 1 / 12, x1: 1 / 12, yref: 'paper', y0: 0, y1: 1, line: { color: '#94a3b8', width: 1, dash: 'dot' } },
                { type: 'line', x0: 1 / 6, x1: 1 / 6, yref: 'paper', y0: 0, y1: 1, line: { color: '#94a3b8', width: 1, dash: 'dot' } }
            ],
            annotations: [
                { x: 1 / 36, y: 1.02, yref: 'paper', text: 'Interanual', showarrow: false, font: { size: 10 } },
                { x: 1 / 12, y: 1.02, yref: 'paper', text: '12 m', showarrow: false, font: { size: 10 } },
                { x: 1 / 6, y: 1.02, yref: 'paper', text: '6 m', showarrow: false, font: { size: 10 } }
            ],
            legend: { orientation: 'h', y: -0.22, x: 0 },
            margin: { t: 26, r: 12, l: 62, b: 70 }
        }, plotConfig);
    };

    // Renderizar al cargar
    setTimeout(renderAllCharts, 120);
    let resizeTimer;
    window.addEventListener('resize', () => {
        window.clearTimeout(resizeTimer);
        resizeTimer = window.setTimeout(() => {
            document.querySelectorAll('.view.active .js-plotly-plot').forEach(plot => {
                if (plot.getClientRects().length) Plotly.Plots.resize(plot);
            });
        }, 100);
    });
});
