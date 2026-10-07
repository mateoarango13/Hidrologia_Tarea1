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

    // === ROL A: Controles de presentación y modo ===
    const raPresentationSlides = [...document.querySelectorAll('#ra-exposition .ra-slide')];
    const raPresentationSteps = [...document.querySelectorAll('.ra-slide-step')];
    let currentRaSlide = 0;

    const setRaPresentationSlide = index => {
        if (!raPresentationSlides.length) return;
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
        const countEl = document.getElementById('ra-slide-count');
        if (countEl) countEl.textContent = `${currentRaSlide + 1} / ${raPresentationSlides.length}`;
        const prevBtn = document.querySelector('.ra-present-prev');
        if (prevBtn) prevBtn.disabled = currentRaSlide === 0;
        const nextBtn = document.querySelector('.ra-present-next');
        if (nextBtn) {
            nextBtn.innerHTML = currentRaSlide === raPresentationSlides.length - 1
                ? 'Volver al inicio <i class="fa-solid fa-rotate-left"></i>'
                : 'Siguiente <i class="fa-solid fa-arrow-right"></i>';
        }
        window.dispatchEvent(new Event('resize'));
    };

    const setRoleAMode = mode => {
        const exposition = mode === 'exposition';
        if (exposition) setRaPresentationSlide(0);
        const expoEl = document.getElementById('ra-exposition');
        const analEl = document.getElementById('ra-analysis');
        if (expoEl) expoEl.hidden = !exposition;
        if (analEl) analEl.hidden = exposition;
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
    const raPrev = document.querySelector('.ra-present-prev');
    if (raPrev) raPrev.addEventListener('click', () => setRaPresentationSlide(currentRaSlide - 1));
    const raNext = document.querySelector('.ra-present-next');
    if (raNext) raNext.addEventListener('click', () => setRaPresentationSlide(currentRaSlide === raPresentationSlides.length - 1 ? 0 : currentRaSlide + 1));

    // === ROL B: Controles de presentación y modo ===
    const rbPresentationSlides = [...document.querySelectorAll('#rb-exposition .rb-slide')];
    const rbPresentationSteps = [...document.querySelectorAll('#rb-exposition .rb-slide-step')];
    let currentRbSlide = 0;

    const setRbPresentationSlide = index => {
        if (!rbPresentationSlides.length) return;
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
        const countEl = document.getElementById('rb-slide-count');
        if (countEl) countEl.textContent = `${currentRbSlide + 1} / ${rbPresentationSlides.length}`;
        const prevBtn = document.querySelector('#rb-exposition .rb-present-prev') || document.querySelector('.rb-present-prev');
        if (prevBtn) prevBtn.disabled = currentRbSlide === 0;
        const nextBtn = document.querySelector('#rb-exposition .rb-present-next') || document.querySelector('.rb-present-next');
        if (nextBtn) {
            nextBtn.innerHTML = currentRbSlide === rbPresentationSlides.length - 1
                ? 'Volver al inicio <i class="fa-solid fa-rotate-left"></i>'
                : 'Siguiente <i class="fa-solid fa-arrow-right"></i>';
        }
        window.dispatchEvent(new Event('resize'));
    };

    const setRoleBMode = mode => {
        const exposition = mode === 'exposition';
        if (exposition) setRbPresentationSlide(0);
        const expoEl = document.getElementById('rb-exposition');
        const analEl = document.getElementById('rb-analysis');
        if (expoEl) expoEl.hidden = !exposition;
        if (analEl) analEl.hidden = exposition;
        document.querySelectorAll('#rol-b .rb-mode-btn').forEach(button => {
            const active = button.dataset.rbMode === mode;
            button.classList.toggle('active', active);
            button.setAttribute('aria-selected', String(active));
        });
        window.dispatchEvent(new Event('resize'));
    };

    document.querySelectorAll('#rol-b .rb-mode-btn').forEach(button => {
        button.addEventListener('click', () => setRoleBMode(button.dataset.rbMode));
    });
    rbPresentationSteps.forEach((button, index) => button.addEventListener('click', () => setRbPresentationSlide(index)));
    const rbPrev = document.querySelector('#rb-exposition .rb-present-prev') || document.querySelector('.rb-present-prev');
    if (rbPrev) rbPrev.addEventListener('click', () => setRbPresentationSlide(currentRbSlide - 1));
    const rbNext = document.querySelector('#rb-exposition .rb-present-next') || document.querySelector('.rb-present-next');
    if (rbNext) rbNext.addEventListener('click', () => setRbPresentationSlide(currentRbSlide === rbPresentationSlides.length - 1 ? 0 : currentRbSlide + 1));
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
        renderRoleD(data.rolD);
        renderVisibleFull();

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
            if (!document.getElementById('rol-c').classList.contains('active') || document.getElementById('rc-exposition').hidden) return;
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


    // === ROL D: exposición del punto 5 (teleconexiones) ===
    const rdSlides = [...document.querySelectorAll('#rd-exposition .rd-slide')];
    const rdSteps = [...document.querySelectorAll('#rd-exposition .rd-step')];
    let rdCurrent = 0;
    const rdState = { var: 'P_local_mm', field: 'msl', month: 7, showSig: true, profileVar: 'P_local_mm' };
    const setRoleDSlide = index => {
        if (!rdSlides.length) return;
        rdCurrent = Math.max(0, Math.min(rdSlides.length - 1, index));
        rdSlides.forEach((slide, i) => {
            slide.hidden = i !== rdCurrent;
            slide.classList.toggle('active', i === rdCurrent);
        });
        rdSteps.forEach((step, i) => {
            step.classList.toggle('active', i === rdCurrent);
            if (i === rdCurrent) step.setAttribute('aria-current', 'step');
            else step.removeAttribute('aria-current');
        });
        document.getElementById('rd-slide-count').textContent = `${rdCurrent + 1} / ${rdSlides.length}`;
        document.querySelector('#rd-exposition .rd-present-prev').disabled = rdCurrent === 0;
        document.querySelector('#rd-exposition .rd-present-next').innerHTML = rdCurrent === rdSlides.length - 1
            ? 'Volver al inicio <i class="fa-solid fa-rotate-left"></i>'
            : 'Siguiente <i class="fa-solid fa-arrow-right"></i>';
        window.dispatchEvent(new Event('resize'));
    };
    if (rdSlides.length) {
        rdSteps.forEach((step, i) => step.addEventListener('click', () => setRoleDSlide(i)));
        document.querySelector('#rd-exposition .rd-present-prev').addEventListener('click', () => setRoleDSlide(rdCurrent - 1));
        document.querySelector('#rd-exposition .rd-present-next').addEventListener('click', () => setRoleDSlide(rdCurrent === rdSlides.length - 1 ? 0 : rdCurrent + 1));
        document.addEventListener('keydown', event => {
            if (!document.getElementById('rol-d').classList.contains('active') || document.getElementById('rd-exposition').hidden) return;
            if (event.target instanceof HTMLElement && ['INPUT', 'TEXTAREA', 'SELECT'].includes(event.target.tagName)) return;
            if (event.key === 'ArrowRight') setRoleDSlide(rdCurrent + 1);
            if (event.key === 'ArrowLeft') setRoleDSlide(rdCurrent - 1);
        });
        const monthNames = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
        const monthBox = document.querySelector('#rd-exposition .rd-months');
        if (monthBox) {
            monthNames.forEach((name, i) => {
                const b = document.createElement('button');
                b.type = 'button';
                b.dataset.value = String(i + 1);
                b.textContent = name;
                if (i + 1 === rdState.month) b.classList.add('active');
                monthBox.appendChild(b);
            });
        }
        document.querySelectorAll('#rd-exposition .rd-segment').forEach(group => {
            group.addEventListener('click', event => {
                const button = event.target.closest('button');
                if (!button) return;
                const key = group.dataset.rdControl;
                rdState[key] = key === 'month' ? Number(button.dataset.value) : button.dataset.value;
                group.querySelectorAll('button').forEach(b => b.classList.toggle('active', b === button));
                if (key === 'profileVar') renderRoleDProfiles();
                else renderRoleDMap();
            });
        });
        const sigToggle = document.getElementById('rd-show-sig');
        if (sigToggle) sigToggle.addEventListener('change', () => { rdState.showSig = sigToggle.checked; renderRoleDMap(); });
    }

    const rdFieldNames = { sst: 'SST', msl: 'presión al nivel del mar', z500: 'altura geopotencial de 500 hPa' };
    const rdVarNames = { P_local_mm: 'Precipitación de referencia P_L', Caudal_m3s: 'Caudal Q' };
    const rdMonthLong = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];

    const renderRoleDMap = () => {
        const rd = window.dashboardData?.rolD;
        if (!rd || !document.getElementById('chart-rd-mapa')) return;
        const m = rd.maps[`${rdState.var}|${rdState.field}`][rdState.month - 1];
        const z = m.r100.map(row => row.map(v => (v === null ? null : v / 100)));
        const nx = rd.lon.length;
        const sigLon = [], sigLat = [];
        if (rdState.showSig) m.sig.forEach(k => { sigLon.push(rd.lon[k % nx]); sigLat.push(rd.lat[Math.floor(k / nx)]); });
        const coastX = rd.coast.map(p => (p ? p[0] : null));
        const coastY = rd.coast.map(p => (p ? p[1] : null));
        const colors = getThemeColors();
        const isLight = document.documentElement.getAttribute('data-theme') === 'light';
        const base = baseChartLayout();
        Plotly.react('chart-rd-mapa', [
            { type: 'heatmap', x: rd.lon, y: rd.lat, z, zmin: -1, zmax: 1, zmid: 0,
              colorscale: [[0, '#2166ac'], [0.25, '#92c5de'], [0.5, '#f7f7f7'], [0.75, '#f4a582'], [1, '#b2182b']],
              colorbar: { title: { text: 'r', side: 'right' }, thickness: 12, len: 0.9 },
              hovertemplate: 'lon %{x:.0f}° · lat %{y:.0f}°<br>r = %{z:.2f}<extra></extra>' },
            { type: 'scatter', mode: 'lines', x: coastX, y: coastY, line: { color: isLight ? '#3b3b3b' : '#cbd5e1', width: 0.7 },
              hoverinfo: 'skip', showlegend: false },
            { type: 'scatter', mode: 'markers', x: sigLon, y: sigLat, marker: { size: 2.5, color: isLight ? '#111111' : '#e2e8f0' },
              hoverinfo: 'skip', showlegend: false },
            { type: 'scatter', mode: 'markers', x: [rd.basin[0]], y: [rd.basin[1]], marker: { symbol: 'star', size: 13, color: '#ffd400', line: { color: '#111', width: 1 } },
              hovertemplate: 'Cuenca del Maipo<extra></extra>', showlegend: false }
        ], {
            ...base,
            margin: { t: 8, r: 8, l: 36, b: 30 },
            xaxis: { ...base.xaxis, range: [0, 360], tickvals: [60, 120, 180, 240, 300], ticktext: ['60°E', '120°E', '180°', '120°W', '60°W'], showgrid: false, zeroline: false },
            yaxis: { ...base.yaxis, range: [-72, 72], scaleanchor: 'x', scaleratio: 1, tickvals: [-60, -30, 0, 30, 60], ticktext: ['60°S', '30°S', '0°', '30°N', '60°N'], showgrid: false, zeroline: false },
            showlegend: false
        }, plotConfig);
        setText('rd-map-title', `${rdVarNames[rdState.var]} de ${rdMonthLong[rdState.month - 1]} frente a ${rdFieldNames[rdState.field]}`);
        setText('rd-map-n', `n = ${m.n} años`);
        setText('rd-area', `${(100 * m.areaFdr).toFixed(1)} % del área válida`);
        setText('rd-npairs', `${m.n}`);
    };

    const renderRoleDProfiles = () => {
        const rd = window.dashboardData?.rolD;
        if (!rd || !document.getElementById('chart-rd-perfiles')) return;
        const months = ['E', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D'];
        const specs = [['nino34', 'Niño 3.4 (SST)', '#d97853'], ['pnm_sepac', 'PNM Pacífico SE', '#2a78d6'], ['z500_chile', 'Z500 Chile central', '#1baf7a']];
        const traces = specs.map(([key, name, color], k) => {
            const d = rd.profiles[`${rdState.profileVar}|${key}|1980-2020`];
            const sig = d.q.map(q => q !== null && q < 0.05);
            return { x: months.map((_, i) => i + 1 + (k - 1) * 0.16), y: d.r, name, type: 'scatter', mode: 'lines+markers',
                line: { color, width: 2 },
                marker: { size: 9, color: sig.map(s => (s ? color : 'rgba(0,0,0,0)')), line: { color, width: 2 } },
                error_y: { type: 'data', symmetric: false, array: d.hi.map((v, i) => v - d.r[i]), arrayminus: d.r.map((v, i) => v - d.lo[i]), color, thickness: 1.2, width: 0 },
                customdata: d.q, hovertemplate: `${name}<br>mes %{x:.0f}<br>r = %{y:.2f}<br>q FDR = %{customdata:.3f}<extra></extra>` };
        });
        const base = baseChartLayout();
        Plotly.react('chart-rd-perfiles', traces, {
            ...base,
            xaxis: { ...base.xaxis, tickvals: months.map((_, i) => i + 1), ticktext: months },
            yaxis: { ...base.yaxis, title: 'r (mismo mes, ℓ = 0)', range: [-0.9, 0.9], zeroline: true, zerolinewidth: 1.5 },
            legend: { orientation: 'h', y: 1.12, x: 0 },
            margin: { t: 26, r: 12, l: 58, b: 36 }
        }, plotConfig);
    };

    const renderRoleD = rd => {
        if (!rd || !document.getElementById('chart-rd-mapa')) return;
        renderRoleDMap();
        renderRoleDProfiles();
        const months = ['E', 'F', 'M', 'A', 'M', 'J', 'J', 'A', 'S', 'O', 'N', 'D'];
        const x = months.map((_, i) => i + 1);
        const sub = (key, axis, showLegend) => [['1980-1999', '#56a9ba', 'solid'], ['2000-2019', '#d97853', 'solid'], ['1980-2020', '#94a3b8', 'dot']].map(([period, color, dash]) => ({
            x, y: rd.profiles[`${key}|${period}`].r, name: period, type: 'scatter', mode: 'lines+markers', yaxis: axis,
            line: { color, width: 2, dash }, marker: { size: 6 }, showlegend: showLegend,
            hovertemplate: `${period}<br>mes %{x}<br>r = %{y:.2f}<extra></extra>` }));
        const base = baseChartLayout();
        Plotly.react('chart-rd-subperiodos', [...sub('Caudal_m3s|nino34', 'y', true), ...sub('P_local_mm|pnm_sepac', 'y2', false)], {
            ...base,
            grid: { rows: 2, columns: 1, pattern: 'independent', roworder: 'top to bottom' },
            xaxis: { ...base.xaxis, anchor: 'y2', tickvals: x, ticktext: months },
            yaxis: { ...base.yaxis, domain: [0.56, 1], title: 'Q–Niño 3.4', range: [-0.4, 1], zeroline: true },
            yaxis2: { ...base.yaxis, domain: [0, 0.44], title: 'P_L–PNM', range: [-0.9, 0.4], zeroline: true },
            legend: { orientation: 'h', y: 1.1, x: 0 },
            margin: { t: 26, r: 12, l: 62, b: 36 }
        }, plotConfig);
        const rob = rd.robustness;
        const range = o => (o ? `${o.min.toFixed(2)} – ${o.max.toFixed(2)}` : '—');
        setText('rd-rob-tend', range(rob.patron_anomalia_vs_sin_tendencia));
        setText('rd-rob-ext', range(rob.patron_completo_vs_sin_3_extremos));
        setText('rd-rob-imerg', range(rob.patron_PL_vs_IMERG_2000_2020));
        setText('rd-rob-sub', range(rob.patron_1980_1999_vs_2000_2019));

        const mem = rd.memory;
        const mNames = mem.months.map(m => ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'][m - 1]);
        Plotly.react('chart-rd-memoria', [
            { x: mNames, y: mem.rPL, name: 'Lluvia P_L may–ago previa', type: 'bar', marker: { color: '#56a9ba' },
              hovertemplate: 'Q de %{x} vs P_L invernal<br>r = %{y:.2f}<extra></extra>' },
            { x: mNames, y: mem.rNino, name: 'Niño 3.4 may–ago previo', type: 'bar', marker: { color: '#d97853' },
              hovertemplate: 'Q de %{x} vs Niño 3.4 invernal<br>r = %{y:.2f}<extra></extra>' }
        ], {
            ...base,
            barmode: 'group',
            xaxis: { ...base.xaxis, title: 'Mes del caudal (temporada de deshielo)' },
            yaxis: { ...base.yaxis, title: 'r', range: [0, 1] },
            legend: { orientation: 'h', y: 1.12, x: 0 },
            margin: { t: 26, r: 12, l: 52, b: 44 }
        }, plotConfig);
        setText('rd-memory-n', `n ≈ ${Math.min(...mem.n)}–${Math.max(...mem.n)} años`);
        const dep = rd.dependence;
        setText('rd-dep-n34', `${dep.r_PL_nino34[7].toFixed(2)}`);
        setText('rd-dep-n34p', `${dep.r_parcial_PL_nino34_dado_pnm[7].toFixed(2)}`);
        setText('rd-dep-pnm', `${dep.r_PL_pnm[6].toFixed(2)}`);
        setText('rd-dep-pnmp', `${dep.r_parcial_PL_pnm_dado_nino34[6].toFixed(2)}`);
        const coh = rd.coherence.Caudal_m3s;
        setText('rd-coh', `media ${coh.mean.toFixed(2)} · máx. ${coh.max.toFixed(2)} (umbral ${coh.threshold.toFixed(2)})`);
    };

    // === ROLES C y D: vista "Análisis completo" ===
    const fmt = (value, digits = 2) => (value === null || value === undefined || Number.isNaN(Number(value)) ? '—' : Number(value).toFixed(digits));
    const fmtP = value => (value === null || value === undefined ? '—' : (value < 0.001 ? '< 0.001' : Number(value).toFixed(3)));
    const yesNo = value => (value === true || value === 'True' ? 'sí' : value === false || value === 'False' ? 'no' : '—');
    const renderTable = (id, headers, rows, emptyText = 'Sin datos para esta selección.') => {
        const el = document.getElementById(id);
        if (!el) return;
        if (!rows.length) { el.innerHTML = `<p class="rb-small-note">${emptyText}</p>`; return; }
        el.innerHTML = `<table class="rb-data-table"><thead><tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr></thead><tbody>${
            rows.map(r => `<tr>${r.map((c, i) => (i === 0 ? `<th>${c}</th>` : `<td>${c}</td>`)).join('')}</tr>`).join('')}</tbody></table>`;
    };
    const varLabel = { P_local_mm: 'P_L', P_IMERG_mm: 'P_I (IMERG)', Caudal_m3s: 'Q', Temp_C: 'T (ERA5-Land)' };
    const varUnit = { P_local_mm: 'mm/mes', P_IMERG_mm: 'mm/mes', Caudal_m3s: 'm³/s', Temp_C: '°C' };
    const repLabel = { X: 'X original', a: 'a anomalía', z: 'z estandarizada' };
    const repUnit = (v, rep) => (rep === 'z' ? 'z' : varUnit[v]);
    const monthShort = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
    const setSegment = (group, value) => group.querySelectorAll('button').forEach(b => b.classList.toggle('active', b.dataset.value === String(value)));
    const periodTicks = { tickvals: [1 / 480, 1 / 120, 1 / 60, 1 / 24, 1 / 12, 1 / 6, 1 / 3, 1 / 2], ticktext: ['40 a', '10 a', '5 a', '2 a', '12 m', '6 m', '3 m', '2 m'] };

    // ---------- Rol C ----------
    const rcfState = { var: 'P_local_mm', rep: 'a', tramo: 'completo', specVar: 'P_local_mm', tr: 'A', est: 'hann' };

    const renderRcfSeries = full => {
        const key = `${rcfState.var}|${rcfState.rep}`;
        const d = full.series[key];
        const unit = repUnit(rcfState.var, rcfState.rep);
        const base = baseChartLayout();
        Plotly.react('chart-rcf-series', [
            { x: d.date, y: d.hi, type: 'scatter', mode: 'lines', line: { width: 0 }, hoverinfo: 'skip', showlegend: false },
            { x: d.date, y: d.lo, type: 'scatter', mode: 'lines', line: { width: 0 }, fill: 'tonexty', fillcolor: 'rgba(217,120,83,0.18)', name: 'IC 95 % LOESS', hoverinfo: 'skip' },
            { x: d.date, y: d.y, type: 'scatter', mode: 'lines', name: repLabel[rcfState.rep], line: { color: '#56a9ba', width: 1 }, connectgaps: false,
              hovertemplate: `%{x}<br>%{y:.2f} ${unit}<extra></extra>` },
            { x: d.date, y: d.loess, type: 'scatter', mode: 'lines', name: 'LOESS', line: { color: '#d97853', width: 2.5 }, hoverinfo: 'skip' },
            { x: d.date, y: d.ols, type: 'scatter', mode: 'lines', name: 'OLS', line: { color: '#e2a64c', width: 2, dash: 'dash' }, hoverinfo: 'skip' }
        ], {
            ...base,
            yaxis: { ...base.yaxis, title: unit, zeroline: rcfState.rep !== 'X' },
            legend: { orientation: 'h', y: 1.12, x: 0 },
            margin: { t: 26, r: 12, l: 58, b: 36 }
        }, plotConfig);
        setText('rcf-series-title', `${varLabel[rcfState.var]} · ${repLabel[rcfState.rep]}`);
        setText('rcf-series-n', `${d.y.filter(v => v !== null).length} meses válidos`);
        const intervals = full.loessIntervals.filter(r => r.variable === rcfState.var && r.representacion === rcfState.rep);
        renderTable('rcf-loess-table', ['Inicio', 'Fin', 'Sentido', 'Cambio'],
            intervals.map(r => [r.inicio, r.fin, r.sentido, fmt(r.cambio_en_tramo, 2)]),
            'El script 11 tabula los tramos para la representación a; elija «a anomalía».');
    };

    const renderRcfTables = full => {
        const v = rcfState.var;
        renderTable('rcf-methods-table', ['Repr.', 'Método', 'Periodo', 'n', 'Pendiente/déc', 'IC 95 %', 'p', 'p sin corregir', 'Unidad'],
            full.methods.filter(r => r.variable === v).map(r => [r.representacion, r.metodo, r.periodo, r.n,
                fmt(r.pendiente, 3), `[${fmt(r.ic_inf, 3)}, ${fmt(r.ic_sup, 3)}]`, fmtP(r.p), fmtP(r.p_sin_corregir_dependencia), r.unidad]));
        renderTable('rcf-sens-table', ['Prueba', 'Configuración', 'Periodo', 'Años', 'OLS/déc [IC HAC]', 'p HAC', 'Sen/déc [IC]', 'p MK-HR', 'LOESS/déc'],
            full.sensitivity.filter(r => r.variable === v).map(r => [r.prueba, r.configuracion, r.periodo, fmt(r.n_anios, 0),
                `${fmt(r.ols_dec)} [${fmt(r.ols_ic_inf)}, ${fmt(r.ols_ic_sup)}]`, fmtP(r.ols_p_hac),
                `${fmt(r.sen_dec)} [${fmt(r.sen_ic_inf)}, ${fmt(r.sen_ic_sup)}]`, fmtP(r.mk_p_hr),
                r.loess_no_robusto_dec !== null ? `${fmt(r.loess_no_robusto_dec)}${r.loess_rango_robusto ? ` (${r.loess_rango_robusto})` : ''}` : '—']));
        setText('rcf-sens-title', `Sensibilidad de ${varLabel[v]} (años hidrológicos, ${varUnit[v]} por década)`);
    };

    const renderRcfMonthly = full => {
        const d = full.monthly[`${rcfState.var}|${rcfState.rep}`];
        const unit = `${repUnit(rcfState.var, rcfState.rep)} por década`;
        const base = baseChartLayout();
        const trace = (name, y, lo, hi, sig, p, q, color, offset) => ({
            x: monthShort.map((_, i) => i + 1 + offset), y, name, type: 'scatter', mode: 'markers',
            error_y: { type: 'data', symmetric: false, array: hi.map((v, i) => v - y[i]), arrayminus: y.map((v, i) => v - lo[i]), color, thickness: 1.8, width: 0 },
            marker: { size: 9, color: sig.map(s => (s ? color : 'rgba(0,0,0,0)')), line: { color, width: 2 } },
            customdata: y.map((_, i) => [monthShort[i], p[i], q[i], d.n[i]]),
            hovertemplate: `<b>${name} · %{customdata[0]}</b><br>%{y:.3f} ${unit}<br>p = %{customdata[1]:.3f} · q FDR = %{customdata[2]:.3f}<br>n = %{customdata[3]} años<extra></extra>`
        });
        Plotly.react('chart-rcf-monthly', [
            trace('OLS (IC HAC)', d.ols, d.olsLo, d.olsHi, d.sigOls, d.pOls, d.qOls, '#56a9ba', -0.13),
            trace('Theil–Sen (IC Hamed–Rao)', d.sen, d.senLo, d.senHi, d.sigMk, d.pMk, d.qMk, '#d97853', 0.13)
        ], {
            ...base,
            xaxis: { ...base.xaxis, tickvals: monthShort.map((_, i) => i + 1), ticktext: monthShort },
            yaxis: { ...base.yaxis, title: unit, zeroline: true, zerolinewidth: 1.5 },
            legend: { orientation: 'h', y: 1.12, x: 0 },
            margin: { t: 26, r: 12, l: 62, b: 36 }
        }, plotConfig);
        setText('rcf-monthly-title', `${varLabel[rcfState.var]} · ${repLabel[rcfState.rep]} · pendiente por mes calendario`);
        setText('rcf-monthly-n', `${Math.min(...d.n)}–${Math.max(...d.n)} años por mes`);
    };

    const specShapes = () => ([
        { type: 'rect', x0: 1 / 480, x1: 1 / 18, yref: 'paper', y0: 0, y1: 1, fillcolor: 'rgba(148,163,184,0.10)', line: { width: 0 } },
        { type: 'rect', x0: 1 / 14, x1: 1 / 10.5, yref: 'paper', y0: 0, y1: 1, fillcolor: 'rgba(86,169,186,0.12)', line: { width: 0 } },
        { type: 'rect', x0: 1 / 7, x1: 1 / 5.25, yref: 'paper', y0: 0, y1: 1, fillcolor: 'rgba(226,166,76,0.12)', line: { width: 0 } }
    ]);
    const specVarsIn = (full, tramo) => ['P_local_mm', 'P_IMERG_mm', 'Caudal_m3s', 'Temp_C'].filter(v => full.spectra[`${tramo}|${v}|A|hann`]);

    const renderRcfSpectra = full => {
        const available = specVarsIn(full, rcfState.tramo);
        if (!available.includes(rcfState.specVar)) rcfState.specVar = available[0];
        document.querySelectorAll('#rc-analysis [data-rcf-control="specVar"] button').forEach(b => {
            b.disabled = !available.includes(b.dataset.value);
            b.classList.toggle('active', b.dataset.value === rcfState.specVar);
        });
        const key = `${rcfState.tramo}|${rcfState.specVar}|${rcfState.tr}|${rcfState.est}`;
        const d = full.spectra[key];
        const base = baseChartLayout();
        const unit = varUnit[rcfState.specVar];
        const custom = d.f.map(f => 1 / f);
        const traces = [{ x: d.f, y: d.p, name: 'DEP', type: 'scatter', mode: 'lines', line: { color: '#56a9ba', width: 2 }, customdata: custom,
            hovertemplate: `f = %{x:.4f} ciclos/mes<br>periodo %{customdata:.1f} meses<br>DEP = %{y:.3g}<extra></extra>` }];
        if (d.theory) {
            traces.push({ x: d.f, y: d.theory, name: `AR(1) teórico (r₁ = ${d.r1.toFixed(2)})`, type: 'scatter', mode: 'lines', line: { color: '#94a3b8', width: 1.5 }, hoverinfo: 'skip' });
            traces.push({ x: d.f, y: d.point95, name: 'AR(1) 95 % puntual', type: 'scatter', mode: 'lines', line: { color: '#94a3b8', width: 1.2, dash: 'dash' }, hoverinfo: 'skip' });
            traces.push({ x: d.f, y: d.global95, name: 'AR(1) 95 % global', type: 'scatter', mode: 'lines', line: { color: '#d97853', width: 1.4, dash: 'dot' }, hoverinfo: 'skip' });
        }
        Plotly.react('chart-rcf-spec', traces, {
            ...base,
            xaxis: { ...base.xaxis, type: 'log', title: 'Periodo (frecuencia en ciclos/mes, escala log)', ...periodTicks },
            yaxis: { ...base.yaxis, type: 'log', title: `DEP [(${unit})²/(ciclo/mes)]` },
            shapes: specShapes(),
            legend: { orientation: 'h', y: -0.28, x: 0 },
            margin: { t: 18, r: 12, l: 64, b: 86 }
        }, plotConfig);
        const doc = full.specDoc.find(r => r.tramo === rcfState.tramo && r.variable === rcfState.specVar);
        const trName = { C: 'serie centrada (conserva el ciclo anual)', A: 'anomalías respecto a la climatología mensual', AD: 'anomalías sin la tendencia lineal del punto 3' }[rcfState.tr];
        setText('rcf-spec-title', `${varLabel[rcfState.specVar]} · ${trName}`);
        setText('rcf-spec-n', doc ? `N = ${doc.N_meses} · Δf = ${fmt(doc.delta_f_ciclos_mes, 4)}` : '');
        setText('rcf-spec-note', `${doc ? `${doc.inicio} a ${doc.fin}, ${doc.ciclos_anuales_en_tramo} ciclos anuales; meses rellenados: ${doc.meses_rellenados}. ` : ''}`
            + (d.theory ? 'Un pico solo se considera significativo si supera el umbral global, que corrige la búsqueda entre frecuencias.' : 'El fondo AR(1) se calcula para anomalías con Hann y Welch; la serie centrada C contiene el ciclo anual determinista y el boxcar sirve para máxima resolución.'));

        const colors = { P_local_mm: '#56a9ba', P_IMERG_mm: '#8b5cf6', Caudal_m3s: '#d97853', Temp_C: '#79a878' };
        Plotly.react('chart-rcf-spec-all', available.map(v => {
            const s = full.spectra[`${rcfState.tramo}|${v}|${rcfState.tr}|${rcfState.est}`];
            return { x: s.f, y: s.p.map(p => p / s.var), name: varLabel[v], type: 'scatter', mode: 'lines', line: { color: colors[v], width: 2 },
                hovertemplate: `${varLabel[v]}<br>f = %{x:.4f}<br>DEP/var = %{y:.3g}<extra></extra>` };
        }), {
            ...base,
            xaxis: { ...base.xaxis, type: 'log', title: 'Periodo (escala log)', ...periodTicks },
            yaxis: { ...base.yaxis, type: 'log', title: 'DEP / varianza' },
            shapes: specShapes(),
            legend: { orientation: 'h', y: -0.28, x: 0 },
            margin: { t: 18, r: 12, l: 64, b: 86 }
        }, plotConfig);

        // Bandas, picos y tablas del punto 4.
        const bandCols = [['interanual (T > 18 meses)', 'Interanual', '#94a3b8'], ['anual (10.5-14 meses)', 'Anual', '#56a9ba'],
            ['semianual (5.25-7 meses)', 'Semianual', '#e2a64c'], ['resto (intraanual no armónico)', 'Resto', '#d97853']];
        const bandRows = full.bands.filter(r => r.tramo === rcfState.tramo && r.transformacion === rcfState.tr && r.estimador === rcfState.est);
        Plotly.react('chart-rcf-bands', bandCols.map(([col, name, color]) => ({
            x: bandRows.map(r => varLabel[r.variable]), y: bandRows.map(r => r[col]), name, type: 'bar', marker: { color },
            hovertemplate: `${name}: %{y:.1%}<extra></extra>` })), {
            ...base, barmode: 'stack',
            yaxis: { ...base.yaxis, title: 'Fracción de la varianza', tickformat: '.0%', range: [0, 1] },
            legend: { orientation: 'h', y: 1.14, x: 0 },
            margin: { t: 26, r: 12, l: 58, b: 36 }
        }, plotConfig);
        setText('rcf-bands-sub', `Tramo ${rcfState.tramo} · serie ${rcfState.tr} · estimador ${rcfState.est}`);
        const peaks = full.peaks.filter(r => r.tramo === rcfState.tramo && r.variable === rcfState.specVar && r.transformacion === rcfState.tr && r.estimador === rcfState.est);
        renderTable('rcf-peaks-table', ['Periodo (meses)', 'Periodo (años)', 'Rango de periodos del bin', 'Ciclos en el registro', 'Fracción de varianza del bin', '> AR(1) 95 % puntual', '> AR(1) 95 % global'],
            peaks.map(r => [fmt(r.periodo_meses, 1), fmt(r.periodo_anios, 2), `${fmt(r.periodo_min_meses, 1)}–${fmt(r.periodo_max_meses, 1)}`, fmt(r.ciclos_observados, 1),
                fmt(r.fraccion_varianza_bin, 3), yesNo(r.supera_AR1_95_puntual), yesNo(r.supera_AR1_95_global)]));
        setText('rcf-peaks-title', `Picos principales · ${varLabel[rcfState.specVar]} · ${rcfState.tr} · ${rcfState.est}`);
    };

    const renderRcfStaticTables = full => {
        renderTable('rcf-periods-table', ['Variable', 'Fuente', 'Inicio', 'Fin', 'Meses', 'Válidos', 'Faltantes internos', 'Válidos en periodo común'],
            full.periods.map(r => [varLabel[r.variable], r.fuente, r.inicio_registro, r.fin_registro, r.meses_en_registro, r.meses_validos_registro, r.faltantes_internos, `${r.meses_validos_periodo_comun} / ${r.meses_periodo_comun}`]));
        renderTable('rcf-fdr-table', ['Variable', 'Prueba', 'p', 'q FDR', 'Significativo'],
            full.fdrGlobal.map(r => [varLabel[r.variable], r.prueba, fmtP(r.p), fmtP(r.q_fdr), yesNo(r.signif_fdr)]));
        renderTable('rcf-step-table', ['Variable', 'Año Pettitt', 'K', 'p Pettitt', 'Media antes', 'Media después', 'AIC constante', 'AIC tendencia', 'AIC escalón', 'AIC escalón + tendencia', 'Menor AIC', 'ΔAIC tend. − esc.'],
            full.step.map(r => [varLabel[r.variable], r.anio_cambio_pettitt, fmt(r.K_pettitt, 0), fmtP(r.p_pettitt), fmt(r.media_antes), fmt(r.media_despues),
                fmt(r['AIC_nivel constante'], 1), fmt(r['AIC_tendencia lineal'], 1), fmt(r['AIC_escalón (Pettitt)'], 1), fmt(r['AIC_escalón + tendencia'], 1), r.modelo_menor_AIC, fmt(r.delta_AIC_tendencia_menos_escalon)]));
        renderTable('rcf-persist-table', ['Tramo', 'Variable', 'Serie', 'N', 'r₁', 'Pendiente log–log', 'Periodo interanual dominante (años)'],
            full.persistence.map(r => [r.tramo, varLabel[r.variable], r.transformacion, r.N, fmt(r.r1), fmt(r['pendiente_espectral_loglog_f<1/12']), fmt(r.periodo_interanual_dominante_anios, 1)]));
        renderTable('rcf-stab-table', ['Variable', 'Configuración', 'N', 'Periodo interanual dominante (años)', 'Interanual', 'Anual', 'Semianual', 'Resto'],
            full.stability.map(r => [varLabel[r.variable], r.configuracion, r.N, fmt(r.periodo_interanual_dominante_anios, 1),
                fmt(r['frac_interanual (T > 18 meses)'], 3), fmt(r['frac_anual (10.5-14 meses)'], 3), fmt(r['frac_semianual (5.25-7 meses)'], 3), fmt(r['frac_resto (intraanual no armónico)'], 3)]));
        renderTable('rcf-doc-table', ['Tramo', 'Variable', 'Inicio', 'Fin', 'N', 'Δf (ciclos/mes)', 'Nyquist', 'Meses rellenados', 'Tendencia retirada (AD, por déc.)', 'Fracción ciclo anual'],
            full.specDoc.map(r => [r.tramo, varLabel[r.variable], r.inicio, r.fin, r.N_meses, fmt(r.delta_f_ciclos_mes, 5), fmt(r.f_nyquist_ciclos_mes, 1), r.meses_rellenados,
                fmt(r.tendencia_retirada_AD_por_decada, 3), fmt(r.fraccion_varianza_ciclo_anual, 3)]));
    };

    const renderRoleCFull = () => {
        const full = window.dashboardData?.rolC?.full;
        if (!full || !document.getElementById('chart-rcf-series')) return;
        renderRcfSeries(full);
        renderRcfTables(full);
        renderRcfMonthly(full);
        renderRcfSpectra(full);
        renderRcfStaticTables(full);
    };

    document.querySelectorAll('#rc-analysis .rd-segment').forEach(group => {
        group.addEventListener('click', event => {
            const button = event.target.closest('button');
            if (!button || button.disabled) return;
            rcfState[group.dataset.rcfControl] = button.dataset.value;
            setSegment(group, button.dataset.value);
            renderRoleCFull();
        });
    });

    // ---------- Rol D ----------
    const rdfState = { var: 'P_local_mm', field: 'msl', lag: 0, showSig: true, profVar: 'P_local_mm', period: '1980-2020', lagVar: 'Caudal_m3s' };
    const rdfIndexOfField = { sst: 'nino34', msl: 'pnm_sepac', z500: 'z500_chile' };
    const rdfFieldLabel = { sst: 'SST', msl: 'PNM', z500: 'Z500' };

    const renderRdfMaps = rd => {
        const key = `${rdfState.var}|${rdfState.field}${rdfState.lag ? `|lag${rdfState.lag}` : ''}`;
        const maps = rd.maps[key];
        const isLight = document.documentElement.getAttribute('data-theme') === 'light';
        const coastX = rd.coast.map(p => (p ? p[0] : null));
        const coastY = rd.coast.map(p => (p ? p[1] : null));
        const nx = rd.lon.length;
        const cols = 3, rows = 4, traces = [], annotations = [];
        const base = baseChartLayout();
        const layout = { ...base, margin: { t: 22, r: 70, l: 8, b: 8 }, showlegend: false };
        maps.forEach((m, i) => {
            const k = i + 1, ax = k === 1 ? '' : String(k);
            const col = i % cols, row = Math.floor(i / cols);
            layout[`xaxis${ax}`] = { domain: [col / cols + 0.004, (col + 1) / cols - 0.004], range: [0, 360], showticklabels: false, showgrid: false, zeroline: false, anchor: `y${ax}` };
            layout[`yaxis${ax}`] = { domain: [1 - (row + 1) / rows + 0.006, 1 - row / rows - 0.03], range: [-72, 72], showticklabels: false, showgrid: false, zeroline: false, anchor: `x${ax}` };
            traces.push({ type: 'heatmap', x: rd.lon, y: rd.lat, z: m.r100.map(r => r.map(v => (v === null ? null : v / 100))), zmin: -1, zmax: 1, zmid: 0,
                colorscale: [[0, '#2166ac'], [0.25, '#92c5de'], [0.5, '#f7f7f7'], [0.75, '#f4a582'], [1, '#b2182b']],
                showscale: i === 0, colorbar: { title: { text: 'r', side: 'right' }, thickness: 12, len: 0.9, x: 1.01 },
                xaxis: `x${ax}`, yaxis: `y${ax}`, hovertemplate: `${monthShort[i]} · lon %{x:.0f}° · lat %{y:.0f}°<br>r = %{z:.2f}<extra></extra>` });
            traces.push({ type: 'scatter', mode: 'lines', x: coastX, y: coastY, xaxis: `x${ax}`, yaxis: `y${ax}`, line: { color: isLight ? '#3b3b3b' : '#cbd5e1', width: 0.5 }, hoverinfo: 'skip' });
            if (rdfState.showSig) {
                const sx = [], sy = [];
                m.sig.forEach(c => { sx.push(rd.lon[c % nx]); sy.push(rd.lat[Math.floor(c / nx)]); });
                traces.push({ type: 'scatter', mode: 'markers', x: sx, y: sy, xaxis: `x${ax}`, yaxis: `y${ax}`, marker: { size: 1.8, color: isLight ? '#111' : '#e2e8f0' }, hoverinfo: 'skip' });
            }
            traces.push({ type: 'scatter', mode: 'markers', x: [rd.basin[0]], y: [rd.basin[1]], xaxis: `x${ax}`, yaxis: `y${ax}`, marker: { symbol: 'star', size: 8, color: '#ffd400', line: { color: '#111', width: 0.8 } }, hoverinfo: 'skip' });
            annotations.push({ text: `<b>${monthShort[i]}</b> · n = ${m.n} · área FDR ${(100 * m.areaFdr).toFixed(1)} %`, xref: 'paper', yref: 'paper',
                x: col / cols + 0.006, y: 1 - row / rows - 0.004, xanchor: 'left', yanchor: 'top', showarrow: false, font: { size: 10 } });
        });
        layout.annotations = annotations;
        Plotly.react('chart-rdf-maps', traces, layout, plotConfig);
        const lagText = rdfState.lag ? `ℓ = ${rdfState.lag} meses (el campo antecede)` : 'ℓ = 0';
        setText('rdf-maps-title', `${rdVarNames[rdfState.var] || 'Precipitación IMERG P_I'} frente a ${rdFieldNames[rdfState.field]} · ${lagText}`);
        setText('rdf-maps-n', `n = ${Math.min(...maps.map(m => m.n))}–${Math.max(...maps.map(m => m.n))} años`);

        const base2 = baseChartLayout();
        Plotly.react('chart-rdf-area', [{ x: monthShort, y: maps.map(m => m.areaFdr), type: 'bar', marker: { color: '#56a9ba' },
            hovertemplate: '%{x}: %{y:.1%} del área válida<extra></extra>' }], {
            ...base2, yaxis: { ...base2.yaxis, title: 'Área significativa (FDR)', tickformat: '.0%', rangemode: 'tozero' }, margin: { t: 14, r: 12, l: 62, b: 36 }
        }, plotConfig);
        const summary = rd.tables.tabla_5_2_resumen_mapas.filter(r => r.variable_cuenca === rdfState.var && r.campo === rdfState.field && r.rezago_meses === rdfState.lag && r.metodo === 'pearson');
        const box = rdfIndexOfField[rdfState.field];
        renderTable('rdf-summary-table', ['Mes', 'n', 'máx |r| Pacífico', 'Lat', 'Lon', '|r| > 0.4', 'Área FDR', `r medio ${rdfFieldLabel[rdfState.field] === 'SST' ? 'Niño 3.4' : box === 'pnm_sepac' ? 'PNM SE' : 'Z500 Chile'}`],
            summary.map(r => [monthShort[r.mes - 1], r.n_pares, fmt(r.r_max_abs_pacifico), fmt(r.lat_max, 0), `${fmt(r.lon_max_0_360 > 180 ? 360 - r.lon_max_0_360 : r.lon_max_0_360, 0)}°${r.lon_max_0_360 > 180 ? 'W' : 'E'}`,
                `${fmt(100 * r['fraccion_area_abs_r_mayor_0.4'], 1)} %`, `${fmt(100 * r.fraccion_area_signif_fdr, 1)} %`, fmt(r[`r_media_${box}`])]),
            'El script 17 tabula P_L y Q con ℓ = 0 y Q–SST con ℓ = 6; para IMERG, ver la robustez (sección 05).');

        const rob = rd.tables.tabla_5_3_robustez.filter(r => r.variable_cuenca === rdfState.var && r.campo === rdfState.field);
        renderTable('rdf-rob-table', ['Mes', 'n', 'Área FDR', 'Área FDR sin tendencia', 'Patrón vs sin tendencia', 'Patrón 1980–99 vs 2000–19', 'Patrón sin 3 extremos', 'Años retirados', 'Patrón P_L vs IMERG', `r índice (anom. / sin tend.)`],
            rob.map(r => [monthShort[r.mes - 1], r.n_pares, `${fmt(100 * r.area_signif_fdr, 1)} %`, `${fmt(100 * r.area_signif_fdr_sin_tendencia, 1)} %`, fmt(r.patron_anomalia_vs_sin_tendencia),
                fmt(r.patron_1980_1999_vs_2000_2019), fmt(r.patron_completo_vs_sin_3_extremos), r.anios_extremos_retirados, fmt(r.patron_PL_vs_IMERG_2000_2020),
                `${fmt(r[`r_${box}_anomalia`])} / ${fmt(r[`r_${box}_sin_tendencia`])}`]),
            'La robustez se calculó para P_L y Q; IMERG se usa como contraste dentro de esta tabla (columna «Patrón P_L vs IMERG»).');
        setText('rdf-rob-title', `Robustez · ${varLabel[rdfState.var]} frente a ${rdfFieldLabel[rdfState.field]}`);
        const neff = rd.tables.tabla_5_3_tamano_muestra.filter(r => r.variable_cuenca === rdfState.var && r.campo === rdfState.field);
        renderTable('rdf-neff-table', ['Mes', 'n pares', 'Celdas válidas', 'n_eff mediana', 'n_eff p10', 'n_eff mín.'],
            neff.map(r => [monthShort[r.mes - 1], r.n_pares, r.celdas_validas, fmt(r.n_eff_mediana, 1), fmt(r.n_eff_p10, 1), fmt(r.n_eff_min, 1)]),
            'Tabulado para P_L y Q.');
    };

    const renderRdfProfiles = rd => {
        const specs = [['nino34', 'Niño 3.4 (SST)', '#d97853'], ['pnm_sepac', 'PNM Pacífico SE', '#2a78d6'], ['z500_chile', 'Z500 Chile central', '#1baf7a']];
        const base = baseChartLayout();
        Plotly.react('chart-rdf-prof', specs.map(([key, name, color], k) => {
            const d = rd.profiles[`${rdfState.profVar}|${key}|${rdfState.period}`];
            const sig = d.q.map(q => q !== null && q < 0.05);
            return { x: monthShort.map((_, i) => i + 1 + (k - 1) * 0.15), y: d.r, name, type: 'scatter', mode: 'lines+markers', line: { color, width: 2 },
                marker: { size: 9, color: sig.map(s => (s ? color : 'rgba(0,0,0,0)')), line: { color, width: 2 } },
                error_y: { type: 'data', symmetric: false, array: d.hi.map((v, i) => v - d.r[i]), arrayminus: d.r.map((v, i) => v - d.lo[i]), color, thickness: 1.2, width: 0 },
                hovertemplate: `${name}<br>mes %{x:.0f}<br>r = %{y:.2f}<extra></extra>` };
        }), {
            ...base,
            xaxis: { ...base.xaxis, tickvals: monthShort.map((_, i) => i + 1), ticktext: monthShort },
            yaxis: { ...base.yaxis, title: 'r (mismo mes, ℓ = 0)', range: [-1, 1], zeroline: true, zerolinewidth: 1.5 },
            legend: { orientation: 'h', y: 1.12, x: 0 }, margin: { t: 26, r: 12, l: 58, b: 36 }
        }, plotConfig);
        setText('rdf-prof-title', `${varLabel[rdfState.profVar]} · ${rdfState.period}`);
    };

    const renderRdfLags = rd => {
        const lagsAxis = Array.from({ length: 13 }, (_, i) => i);
        const z = lagsAxis.map(l => monthShort.map((_, m) => rd.lags[`${rdfState.lagVar}|${m + 1}`]?.r[l] ?? null));
        const p = lagsAxis.map(l => monthShort.map((_, m) => rd.lags[`${rdfState.lagVar}|${m + 1}`]?.p[l] ?? null));
        const sx = [], sy = [];
        p.forEach((row, l) => row.forEach((v, m) => { if (v !== null && v < 0.05) { sx.push(monthShort[m]); sy.push(l); } }));
        const base = baseChartLayout();
        Plotly.react('chart-rdf-lags', [
            { type: 'heatmap', x: monthShort, y: lagsAxis, z, zmin: -0.8, zmax: 0.8, zmid: 0,
              colorscale: [[0, '#2166ac'], [0.25, '#92c5de'], [0.5, '#f7f7f7'], [0.75, '#f4a582'], [1, '#b2182b']],
              colorbar: { title: { text: 'r', side: 'right' }, thickness: 12 }, hovertemplate: 'mes %{x} · ℓ = %{y}<br>r = %{z:.2f}<extra></extra>' },
            { type: 'scatter', mode: 'markers', x: sx, y: sy, marker: { size: 5, color: '#111' }, hoverinfo: 'skip', showlegend: false }
        ], {
            ...base,
            xaxis: { ...base.xaxis, title: 'Mes de la cuenca (j)' },
            yaxis: { ...base.yaxis, title: 'Rezago ℓ (meses)', dtick: 2 },
            margin: { t: 14, r: 12, l: 58, b: 44 }
        }, plotConfig);
        setText('rdf-lag-title', `r(${varLabel[rdfState.lagVar]} en el mes j, Niño 3.4 en j − ℓ)`);
    };

    const renderRdfStatic = rd => {
        const t = rd.tables;
        renderTable('rdf-memory-table', ['Mes de Q', 'r con P_L may–ago', 'p', 'r con Niño 3.4 may–ago', 'p', 'n'],
            t.tabla_5_4_memoria_nival.map(r => [monthShort[r.mes_Q - 1], fmt(r.r_Q_vs_PL_may_ago), fmtP(r.p_PL), fmt(r.r_Q_vs_Nino34_may_ago), fmtP(r.p_Nino), r.n]));
        renderTable('rdf-spear-table', ['Cuenca', 'Mes', 'Mediana |r_P − r_S|', 'p95 |r_P − r_S|', 'Correlación de patrón'],
            t.tabla_5_2_pearson_vs_spearman.map(r => [varLabel[r.variable_cuenca], monthShort[r.mes - 1], fmt(r.mediana_abs_dif, 3), fmt(r.p95_abs_dif, 3), fmt(r.corr_patron_pacifico)]));
        renderTable('rdf-coh-table', ['Cuenca', 'Coherencia media 2–7 a', 'Máxima', 'Periodo del máximo (años)', 'Umbral 95 % aprox.', 'Segmentos'],
            t.tabla_5_4_coherencia.map(r => [varLabel[r.variable_cuenca], fmt(r.coherencia_media_2_7_anios), fmt(r.coherencia_max_2_7_anios), fmt(r.periodo_max_anios, 1), fmt(r.umbral_95_aprox), r.segmentos]));
        renderTable('rdf-meta-table', ['Campo', 'Producto', 'Variable', 'Nivel', 'Unidad usada', 'Resolución usada', 'Periodo', 'Máscara'],
            t.tabla_5_1_metadatos_campos.map(r => [r.campo.toUpperCase(), r.producto, r.variable, r.nivel, r.unidad_usada, r.resolucion_usada, r.periodo, r.mascara]));
        const dep = rd.dependence;
        const base = baseChartLayout();
        const line = (y, name, color, dash) => ({ x: monthShort, y, name, type: 'scatter', mode: 'lines+markers', line: { color, width: 2, dash }, marker: { size: 6 } });
        Plotly.react('chart-rdf-dep', [
            line(dep.r_PL_nino34, 'r(P_L, Niño 3.4)', '#d97853', 'solid'),
            line(dep.r_parcial_PL_nino34_dado_pnm, 'parcial | PNM', '#d97853', 'dot'),
            line(dep.r_PL_pnm, 'r(P_L, PNM)', '#2a78d6', 'solid'),
            line(dep.r_parcial_PL_pnm_dado_nino34, 'parcial | Niño 3.4', '#2a78d6', 'dot'),
            line(dep.r_nino34_pnm, 'r(Niño 3.4, PNM)', '#94a3b8', 'dash')
        ], {
            ...base, yaxis: { ...base.yaxis, title: 'r', range: [-1, 1], zeroline: true },
            legend: { orientation: 'h', y: -0.2, x: 0 }, margin: { t: 14, r: 12, l: 52, b: 70 }
        }, plotConfig);
    };

    const renderRoleDFull = () => {
        const rd = window.dashboardData?.rolD;
        if (!rd || !rd.tables || !document.getElementById('chart-rdf-maps')) return;
        renderRdfMaps(rd);
        renderRdfProfiles(rd);
        renderRdfLags(rd);
        renderRdfStatic(rd);
    };

    document.querySelectorAll('#rd-analysis .rd-segment').forEach(group => {
        group.addEventListener('click', event => {
            const button = event.target.closest('button');
            if (!button) return;
            const key = group.dataset.rdfControl;
            rdfState[key] = key === 'lag' ? Number(button.dataset.value) : button.dataset.value;
            // ℓ = 6 solo existe para Q–SST; cualquier otra combinación vuelve a ℓ = 0.
            if (key === 'lag' && rdfState.lag === 6) { rdfState.var = 'Caudal_m3s'; rdfState.field = 'sst'; }
            if ((key === 'var' || key === 'field') && !(rdfState.var === 'Caudal_m3s' && rdfState.field === 'sst')) rdfState.lag = 0;
            document.querySelectorAll('#rd-analysis .rd-segment').forEach(g => setSegment(g, rdfState[g.dataset.rdfControl]));
            if (key === 'profVar' || key === 'period') renderRdfProfiles(window.dashboardData.rolD);
            else if (key === 'lagVar') renderRdfLags(window.dashboardData.rolD);
            else renderRdfMaps(window.dashboardData.rolD);
        });
    });
    const rdfSig = document.getElementById('rdf-show-sig');
    if (rdfSig) rdfSig.addEventListener('change', () => { rdfState.showSig = rdfSig.checked; renderRdfMaps(window.dashboardData.rolD); });

    // ---------- Interruptores de modo de C y D ----------
    const makeModeSwitch = (role, renderFull, resetSlide) => {
        const setMode = mode => {
            const exposition = mode === 'exposition';
            document.getElementById(`${role}-exposition`).hidden = !exposition;
            document.getElementById(`${role}-analysis`).hidden = exposition;
            document.querySelectorAll(`.${role}-mode-btn`).forEach(button => {
                const active = button.dataset[`${role}Mode`] === mode;
                button.classList.toggle('active', active);
                button.setAttribute('aria-selected', String(active));
            });
            if (exposition) resetSlide(0);
            else renderFull();
            window.dispatchEvent(new Event('resize'));
        };
        document.querySelectorAll(`.${role}-mode-btn`).forEach(button => button.addEventListener('click', () => setMode(button.dataset[`${role}Mode`])));
    };
    if (document.getElementById('rc-analysis')) makeModeSwitch('rc', renderRoleCFull, setRoleCSlide);
    if (document.getElementById('rd-analysis')) makeModeSwitch('rd', renderRoleDFull, setRoleDSlide);
    const renderVisibleFull = () => {
        if (document.getElementById('rc-analysis') && !document.getElementById('rc-analysis').hidden) renderRoleCFull();
        if (document.getElementById('rd-analysis') && !document.getElementById('rd-analysis').hidden) renderRoleDFull();
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
