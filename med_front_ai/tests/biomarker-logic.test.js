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
  HER2_positive: { THP: {}, TCHP: {} },
  HER2_negative: { ACT: {}, TC: {} }
};

const HORMONE_THERAPY_STUB = {
  Tamoxifen: {},
  Letrozole: {}
};

function buildBiomarkerFormHtml(erStatus = false, prStatus = false, her2Status = false) {
  return `
    <div id="form-root">
      <input type="checkbox" id="erStatus" ${erStatus ? 'checked' : ''}>
      <input type="checkbox" id="prStatus" ${prStatus ? 'checked' : ''}>
      <input type="checkbox" id="her2Status" ${her2Status ? 'checked' : ''}>
      <div id="tnbcWarning" style="display: none;"></div>
      <div id="hormoneWarning" style="display: none;"></div>
      <div id="hormoneSection" style="display: none;"></div>
      <select id="chemotherapyRegimen"></select>
    </div>
  `;
}

function createFormHandlerContext(dom) {
  const context = {
    window: dom.window,
    document: dom.window.document,
    console,
    showNotification: () => {},
    CHEMOTHERAPY_REGIMENS: CHEMOTHERAPY_STUB,
    HORMONE_THERAPY_OPTIONS: HORMONE_THERAPY_STUB,
    setTimeout: dom.window.setTimeout.bind(dom.window),
    clearTimeout: dom.window.clearTimeout.bind(dom.window)
  };

  createContext(context);
  
  // Wrap the code to make FormHandler available in context
  const wrappedCode = `
    ${FORM_HANDLER_CODE}
    globalThis.FormHandler = FormHandler;
  `;
  
  const script = new Script(wrappedCode, { filename: 'form-handler.js' });
  script.runInContext(context);
  
  return context;
}

function testTNBCCalculation(erStatus, prStatus, her2Status) {
  const dom = new JSDOM(
    `<!doctype html><html><body>${buildBiomarkerFormHtml(erStatus, prStatus, her2Status)}</body></html>`,
    { url: 'http://localhost' }
  );
  const context = createFormHandlerContext(dom);
  const isTNBC = context.FormHandler.updateTNBCCalculation();
  const tnbcWarning = dom.window.document.getElementById('tnbcWarning');
  return { isTNBC, isWarningVisible: tnbcWarning.style.display === 'block' };
}

function testHormoneTherapySection(erStatus, prStatus) {
  const dom = new JSDOM(
    `<!doctype html><html><body>${buildBiomarkerFormHtml(erStatus, prStatus, false)}</body></html>`,
    { url: 'http://localhost' }
  );
  const context = createFormHandlerContext(dom);
  const isHormoneIndicated = context.FormHandler.updateHormoneTherapySection();
  const hormoneSection = dom.window.document.getElementById('hormoneSection');
  const hormoneWarning = dom.window.document.getElementById('hormoneWarning');
  return {
    isHormoneIndicated,
    isSectionVisible: hormoneSection.style.display === 'block',
    isWarningVisible: hormoneWarning.style.display === 'block'
  };
}

