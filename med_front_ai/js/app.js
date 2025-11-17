document.addEventListener('DOMContentLoaded', function() {
    console.log('Страница загружена!');
    
    // Инициализация приложения
    FormHandler.init();
    
    // Обработчики основных кнопок
    document.getElementById('addPatientBtn').addEventListener('click', function() {
        FormHandler.clearForm();
        Recommendations.clear();
        showNotification('Форма очищена. Можете ввести данные нового пациента.', 'success');
    });

    document.getElementById('analyzeBtn').addEventListener('click', function() {
        if (FormHandler.validateForm()) {
            ApiService.analyzePatientData();
        }
    });

    document.getElementById('saveTxtBtn').addEventListener('click', function() {
        if (typeof saveToTXT === 'function') {
            saveToTXT();
        } else {
            showNotification('Сохранение отчета временно недоступно', 'error');
        }
    });
    
    // Загрузка формы
    FormHandler.loadForm();
});

// Глобальные функции уведомлений
function showNotification(message, type) {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    
    if (type === 'error') {
        notification.style.backgroundColor = '#EF4444';
    } else if (type === 'warning') {
        notification.style.backgroundColor = '#F59E0B';
    } else if (type === 'info') {
        notification.style.backgroundColor = '#3B82F6';
    } else {
        notification.style.backgroundColor = '#10B981';
    }
    
    notification.textContent = message;
    document.body.appendChild(notification);
    
    setTimeout(() => notification.style.opacity = '1', 100);
    
    setTimeout(() => {
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 300);
    }, 4000);
}