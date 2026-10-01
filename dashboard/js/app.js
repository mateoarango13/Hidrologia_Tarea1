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

    const presentationSlides = [...document.querySelectorAll('#rb-exposition .rb-slide')];
    const presentationSteps = [...document.querySelectorAll('.rb-slide-step')];
    let currentPresentationSlide = 0;

    const setPresentationSlide = index => {
        currentPresentationSlide = Math.max(0, Math.min(presentationSlides.length - 1, index));
        presentationSlides.forEach((slide, slideIndex) => {
            const active = slideIndex === currentPresentationSlide;
            slide.hidden = !active;
            slide.classList.toggle('active', active);
        });
        presentationSteps.forEach((step, stepIndex) => {
            const active = stepIndex === currentPresentationSlide;
            step.classList.toggle('active', active);
            if (active) step.setAttribute('aria-current', 'step');
            else step.removeAttribute('aria-current');
        });
        document.getElementById('rb-slide-count').textContent = `${currentPresentationSlide + 1} / ${presentationSlides.length}`;
        document.querySelector('.rb-present-prev').disabled = currentPresentationSlide === 0;
        document.querySelector('.rb-present-next').innerHTML = currentPresentationSlide === presentationSlides.length - 1
            ? 'Volver al inicio <i class="fa-solid fa-rotate-left"></i>'
            : 'Siguiente <i class="fa-solid fa-arrow-right"></i>';
        window.dispatchEvent(new Event('resize'));
    };

    const setRoleBMode = mode => {
        const exposition = mode === 'exposition';
        if (exposition) setPresentationSlide(0);
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
    presentationSteps.forEach((button, index) => button.addEventListener('click', () => setPresentationSlide(index)));
    document.querySelector('.rb-present-prev').addEventListener('click', () => setPresentationSlide(currentPresentationSlide - 1));
    document.querySelector('.rb-present-next').addEventListener('click', () => setPresentationSlide(currentPresentationSlide === presentationSlides.length - 1 ? 0 : currentPresentationSlide + 1));
    document.addEventListener('keydown', event => {
        const expositionActive = document.getElementById('rol-b').classList.contains('active') && !document.getElementById('rb-exposition').hidden;
        if (!expositionActive || (event.target instanceof HTMLElement && ['INPUT', 'TEXTAREA', 'SELECT'].includes(event.target.tagName))) return;
        if (event.key === 'ArrowRight') setPresentationSlide(currentPresentationSlide + 1);
        if (event.key === 'ArrowLeft') setPresentationSlide(currentPresentationSlide - 1);
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
