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

        if (!hasSurvival && !hasTumorData) {
            recommendationsDiv.innerHTML = '<p class="placeholder">От бэкенда не получены данные для отображения</p>';
            this.toggleSaveButton(true);
            return;
        }

        let html = '';

        if (hasSurvival) {
            html += this.renderDataSection('📈 Данные о выживаемости', result.survival);
        }

        if (hasTumorData) {
            html += this.renderDataSection('📉 Динамика опухоли', result.tumor_dynamic);
            const timeSeries = this.extractSeries(result.tumor_dynamic, ['t', 'time', 'timeline']);
            const measurements = this.extractSeries(result.tumor_dynamic, ['indicator', 'values', 'measurements']);

            if (timeSeries.length && measurements.length) {
                html += this.generateChart();
                setTimeout(() => this.renderChart(timeSeries, measurements), 100);
            }
        }

        recommendationsDiv.innerHTML = html;
        this.toggleSaveButton(false);
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
                <h3>📈 График динамики</h3>
                <div class="chart-container">
                    <canvas id="tumorSizeChart" width="400" height="200"></canvas>
                </div>
                <p style="text-align: center; color: #6B7280; margin-top: 10px; font-size: 14px;">
                    Основано на данных, полученных с бэкенда
                </p>
            </div>
        `;
    },

    renderChart(t, indicator) {
        const canvas = document.getElementById('tumorSizeChart');
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        // Очистка canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Настройки графика
        const padding = 40;
        const chartWidth = canvas.width - padding * 2;
        const chartHeight = canvas.height - padding * 2;
        
        // Масштабирование данных
        const maxX = Math.max(...t);
        const maxY = Math.max(...indicator);
        const scaleX = chartWidth / (maxX || 1);
        const scaleY = chartHeight / (maxY || 1);
        
        // Рисование осей
        ctx.strokeStyle = '#374151';
        ctx.lineWidth = 1;
        
        // Ось X
        ctx.beginPath();
        ctx.moveTo(padding, canvas.height - padding);
        ctx.lineTo(canvas.width - padding, canvas.height - padding);
        ctx.stroke();
        
        // Ось Y
        ctx.beginPath();
        ctx.moveTo(padding, padding);
        ctx.lineTo(padding, canvas.height - padding);
        ctx.stroke();
        
        // Подписи осей
        ctx.fillStyle = '#374151';
        ctx.font = '12px Inter';
        ctx.textAlign = 'center';
        
        // Подписи оси X
        for (let i = 0; i < t.length; i++) {
            const x = padding + (t[i] * scaleX);
            ctx.fillText(t[i], x, canvas.height - padding + 15);
        }
        
        // Подписи оси Y
        ctx.textAlign = 'right';
        for (let i = 0; i <= 5; i++) {
            const value = Math.round((maxY / 5) * i);
            const y = canvas.height - padding - (value * scaleY);
            ctx.fillText(value, padding - 5, y + 3);
        }
        
        // Заголовок
        ctx.textAlign = 'center';
        ctx.font = '14px Inter';
        ctx.fillText('Динамика онкомаркера', canvas.width / 2, padding - 10);
        
        // Рисование линии графика
        ctx.strokeStyle = '#15B5C1';
        ctx.lineWidth = 2;
        ctx.beginPath();
        
        for (let i = 0; i < t.length; i++) {
            const x = padding + (t[i] * scaleX);
            const y = canvas.height - padding - (indicator[i] * scaleY);
            
            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        }
        ctx.stroke();
        
        // Рисование точек
        ctx.fillStyle = '#15B5C1';
        for (let i = 0; i < t.length; i++) {
            const x = padding + (t[i] * scaleX);
            const y = canvas.height - padding - (indicator[i] * scaleY);
            ctx.beginPath();
            ctx.arc(x, y, 4, 0, Math.PI * 2);
            ctx.fill();
        }
    }
};