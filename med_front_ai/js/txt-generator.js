// Сохранение в TXT
function saveToTXT() {
    const recommendationsDiv = document.getElementById('recommendations');
    if (!recommendationsDiv) return;
    
    const patientData = (typeof FormHandler !== 'undefined' && FormHandler.getFormData)
        ? FormHandler.getFormData()
        : null;

    if (!patientData) {
        showNotification('Не удалось собрать данные пациента для отчета', 'error');
        return;
    }

    if (recommendationsDiv.querySelector('.placeholder') || !recommendationsDiv.textContent.trim()) {
        showNotification('Нет данных рекомендаций для сохранения', 'warning');
        return;
    }

    const yesNo = (value) => value ? 'Да' : 'Нет';
    const receptorStatus = (value) => value ? 'Положительный' : 'Отрицательный';
    const menopausalStatusText = patientData.menopausal_status ? 'Менопауза наступила' : 'Менопауза не наступила';
    const surgeryStatusText = patientData.surgery_type ? 'Проводилось' : 'Не проводилось';
    const hormoneTherapyText = patientData.harmon_treatment ? patientData.harmon_treatment : 'Не назначена';

    const recommendationsText = recommendationsDiv.innerText;
    
    let txtContent = 'МЕДИЦИНСКИЙ ОТЧЕТ\n';
    txtContent += '='.repeat(50) + '\n\n';
    
    // Данные пациента
    txtContent += 'ДАННЫЕ ПАЦИЕНТА:\n';
    txtContent += '-'.repeat(30) + '\n';
    txtContent += `ФИО: ${patientData.last_name} ${patientData.first_name} ${patientData.patronymic}\n`;
    txtContent += `Возраст: ${patientData.age} лет\n`;
    txtContent += `Стадия: ${patientData.stage}\n`;
    txtContent += `Ki-67: ${patientData.ki67_level}%\n`;
    txtContent += `Размер опухоли: ${patientData.tumor_size_before} мм\n`;
    txtContent += `Пораженные лимфоузлы: ${patientData.positive_lymph_nodes}\n`;
    txtContent += `Менопаузальный статус: ${menopausalStatusText}\n`;
    txtContent += `Семейный анамнез: ${yesNo(patientData.family_history)}\n`;
    txtContent += `ER статус: ${receptorStatus(patientData.er_status)}\n`;
    txtContent += `PR статус: ${receptorStatus(patientData.pr_status)}\n`;
    txtContent += `HER2 статус: ${receptorStatus(patientData.her2_status)}\n`;
    txtContent += `BRCA мутация: ${yesNo(patientData.brca_mutation)}\n`;
    txtContent += `TNBC: ${yesNo(patientData.tnbc)}\n`;
    txtContent += `Хирургическое вмешательство: ${surgeryStatusText}\n`;
    txtContent += `HER2-терапия: ${patientData.HER2_treatment || 'Не выбрана'}\n`;
    txtContent += `Гормонотерапия назначена: ${yesNo(patientData.harmon)}\n`;
    txtContent += `Назначенная схема гормонотерапии: ${hormoneTherapyText}\n`;
    
    // Метастазы
    const hasMetastasis = patientData.met_bone || patientData.met_brain || patientData.met_liver || patientData.met_lung;
    txtContent += `Метастазы: ${hasMetastasis ? 'Да' : 'Нет'}\n`;
    
    if (hasMetastasis) {
        txtContent += `Локализация метастазов:\n`;
        if (patientData.met_bone) txtContent += '  - Кости\n';
        if (patientData.met_brain) txtContent += '  - Головной мозг\n';
        if (patientData.met_liver) txtContent += '  - Печень\n';
        if (patientData.met_lung) txtContent += '  - Легкие\n';
    } else if (patientData.met_none) {
        txtContent += `Метастазы отсутствуют\n`;
    }
    
    txtContent += `Степень злокачественности: ${patientData.tumor_grade}\n`;
    txtContent += `Функциональный статус (ECOG): ${patientData.performance_status}\n`;
    
    txtContent += '\n';
    
    // Рекомендации
    txtContent += 'РЕКОМЕНДАЦИИ И РЕЗУЛЬТАТЫ АНАЛИЗА:\n';
    txtContent += '-'.repeat(45) + '\n';
    txtContent += recommendationsText + '\n\n';
    
    // Дата и подпись
    txtContent += '='.repeat(50) + '\n';
    txtContent += `Отчет создан: ${new Date().toLocaleDateString('ru-RU')}\n`;
    txtContent += 'Врач: ___________________\n';
    
    // Создание и скачивание файла
    const blob = new Blob([txtContent], { type: 'text/plain; charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `medical_report_${patientData.last_name}_${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}