describe('Biomarker Logic Tests', () => {
  describe('TNBC (Triple Negative Breast Cancer) Detection', () => {
    it('identifies TNBC when all biomarkers are negative', () => {
      const { isTNBC, isWarningVisible } = testTNBCCalculation(false, false, false);
      expect(isTNBC).toBe(true);
      expect(isWarningVisible).toBe(true);
    });

    it('does not identify TNBC when ER is positive', () => {
      const { isTNBC, isWarningVisible } = testTNBCCalculation(true, false, false);
      expect(isTNBC).toBe(false);
      expect(isWarningVisible).toBe(false);
    });

    it('does not identify TNBC when PR is positive', () => {
      const { isTNBC, isWarningVisible } = testTNBCCalculation(false, true, false);
      expect(isTNBC).toBe(false);
      expect(isWarningVisible).toBe(false);
    });

    it('does not identify TNBC when HER2 is positive', () => {
      const { isTNBC, isWarningVisible } = testTNBCCalculation(false, false, true);
      expect(isTNBC).toBe(false);
      expect(isWarningVisible).toBe(false);
    });

    it('does not identify TNBC when ER and PR are positive', () => {
      const { isTNBC, isWarningVisible } = testTNBCCalculation(true, true, false);
      expect(isTNBC).toBe(false);
      expect(isWarningVisible).toBe(false);
    });

    it('does not identify TNBC when ER and HER2 are positive', () => {
      const { isTNBC, isWarningVisible } = testTNBCCalculation(true, false, true);
      expect(isTNBC).toBe(false);
      expect(isWarningVisible).toBe(false);
    });

    it('does not identify TNBC when PR and HER2 are positive', () => {
      const { isTNBC, isWarningVisible } = testTNBCCalculation(false, true, true);
      expect(isTNBC).toBe(false);
      expect(isWarningVisible).toBe(false);
    });

    it('does not identify TNBC when all biomarkers are positive', () => {
      const { isTNBC, isWarningVisible } = testTNBCCalculation(true, true, true);
      expect(isTNBC).toBe(false);
      expect(isWarningVisible).toBe(false);
    });
  });

  describe('Hormone Therapy Section Visibility', () => {
    it('hides hormone therapy section when both ER and PR are negative', () => {
      const { isHormoneIndicated, isSectionVisible, isWarningVisible } = testHormoneTherapySection(false, false);
      expect(isHormoneIndicated).toBe(false);
      expect(isSectionVisible).toBe(false);
      expect(isWarningVisible).toBe(true);
    });

    it('shows hormone therapy section when ER is positive', () => {
      const { isHormoneIndicated, isSectionVisible, isWarningVisible } = testHormoneTherapySection(true, false);
      expect(isHormoneIndicated).toBe(true);
      expect(isSectionVisible).toBe(true);
      expect(isWarningVisible).toBe(false);
    });

    it('shows hormone therapy section when PR is positive', () => {
      const { isHormoneIndicated, isSectionVisible, isWarningVisible } = testHormoneTherapySection(false, true);
      expect(isHormoneIndicated).toBe(true);
      expect(isSectionVisible).toBe(true);
      expect(isWarningVisible).toBe(false);
    });

    it('shows hormone therapy section when both ER and PR are positive', () => {
      const { isHormoneIndicated, isSectionVisible, isWarningVisible } = testHormoneTherapySection(true, true);
      expect(isHormoneIndicated).toBe(true);
      expect(isSectionVisible).toBe(true);
      expect(isWarningVisible).toBe(false);
    });
  });

  describe('Chemotherapy Options Update', () => {
    it('updates chemotherapy options based on HER2 status', () => {
      const dom = new JSDOM(
        `<!doctype html><html><body>${buildBiomarkerFormHtml(false, false, false)}</body></html>`,
        { url: 'http://localhost' }
      );
      const context = createFormHandlerContext(dom);
      
      // Test HER2 negative options
      context.FormHandler.updateChemotherapyOptions();
      let selectElement = dom.window.document.getElementById('chemotherapyRegimen');
      let optionsCount = selectElement.options.length;
      
      expect(optionsCount).toBeGreaterThan(1); // At least placeholder + options
      
      // Now test with HER2 positive
      dom.window.document.getElementById('her2Status').checked = true;
      context.FormHandler.updateChemotherapyOptions();
      selectElement = dom.window.document.getElementById('chemotherapyRegimen');
      let newOptionsCount = selectElement.options.length;
      
      expect(newOptionsCount).toBeGreaterThan(1);
    });

    it('includes placeholder option in chemotherapy select', () => {
      const dom = new JSDOM(
        `<!doctype html><html><body>${buildBiomarkerFormHtml(false, false, false)}</body></html>`,
        { url: 'http://localhost' }
      );
      const context = createFormHandlerContext(dom);
      context.FormHandler.updateChemotherapyOptions();
      
      const selectElement = dom.window.document.getElementById('chemotherapyRegimen');
      const firstOption = selectElement.options[0];
      
      expect(firstOption.value).toBe('');
      expect(firstOption.textContent).toContain('Выберите режим химиотерапии');
    });
  });

  describe('Combined Biomarker Scenarios', () => {
    it('handles ER+/PR+/HER2- scenario correctly', () => {
      const { isTNBC } = testTNBCCalculation(true, true, false);
      const { isHormoneIndicated } = testHormoneTherapySection(true, true);
      
      expect(isTNBC).toBe(false);
      expect(isHormoneIndicated).toBe(true);
    });

    it('handles ER-/PR-/HER2+ scenario correctly', () => {
      const { isTNBC } = testTNBCCalculation(false, false, true);
      const { isHormoneIndicated } = testHormoneTherapySection(false, false);
      
      expect(isTNBC).toBe(false);
      expect(isHormoneIndicated).toBe(false);
    });

    it('handles ER+/PR-/HER2+ scenario correctly', () => {
      const { isTNBC } = testTNBCCalculation(true, false, true);
      const { isHormoneIndicated } = testHormoneTherapySection(true, false);
      
      expect(isTNBC).toBe(false);
      expect(isHormoneIndicated).toBe(true);
    });

    it('handles ER-/PR+/HER2- scenario correctly', () => {
      const { isTNBC } = testTNBCCalculation(false, true, false);
      const { isHormoneIndicated } = testHormoneTherapySection(false, true);
      
      expect(isTNBC).toBe(false);
      expect(isHormoneIndicated).toBe(true);
    });
  });
});

