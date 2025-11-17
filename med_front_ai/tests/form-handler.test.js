import { describe, it, expect } from 'vitest';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Script, createContext } from 'node:vm';
import { JSDOM } from 'jsdom';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const FORM_HANDLER_PATH = path.resolve(__dirname, '../js/form-handler.js');
const FORM_HANDLER_CODE = readFileSync(FORM_HANDLER_PATH, 'utf8');

const CHEMOTHERAPY_STUB = {
  HER2_positive: {
    THP: {},
    TCHP: {}
  },
  HER2_negative: {
    ACT: {},
    TC: {}
  }
};

const HORMONE_THERAPY_STUB = {
  Tamoxifen: {},
  Letrozole: {}
};

function renderRadioGroup(name, values, selectedValue) {
  return values
    .map(
      (value, index) => `
    <label>
      <input type="radio" name="${name}" value="${value}" ${selectedValue === value ? 'checked' : ''}>
      ${name}-${index + 1}
    </label>
  `
    )
    .join('\n');
}

function buildFormHtml(overrides = {}) {
  const defaults = {
    age: '45',
    stage: 'IIA',
    ki67Level: '30',
    tumorSizeBefore: '25',
    chemotherapyRegimen: 'THP',
    hormoneTherapy: 'Tamoxifen',
    hormoneSectionDisplay: 'none',
    positiveLymphNodes: '2',
    tumorGrade: '2',
    performanceStatus: '1',
    menopausalStatus: 'true',
    surgeryType: 'true'
  };

  const state = { ...defaults, ...overrides };

  return `
    <div id="form-root">
      <input id="age" value="${state.age ?? ''}">
      <input id="stage" value="${state.stage ?? ''}">
      <input id="ki67Level" value="${state.ki67Level ?? ''}">
      <input id="tumorSizeBefore" value="${state.tumorSizeBefore ?? ''}">
      <input id="positiveLymphNodes" value="${state.positiveLymphNodes ?? ''}">

      <select id="chemotherapyRegimen">
        <option value="" ${state.chemotherapyRegimen ? '' : 'selected'}>Выберите режим</option>
        <option value="THP" ${state.chemotherapyRegimen === 'THP' ? 'selected' : ''}>THP</option>
        <option value="ACT" ${state.chemotherapyRegimen === 'ACT' ? 'selected' : ''}>AC-T</option>
      </select>

      <div id="hormoneSection" style="display:${state.hormoneSectionDisplay};">
        <select id="hormoneTherapy">
          <option value="" ${state.hormoneTherapy ? '' : 'selected'}>Выберите гормонотерапию</option>
          <option value="Tamoxifen" ${state.hormoneTherapy === 'Tamoxifen' ? 'selected' : ''}>Tamoxifen</option>
        </select>
      </div>

      <div id="tnbcWarning"></div>
      <div id="hormoneWarning"></div>

      <div class="radio-group">
        ${renderRadioGroup('tumorGrade', ['1', '2', '3'], state.tumorGrade)}
      </div>
      <div class="radio-group">
        ${renderRadioGroup('performanceStatus', ['0', '1', '2'], state.performanceStatus)}
      </div>
      <div class="radio-group">
        ${renderRadioGroup('menopausalStatus', ['true', 'false'], state.menopausalStatus)}
      </div>
      <div class="radio-group">
        ${renderRadioGroup('surgeryType', ['true', 'false'], state.surgeryType)}
      </div>
    </div>
  `;
}

function createFormHandlerContext(dom, notificationCalls) {
  const context = {
    window: dom.window,
    document: dom.window.document,
    console,
    showNotification: (message, type) => notificationCalls.push({ message, type }),
    CHEMOTHERAPY_REGIMENS: CHEMOTHERAPY_STUB,
    HORMONE_THERAPY_OPTIONS: HORMONE_THERAPY_STUB,
    setTimeout: dom.window.setTimeout.bind(dom.window),
    clearTimeout: dom.window.clearTimeout.bind(dom.window)
  };

  createContext(context);
  
 
  const wrappedCode = `
    ${FORM_HANDLER_CODE}
    globalThis.FormHandler = FormHandler;
  `;
  
  const script = new Script(wrappedCode, { filename: 'form-handler.js' });
  script.runInContext(context);
  
  return context;
}

function runValidation(overrides = {}) {
  const dom = new JSDOM(`<!doctype html><html><body>${buildFormHtml(overrides)}</body></html>`, {
    url: 'http://localhost'
  });
  const notificationCalls = [];
  const context = createFormHandlerContext(dom, notificationCalls);
  const result = context.FormHandler.validateForm();
  return { result, notificationCalls };
}

function lastMessage(calls) {
  return calls[calls.length - 1] ?? null;
}

describe('FormHandler.validateForm', () => {
  it('rejects empty required text fields', () => {
    const { result, notificationCalls } = runValidation({ age: '' });
    expect(result).toBe(false);
    expect(lastMessage(notificationCalls)?.message).toContain('Возраст');
  });

  it('enforces the allowed age range', () => {
    const { result, notificationCalls } = runValidation({ age: '130' });
    expect(result).toBe(false);
    expect(lastMessage(notificationCalls)?.message).toContain('Возраст должен быть от 1 до 120 лет');
  });

  it('validates Ki-67 percentage boundaries', () => {
    const { result, notificationCalls } = runValidation({ ki67Level: '150' });
    expect(result).toBe(false);
    expect(lastMessage(notificationCalls)?.message).toContain('Уровень Ki-67 должен быть от 0 до 100%');
  });

  it('prevents negative tumor size values', () => {
    const { result, notificationCalls } = runValidation({ tumorSizeBefore: '-5' });
    expect(result).toBe(false);
    expect(lastMessage(notificationCalls)?.message).toContain('Размер опухоли должен быть от 0 до 500 мм');
  });

  it('requires tumor grade selection', () => {
    const { result, notificationCalls } = runValidation({ tumorGrade: null });
    expect(result).toBe(false);
    expect(lastMessage(notificationCalls)?.message).toContain('степень злокачественности опухоли');
  });

  it('requires chemotherapy regimen selection', () => {
    const { result, notificationCalls } = runValidation({ chemotherapyRegimen: '' });
    expect(result).toBe(false);
    expect(lastMessage(notificationCalls)?.message).toContain('Выберите режим химиотерапии');
  });

  it('requires hormone therapy when the section is visible', () => {
    const { result, notificationCalls } = runValidation({
      hormoneSectionDisplay: 'block',
      hormoneTherapy: ''
    });
    expect(result).toBe(false);
    expect(lastMessage(notificationCalls)?.message).toContain('Выберите гормональную терапию');
  });

  it('returns true for a fully valid dataset', () => {
    const { result, notificationCalls } = runValidation();
    expect(result).toBe(true);
    expect(notificationCalls.length).toBe(0);
  });
});

