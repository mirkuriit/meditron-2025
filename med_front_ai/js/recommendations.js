const Recommendations = {
    showLoading() {
        const recommendationsDiv = document.getElementById('recommendations');
        recommendationsDiv.innerHTML = '<div class="loading">Анализ данных... Пожалуйста, подождите.</div>';
        this.toggleSaveButton(true);
    },

    clear() {
        const recommendationsDiv = document.getElementById('recommendations');
        recommendationsDiv.innerHTML = '<p class="placeholder">Здесь будут отображаться рекомендации после анализа данных</p>';
        this.toggleSaveButton(true);
    },

    displayBackendResult(result) {
        const recommendationsDiv = document.getElementById('recommendations');
        const hasSurvival = !!result?.survival;
        const hasTumorData = !!result?.tumor_dynamic;

        console.log('🎯 Отображение результатов:', { hasSurvival, hasTumorData, tumorData: result?.tumor_dynamic });

        if (!hasSurvival && !hasTumorData) {
            recommendationsDiv.innerHTML = '<p class="placeholder">От бэкенда не получены данные для отображения</p>';
            this.toggleSaveButton(true);
            return;
        }

        let html = '';

        if (hasSurvival) {
            html += this.renderSurvivalSection(result.survival);
        }

        // Проверяем наличие данных для графика более гибко
        const tumorData = result?.tumor_dynamic;
        // Проверяем наличие массива t и что ok не равен false явно
        const hasTumorChartData = tumorData && 
            Array.isArray(tumorData.t) && 
            tumorData.t.length > 0 &&
            (tumorData.ok === undefined || tumorData.ok === true || tumorData.ok !== false);

        console.log('📈 Проверка данных для графика:', {
            hasTumorData: !!tumorData,
            hasOk: tumorData?.ok,
            hasT: Array.isArray(tumorData?.t),
            tLength: tumorData?.t?.length,
            hasTumorChartData
        });

        if (hasTumorChartData) {
            html += this.generateChart();
            html += this.renderDosesRecommendations(tumorData.doses);
            recommendationsDiv.innerHTML = html;
            // Увеличиваем задержку, чтобы убедиться, что DOM обновлен
            setTimeout(() => {
                console.log('🎨 Рендеринг графика с данными:', tumorData);
                this.renderChart(tumorData);
            }, 200);
        } else {
            if (tumorData) {
                console.warn('⚠️ Данные tumor_dynamic есть, но не подходят для графика:', tumorData);
                html += this.renderDataSection('📉 Динамика опухоли', tumorData);
            }
            recommendationsDiv.innerHTML = html;
        }

        this.toggleSaveButton(false);
    },

    renderSurvivalSection(survivalData) {
        if (!survivalData) return '';
        
        const month = survivalData.month || survivalData.survival_month;
        if (!month) return '';

        return `
            <div class="recommendation-item">
                <h3>📈 Данные о выживаемости</h3>
                <p><strong>Прогнозируемая выживаемость:</strong> ${month} месяцев</p>
            </div>
        `;
    },

    renderDosesRecommendations(doses) {
        if (!doses || typeof doses !== 'object' || Object.keys(doses).length === 0) {
            return '';
        }

        let html = `
            <div class="recommendation-item">
                <h3>💊 Рекомендуемые изменения дозировок препаратов</h3>
                <div class="doses-table">
        `;

        for (const [drugName, doseInfo] of Object.entries(doses)) {
            if (doseInfo && typeof doseInfo === 'object') {
                const baseDose = doseInfo.base_dose || 0;
                const optimizedDose = doseInfo.optimized_dose || 0;
                const change = optimizedDose - baseDose;
                const changePercent = baseDose !== 0 ? ((change / baseDose) * 100).toFixed(1) : 0;
                const changeSign = change > 0 ? '+' : '';
                const changeClass = change > 0 ? 'increase' : change < 0 ? 'decrease' : 'no-change';

                html += `
                    <div class="dose-item">
                        <div class="dose-drug-name">${this.escapeHtml(drugName)}</div>
                        <div class="dose-values">
                            <div class="dose-value">
                                <span class="dose-label">Базовая доза:</span>
                                <span class="dose-number">${baseDose.toFixed(2)}</span>
                            </div>
                            <div class="dose-value">
                                <span class="dose-label">Оптимизированная доза:</span>
                                <span class="dose-number optimized">${optimizedDose.toFixed(2)}</span>
                            </div>
                            <div class="dose-change ${changeClass}">
                                <span class="dose-label">Изменение:</span>
                                <span class="dose-number">${changeSign}${change.toFixed(2)} (${changeSign}${changePercent}%)</span>
                            </div>
                        </div>
                    </div>
                `;
            }
        }

        html += `
                </div>
            </div>
        `;

        return html;
    },

    toggleSaveButton(disabled) {
        const btn = document.getElementById('saveTxtBtn');
        if (btn) {
            btn.disabled = disabled;
        }
    },

    renderDataSection(title, data) {
        return `
            <div class="recommendation-item">
                <h3>${title}</h3>
                ${this.renderValue(data)}
            </div>
        `;
    },

    renderValue(value) {
        if (Array.isArray(value)) {
            if (!value.length) {
                return '<p>—</p>';
            }

            return `<ul class="data-list">
                ${value.map(entry => `<li>${this.renderValue(entry)}</li>`).join('')}
            </ul>`;
        }

        if (value && typeof value === 'object') {
            return `<ul class="data-list">
                ${Object.entries(value).map(([key, val]) => `
                    <li>
                        <strong>${this.escapeHtml(this.formatKey(key))}:</strong>
                        ${this.renderValue(val)}
                    </li>
                `).join('')}
            </ul>`;
        }

        if (value === null || value === undefined || value === '') {
            return '<span>—</span>';
        }

        return `<span>${this.escapeHtml(String(value))}</span>`;
    },

    formatKey(key) {
        return key.replace(/_/g, ' ');
    },

    escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        };
        return text.replace(/[&<>"']/g, (char) => map[char]);
    },

    extractSeries(data, candidates) {
        for (const key of candidates) {
            if (Array.isArray(data?.[key])) {
                return data[key];
            }
        }
        return [];
    },

    generateChart() {
        return `
            <div class="recommendation-item">
                <h3>📊 График динамики опухоли</h3>
                <div class="chart-container">
                    <canvas id="tumorSizeChart" width="600" height="400"></canvas>
                </div>
                <div class="chart-legend" id="chartLegend"></div>
            </div>
        `;
    },

    renderChart(tumorData) {
        console.log('🎨 Начало рендеринга графика, данные:', tumorData);
        
        const canvas = document.getElementById('tumorSizeChart');
        if (!canvas) {
            console.error('❌ Canvas элемент не найден!');
            return;
        }
        
        console.log('✅ Canvas найден, размеры:', canvas.width, canvas.height);
        
        const t = tumorData.t || [];
        const V = tumorData.V || [];
        const Ns = tumorData.Ns || [];
        const Nr = tumorData.Nr || [];
        const N = tumorData.N || [];

        console.log('📊 Данные для графика:', {
            tLength: t.length,
            VLength: V.length,
            NsLength: Ns.length,
            NrLength: Nr.length,
            NLength: N.length
        });

        if (!t.length || (!V.length && !Ns.length && !Nr.length && !N.length)) {
            console.warn('⚠️ Недостаточно данных для построения графика');
            return;
        }
        
        const ctx = canvas.getContext('2d');
        if (!ctx) {
            console.error('❌ Не удалось получить контекст canvas');
            return;
        }
        
        // Устанавливаем правильные размеры canvas
        const container = canvas.parentElement;
        let canvasWidth = 600;
        let canvasHeight = 400;
        
        if (container) {
            canvasWidth = container.clientWidth || 600;
            canvasHeight = 400;
        }
        
        // Устанавливаем размеры canvas
        canvas.width = canvasWidth;
        canvas.height = canvasHeight;
        canvas.style.width = canvasWidth + 'px';
        canvas.style.height = canvasHeight + 'px';
        
        console.log('📐 Размеры canvas:', canvas.width, canvas.height);
        
        // Очистка canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Настройки графика
        const padding = { top: 50, right: 50, bottom: 60, left: 70 };
        const chartWidth = canvas.width - padding.left - padding.right;
        const chartHeight = canvas.height - padding.top - padding.bottom;
        
        console.log('📐 Размеры области графика:', chartWidth, chartHeight);
        
        // Находим максимальные значения для масштабирования
        const allValues = [...V, ...Ns, ...Nr, ...N].filter(v => typeof v === 'number' && !isNaN(v));
        const validT = t.filter(v => typeof v === 'number' && !isNaN(v));
        
        if (validT.length === 0 || allValues.length === 0) {
            console.warn('⚠️ Нет валидных данных для построения графика');
            return;
        }
        
        const maxX = Math.max(...validT);
        const maxY = allValues.length > 0 ? Math.max(...allValues) : 1;
        const minY = allValues.length > 0 ? Math.min(...allValues) : 0;
        const yRange = maxY - minY || 1;
        
        console.log('📊 Диапазоны данных:', { maxX, maxY, minY, yRange });
        
        const scaleX = chartWidth / (maxX || 1);
        const scaleY = chartHeight / yRange;
        
        console.log('📏 Масштабы:', { scaleX, scaleY });
        
        // Рисование осей
        ctx.strokeStyle = '#6B7280';
        ctx.lineWidth = 1;
        
        // Ось X
        ctx.beginPath();
        ctx.moveTo(padding.left, canvas.height - padding.bottom);
        ctx.lineTo(canvas.width - padding.right, canvas.height - padding.bottom);
        ctx.stroke();
        
        // Ось Y
        ctx.beginPath();
        ctx.moveTo(padding.left, padding.top);
        ctx.lineTo(padding.left, canvas.height - padding.bottom);
        ctx.stroke();
        
        // Подписи осей
        ctx.fillStyle = '#374151';
        ctx.font = '12px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        
        // Подписи оси X (время в днях) - округляем до целых
        // Выбираем оптимальный шаг для подписей, чтобы не было перекрытий
        const maxLabels = 12; // Максимальное количество подписей
        const xStep = Math.max(1, Math.floor(t.length / maxLabels));
        
        // Собираем уникальные округленные значения для отображения
        const displayedValues = new Set();
        for (let i = 0; i < t.length; i += xStep) {
            const roundedValue = Math.round(t[i]);
            if (!displayedValues.has(roundedValue)) {
                displayedValues.add(roundedValue);
                const x = padding.left + (t[i] * scaleX);
                // Округляем до целого числа для отображения
                ctx.fillText(roundedValue.toString(), x, canvas.height - padding.bottom + 5);
            }
        }
        
        // Подписи оси Y
        ctx.textAlign = 'right';
        ctx.textBaseline = 'middle';
        const yTicks = 8;
        for (let i = 0; i <= yTicks; i++) {
            const value = minY + (yRange / yTicks) * i;
            const y = canvas.height - padding.bottom - ((value - minY) * scaleY);
            ctx.fillText(value.toFixed(1), padding.left - 10, y);
        }
        
        // Заголовки осей
        ctx.textAlign = 'center';
        ctx.font = '14px Inter, sans-serif';
        ctx.fillText('Время (дни)', canvas.width / 2, canvas.height - 15);
        
        ctx.save();
        ctx.translate(15, canvas.height / 2);
        ctx.rotate(-Math.PI / 2);
        ctx.fillText('Значения показателей', 0, 0);
        ctx.restore();
        
        // Цвета для линий
        const series = [
            { data: V, color: '#EF4444', label: 'V (объем опухоли)' },
            { data: Ns, color: '#10B981', label: 'Ns (чувствительные клетки)' },
            { data: Nr, color: '#F59E0B', label: 'Nr (резистентные клетки)' },
            { data: N, color: '#3B82F6', label: 'N (общее количество клеток)' }
        ];
        
        // Рисование линий графика
        let hasDrawnAnyLine = false;
        series.forEach((serie, seriesIndex) => {
            if (!serie.data || serie.data.length === 0) {
                console.log(`⏭️ Пропуск серии ${serie.label}: нет данных`);
                return;
            }
            
            console.log(`🎨 Рисование серии ${serie.label}, точек: ${serie.data.length}`);
            
            ctx.strokeStyle = serie.color;
            ctx.lineWidth = 2;
            ctx.beginPath();
            
            let firstPoint = true;
            let validPoints = 0;
            
            for (let i = 0; i < t.length && i < serie.data.length; i++) {
                if (typeof t[i] !== 'number' || isNaN(t[i]) || typeof serie.data[i] !== 'number' || isNaN(serie.data[i])) {
                    continue;
                }
                
                const x = padding.left + (t[i] * scaleX);
                const y = canvas.height - padding.bottom - ((serie.data[i] - minY) * scaleY);
                
                if (firstPoint) {
                    ctx.moveTo(x, y);
                    firstPoint = false;
                } else {
                    ctx.lineTo(x, y);
                }
                validPoints++;
            }
            
            if (validPoints > 0) {
                ctx.stroke();
                hasDrawnAnyLine = true;
                console.log(`✅ Нарисована серия ${serie.label} с ${validPoints} точками`);
            }
            
            // Рисование точек (только для некоторых точек, чтобы не перегружать)
            ctx.fillStyle = serie.color;
            const pointStep = Math.max(1, Math.floor(t.length / 20));
            for (let i = 0; i < t.length && i < serie.data.length; i += pointStep) {
                if (typeof t[i] !== 'number' || isNaN(t[i]) || typeof serie.data[i] !== 'number' || isNaN(serie.data[i])) {
                    continue;
                }
                
                const x = padding.left + (t[i] * scaleX);
                const y = canvas.height - padding.bottom - ((serie.data[i] - minY) * scaleY);
                ctx.beginPath();
                ctx.arc(x, y, 3, 0, Math.PI * 2);
                ctx.fill();
            }
        });
        
        if (!hasDrawnAnyLine) {
            console.error('❌ Не удалось нарисовать ни одной линии графика');
            return;
        }
        
        console.log('✅ График успешно отрисован');
        
        // Создание легенды
        const legendDiv = document.getElementById('chartLegend');
        if (legendDiv) {
            const legendItems = series
                .filter(s => s.data && s.data.length > 0)
                .map(s => `
                    <div class="legend-item">
                        <span class="legend-color" style="background-color: ${s.color}"></span>
                        <span class="legend-label">${s.label}</span>
                    </div>
                `).join('');
            
            legendDiv.innerHTML = legendItems;
            console.log('✅ Легенда создана');
        } else {
            console.warn('⚠️ Элемент легенды не найден');
        }
    }
};