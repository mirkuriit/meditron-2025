const ApiService = {
    async analyzePatientData() {
        Recommendations.showLoading();
        
        const patientData = FormHandler.getFormData();
        
        console.log('📤 Отправляемые данные:', patientData);

        try {
            const [survivalResponse, tumorResponse] = await Promise.all([
                fetch('/api/reports/survival_month', {
                    method: 'POST',
                    headers: {
                        'accept': 'application/json',
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(patientData)
                }),
                fetch('/api/reports/tumor_dynamic', {
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

            const survivalData = survivalResponse.ok ? await survivalResponse.json() : null;
            const tumorData = tumorResponse.ok ? await tumorResponse.json() : null;

            if (!survivalData && !tumorData) {
                throw new Error('Бэкенд не вернул данные для отображения');
            }

            Recommendations.displayBackendResult({
                survival: survivalData,
                tumor_dynamic: tumorData
            });
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
    }
};