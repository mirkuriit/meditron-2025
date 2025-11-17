const ApiService = {
    async analyzePatientData() {
        Recommendations.showLoading();
        
        const patientData = FormHandler.getFormData();
        
        console.log('📤 Отправляемые данные:', patientData);

        try {
            // Параллельные запросы к двум эндпоинтам
            const [survivalResponse, tumorResponse] = await Promise.all([
                // Запрос к выживаемости
                fetch('http://89.169.174.45:8010/reports/survival_month', {
                    method: 'POST',
                    headers: {
                        'accept': 'application/json',
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(patientData)
                }),
                // Запрос к динамике опухоли
                fetch('http://89.169.174.45:8010/reports/tumor_dynamic', {
                    method: 'POST',
                    headers: {
                        'accept': 'application/json',
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(patientData)
                })
            ]);

            console.log('📥 Статус ответа выживаемости:', survivalResponse.status);
            console.log('📥 Статус ответа динамики:', tumorResponse.status);

            // Обрабатываем ответы
            const survivalData = survivalResponse.ok ? await survivalResponse.json() : null;
            const tumorData = tumorResponse.ok ? await tumorResponse.json() : null;

            const combinedResult = {
                // Данные о выживаемости
                month: survivalData?.survival_month || survivalData?.month,
                survival_metrics: survivalData,
                
                // Данные о динамике опухоли
                t: tumorData?.t,
                indicator: tumorData?.indicator,
                tumor_dynamic: tumorData,
                
                // Генерация рекомендаций
                treatment_recommendations: this.generateTreatmentRecommendations(survivalData, tumorData),
                risks: this.generateRisks(survivalData),
                monitoring: this.generateMonitoringPlan(survivalData),
                
                // Мета-информация
                data_sources: {
                    survival: !!survivalData,
                    tumor_dynamic: !!tumorData
                },
                timestamp: new Date().toISOString()
            };

            console.log('✅ Комбинированные данные:', combinedResult);
            
            Recommendations.displayBackendResult(combinedResult);
            showNotification('Анализ завершен успешно!', 'success');
            
        } catch (error) {
            console.error('❌ Ошибка при анализе данных:', error);
            
            if (error.message.includes('Failed to fetch') || error.message.includes('CORS')) {
                showNotification('CORS ошибка. Запустите браузер с отключенной CORS политикой.', 'error');
            } else {
                showNotification(`Ошибка: ${error.message}`, 'error');
            }
            
            Recommendations.clear();
        }
    },

    generateTreatmentRecommendations(survivalData, tumorData) {
        const recommendations = [];
        
        // Рекомендации на основе выживаемости
        const survivalMonth = survivalData?.survival_month || survivalData?.month;
        if (survivalMonth) {
            if (survivalMonth < 24) {
                recommendations.push('Агрессивная комбинированная химиотерапия');
                recommendations.push('Рассмотреть таргетную терапию и иммунотерапию');
                recommendations.push('Интенсивный мониторинг ответа на лечение');
            } else if (survivalMonth < 60) {
                recommendations.push('Стандартная адъювантная химиотерапия');
                recommendations.push('Гормональная терапия по показаниям');
                recommendations.push('Регулярный контроль эффективности');
            } else {
                recommendations.push('Консервативная терапия с наблюдением');
                recommendations.push('Фокус на качество жизни пациента');
            }
        }
        
        return recommendations.length > 0 ? recommendations : [
            'Индивидуальный план лечения на основе клинических данных',
            'Регулярная оценка переносимости терапии'
        ];
    },

    generateRisks(survivalData) {
        const risks = [
            'Гематологическая токсичность (нейтропения, анемия, тромбоцитопения)',
            'Риск инфекционных осложнений на фоне иммуносупрессии',
            'Гепато- и нефротоксичность'
        ];
        
        const survivalMonth = survivalData?.survival_month || survivalData?.month;
        if (survivalMonth && survivalMonth < 36) {
            risks.push('Высокий риск прогрессирования заболевания');
            risks.push('Необходимость частого мониторинга и коррекции терапии');
        }
        
        return risks;
    },

    generateMonitoringPlan(survivalData) {
        const survivalMonth = survivalData?.survival_month || survivalData?.month;
        
        if (survivalMonth && survivalMonth < 24) {
            return 'Интенсивный мониторинг каждые 2-3 месяца: ОАК, биохимический анализ крови, УЗИ/КТ, оценка токсичности';
        } else if (survivalMonth && survivalMonth < 60) {
            return 'Стандартный мониторинг каждые 3-4 месяца: ОАК, биохимия, УЗИ молочных желез и регионарных лимфоузлов';
        } else {
            return 'Плановый мониторинг каждые 6 месяцев: ОАК, биохимия, маммография';
        }
    }
};