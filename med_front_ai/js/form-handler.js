const FormHandler = {
    init() {
        this.setupEventListeners();
    },
    
    async loadForm() {
        try {
            const response = await fetch('components/form-fields.html');
            const formHtml = await response.text();
            document.getElementById('form-fields-container').innerHTML = formHtml;
            this.setupDynamicEventListeners();
            this.updateChemotherapyOptions();
            this.updateHormoneTherapyOptions();
        } catch (error) {
            console.error('Ошибка загрузки формы:', error);
        }
    },
    
    setupEventListeners() {
        // Базовые слушатели будут установлены после загрузки формы
    },
    
    setupDynamicEventListeners() {
        // Обработчики для лимфоузлов
        const decreaseLymphNodesBtn = document.getElementById('decreaseLymphNodes');
        const increaseLymphNodesBtn = document.getElementById('increaseLymphNodes');
        const lymphNodesInput = document.getElementById('positiveLymphNodes');
        
        if (decreaseLymphNodesBtn && increaseLymphNodesBtn && lymphNodesInput) {
            decreaseLymphNodesBtn.addEventListener('click', function() {
                let value = parseInt(lymphNodesInput.value) || 0;
                if (value > 0) {
                    lymphNodesInput.value = value - 1;
                }
            });

            increaseLymphNodesBtn.addEventListener('click', function() {
                let value = parseInt(lymphNodesInput.value) || 0;
                if (value < 15) {
                    lymphNodesInput.value = value + 1;
                }
            });
        }
        
        // Обработчики для биомаркеров (TNBC логика)
        const erCheckbox = document.getElementById('erStatus');
        const prCheckbox = document.getElementById('prStatus');
        const her2Checkbox = document.getElementById('her2Status');
        
        [erCheckbox, prCheckbox, her2Checkbox].forEach(checkbox => {
            if (checkbox) {
                checkbox.addEventListener('change', () => {
                    this.updateTNBCCalculation();
                    this.updateHormoneTherapySection();
                    this.updateChemotherapyOptions();
                });
            }
        });
        
        // Обработчики для метастазов
        const metNoneCheckbox = document.getElementById('metNone');
        const metLocationCheckboxes = [
            document.getElementById('metBone'),
            document.getElementById('metBrain'),
            document.getElementById('metLiver'),
            document.getElementById('metLung')
        ];
        
        // Если выбрано "Нет метастазов", снимаем все остальные галочки
        if (metNoneCheckbox) {
            metNoneCheckbox.addEventListener('change', () => {
                if (metNoneCheckbox.checked) {
                    metLocationCheckboxes.forEach(checkbox => {
                        if (checkbox) checkbox.checked = false;
                    });
                }
            });
        }
        
        // Если выбрана любая локализация метастазов, снимаем галочку "Нет метастазов"
        metLocationCheckboxes.forEach(checkbox => {
            if (checkbox) {
                checkbox.addEventListener('change', () => {
                    if (checkbox.checked && metNoneCheckbox) {
                        metNoneCheckbox.checked = false;
                    }
                });
            }
        });
    },
    
    updateTNBCCalculation() {
        const erStatus = document.getElementById('erStatus').checked;
        const prStatus = document.getElementById('prStatus').checked;
        const her2Status = document.getElementById('her2Status').checked;
        const tnbcWarning = document.getElementById('tnbcWarning');
        
        // TNBC: все три false
        const isTNBC = !erStatus && !prStatus && !her2Status;
        
        if (tnbcWarning) {
            if (isTNBC) {
                tnbcWarning.style.display = 'block';
                tnbcWarning.innerHTML = '<strong>Трижды негативная опухоль (TNBC)</strong>';
            } else {
                tnbcWarning.style.display = 'none';
            }
        }
        
        return isTNBC;
    },
    
    updateHormoneTherapySection() {
        const erStatus = document.getElementById('erStatus').checked;
        const prStatus = document.getElementById('prStatus').checked;
        const hormoneWarning = document.getElementById('hormoneWarning');
        const hormoneSection = document.getElementById('hormoneSection');
        
        // Гормональная терапия не показана если оба рецептора отрицательные
        const hormoneNotIndicated = !erStatus && !prStatus;
        
        if (hormoneWarning) {
            if (hormoneNotIndicated) {
                hormoneWarning.style.display = 'block';
            } else {
                hormoneWarning.style.display = 'none';
            }
        }
        
        if (hormoneSection) {
            if (!hormoneNotIndicated) {
                hormoneSection.style.display = 'block';
            } else {
                hormoneSection.style.display = 'none';
            }
        }
        
        return !hormoneNotIndicated; // Возвращает true если гормональная терапия показана
    },
    
    updateChemotherapyOptions() {
        const her2Status = document.getElementById('her2Status').checked;
        const chemotherapySelect = document.getElementById('chemotherapyRegimen');
        
        if (!chemotherapySelect) return;
        
        // Очищаем текущие опции
        chemotherapySelect.innerHTML = '<option value="">Выберите режим химиотерапии</option>';
        
        // Выбираем соответствующий набор режимов
        const regimens = her2Status ? CHEMOTHERAPY_REGIMENS.HER2_positive : CHEMOTHERAPY_REGIMENS.HER2_negative;
        
        // Добавляем опции
        Object.keys(regimens).forEach(regimen => {
            const option = document.createElement('option');
            option.value = regimen;
            option.textContent = regimen;
            chemotherapySelect.appendChild(option);
        });
    },
    
    updateHormoneTherapyOptions() {
        const hormoneSelect = document.getElementById('hormoneTherapy');
        
        if (!hormoneSelect) return;
        
        // Очищаем текущие опции
        hormoneSelect.innerHTML = '<option value="">Выберите гормональную терапию</option>';
        
        // Добавляем опции
        Object.keys(HORMONE_THERAPY_OPTIONS).forEach(therapy => {
            const option = document.createElement('option');
            option.value = therapy;
            option.textContent = therapy;
            hormoneSelect.appendChild(option);
        });
    },
    
    validateForm() {
        const requiredFields = [
            { field: document.getElementById('firstName'), name: 'Имя' },
            { field: document.getElementById('lastName'), name: 'Фамилия' },
            { field: document.getElementById('age'), name: 'Возраст' },
            { field: document.getElementById('stage'), name: 'Стадия РМЖ' },
            { field: document.getElementById('ki67Level'), name: 'Уровень Ki-67' },
            { field: document.getElementById('tumorSizeBefore'), name: 'Размер опухоли до лечения' }
        ];

        for (let field of requiredFields) {
            if (field.field && !field.field.value.trim()) {
                showNotification(`Поле "${field.name}" обязательно для заполнения`, 'error');
                field.field.focus();
                return false;
            }
        }

        // Проверка числовых значений
        const age = parseInt(document.getElementById('age').value);
        const ki67 = parseFloat(document.getElementById('ki67Level').value);
        const tumorSize = parseFloat(document.getElementById('tumorSizeBefore').value);

        if (age <= 0 || age > 120) {
            showNotification('Возраст должен быть от 1 до 120 лет', 'error');
            return false;
        }

        if (ki67 < 0 || ki67 > 100) {
            showNotification('Уровень Ki-67 должен быть от 0 до 100%', 'error');
            return false;
        }

        if (tumorSize < 0 || tumorSize > 500) {
            showNotification('Размер опухоли должен быть от 0 до 500 мм', 'error');
            return false;
        }

        // Проверка радио-кнопок
        const tumorGradeSelected = document.querySelector('input[name="tumorGrade"]:checked');
        const performanceStatusSelected = document.querySelector('input[name="performanceStatus"]:checked');
        const menopausalStatusSelected = document.querySelector('input[name="menopausalStatus"]:checked');
        const surgeryTypeSelected = document.querySelector('input[name="surgeryType"]:checked');

        if (!tumorGradeSelected) {
            showNotification('Выберите степень злокачественности опухоли', 'error');
            return false;
        }

        if (!performanceStatusSelected) {
            showNotification('Выберите функциональный статус по шкале ECOG', 'error');
            return false;
        }

        if (!menopausalStatusSelected) {
            showNotification('Выберите менопаузальный статус', 'error');
            return false;
        }

        if (!surgeryTypeSelected) {
            showNotification('Выберите наличие хирургического вмешательства', 'error');
            return false;
        }

        const chemotherapySelect = document.getElementById('chemotherapyRegimen');
        if (chemotherapySelect && !chemotherapySelect.value) {
            showNotification('Выберите режим химиотерапии', 'error');
            chemotherapySelect.focus();
            return false;
        }

        const hormoneSection = document.getElementById('hormoneSection');
        const hormoneSelect = document.getElementById('hormoneTherapy');
        const hormoneRequired = hormoneSection && window.getComputedStyle(hormoneSection).display !== 'none';
        if (hormoneRequired && hormoneSelect && !hormoneSelect.value) {
            showNotification('Выберите гормональную терапию', 'error');
            hormoneSelect.focus();
            return false;
        }

        return true;
    },
    
    getFormData() {
        const menopausalStatusSelected = document.querySelector('input[name="menopausalStatus"]:checked');
        const surgeryTypeSelected = document.querySelector('input[name="surgeryType"]:checked');
        const hormoneSelect = document.getElementById('hormoneTherapy');
        const chemotherapySelect = document.getElementById('chemotherapyRegimen');
        const hormoneValue = hormoneSelect ? hormoneSelect.value : '';
        const chemotherapyValue = chemotherapySelect ? chemotherapySelect.value : null;

        const metBone = document.getElementById('metBone').checked;
        const metBrain = document.getElementById('metBrain').checked;
        const metLiver = document.getElementById('metLiver').checked;
        const metLung = document.getElementById('metLung').checked;
        const metNoneCheckbox = document.getElementById('metNone').checked;
        const noMetastasis = metNoneCheckbox || (!metBone && !metBrain && !metLiver && !metLung);

        const positiveNodesValue = parseInt(document.getElementById('positiveLymphNodes').value, 10);
        const tumorSizeValue = parseFloat(document.getElementById('tumorSizeBefore').value);
        const ki67Value = parseFloat(document.getElementById('ki67Level').value);

        const erStatus = document.getElementById('erStatus').checked;
        const prStatus = document.getElementById('prStatus').checked;
        const her2Status = document.getElementById('her2Status').checked;

        return {
            first_name: document.getElementById('firstName').value.trim(),
            last_name: document.getElementById('lastName').value.trim(),
            patronymic: document.getElementById('patronymic').value.trim(),
            age: parseInt(document.getElementById('age').value, 10),
            stage: document.getElementById('stage').value,
            menopausal_status: menopausalStatusSelected ? menopausalStatusSelected.value === 'true' : false,
            family_history: document.getElementById('familyHistory').checked,
            er_status: erStatus,
            pr_status: prStatus,
            her2_status: her2Status,
            brca_mutation: document.getElementById('brcaMutation').checked,
            ki67_level: Number.isFinite(ki67Value) ? ki67Value : 0,
            tnbc: !erStatus && !prStatus && !her2Status,
            harmon: Boolean(hormoneValue),
            surgery_type: surgeryTypeSelected ? surgeryTypeSelected.value === 'true' : false,
            HER2_treatment: chemotherapyValue,
            harmon_treatment: hormoneValue || null,
            tumor_size_before: Number.isFinite(tumorSizeValue) ? Math.round(tumorSizeValue) : 0,
            positive_lymph_nodes: Number.isInteger(positiveNodesValue) ? positiveNodesValue : 0,
            tumor_grade: parseInt(document.querySelector('input[name="tumorGrade"]:checked').value, 10),
            performance_status: parseInt(document.querySelector('input[name="performanceStatus"]:checked').value, 10),
            met_bone: metBone,
            met_brain: metBrain,
            met_liver: metLiver,
            met_lung: metLung,
            met_none: noMetastasis
        };
    },
    
    clearForm() {
        // Текстовые поля и селекты
        const fieldsToClear = [
            'firstName', 'lastName', 'patronymic', 'age', 'stage',
            'ki67Level', 'tumorSizeBefore', 'chemotherapyRegimen', 'hormoneTherapy'
        ];
        
        fieldsToClear.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) field.value = '';
        });
        
        // Чекбоксы
        const checkboxes = [
            'familyHistory', 'erStatus', 'prStatus', 'her2Status', 
            'brcaMutation', 'metBone', 'metBrain', 'metLiver', 'metLung', 'metNone'
        ];
        
        checkboxes.forEach(checkboxId => {
            const checkbox = document.getElementById(checkboxId);
            if (checkbox) checkbox.checked = false;
        });
        
        // Радио-кнопки
        const radioGroups = ['tumorGrade', 'performanceStatus', 'menopausalStatus', 'surgeryType'];
        radioGroups.forEach(groupName => {
            const radios = document.getElementsByName(groupName);
            radios.forEach(radio => radio.checked = false);
        });
        
        // Специальные поля
        document.getElementById('positiveLymphNodes').value = '0';
        
        // Скрываем предупреждения и секции
        document.getElementById('tnbcWarning').style.display = 'none';
        document.getElementById('hormoneWarning').style.display = 'none';
        document.getElementById('hormoneSection').style.display = 'none';
        
        // Обновляем опции
        this.updateChemotherapyOptions();
        this.updateHormoneTherapyOptions();
    }
};