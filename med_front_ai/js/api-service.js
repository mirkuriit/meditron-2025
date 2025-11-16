const ApiService = {
    async analyzePatientData() {
        Recommendations.showLoading();
        
        const patientData = FormHandler.getFormData();
        
        console.log('📤 Отправляемые данные:', patientData);

        try {
            const [survivalResponse, tumorResponse] = await Promise.all([
                fetch('http://89.169.174.45:8010/reports/survival_month', {
                    method: 'POST',
                    headers: {
                        'accept': 'application/json',
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(patientData)
                }),
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

            let survivalData = null;
            let tumorData = null;

            if (survivalResponse.ok) {
                survivalData = await survivalResponse.json();
                console.log('📊 Данные выживаемости:', survivalData);
            } else {
                console.warn('⚠️ Ошибка получения данных выживаемости:', survivalResponse.status);
            }

            if (tumorResponse.ok) {
                tumorData = await tumorResponse.json();
                console.log('📊 Данные динамики опухоли:', tumorData);
            } else {
                const errorText = await tumorResponse.text();
                console.warn('⚠️ Ошибка получения данных динамики:', tumorResponse.status, errorText);
            }

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