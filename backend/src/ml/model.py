from pathlib import Path
import pandas as pd
import pickle
import json

### послание от бекендера: заберите у мльщика курсор

class CoxModelPredictor:
    """Класс для предсказания выживаемости пациентов с раком груди"""
    
    def __init__(self, models_dir: str = "cox_models"):
        """
        Args:
            models_dir: путь к директории с сохраненными моделями
        """
        self.models_dir = Path(models_dir)
        self.label_encoders = None
        self.cox_models = {}
        self.metadata = None
        
        self._load_components()
    
    def _load_components(self):
        """Загружает все сохраненные компоненты"""
        encoders_path = self.models_dir / "label_encoders.pkl"
        with open(encoders_path, 'rb') as f:
            self.label_encoders = pickle.load(f)
        print(f"✓ Загружено {len(self.label_encoders)} label encoders")
        
        metadata_path = self.models_dir / "models_metadata.json"
        with open(metadata_path, 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)
        print(f"✓ Загружены метаданные для {len(self.metadata)} стадий")
        
        for stage in [1, 2, 3, 4]:
            model_path = self.models_dir / f"cox_model_stage_{stage}.pkl"
            with open(model_path, 'rb') as f:
                self.cox_models[stage] = pickle.load(f)
            print(f"✓ Загружена модель для стадии {stage}")
    
    def preprocess_data(self, patient_data: dict) -> pd.DataFrame:
        """
        Препроцессинг данных пациента
        
        Args:
            patient_data: словарь с данными пациента
            
        Returns:
            DataFrame с закодированными признаками
        """
        df = pd.DataFrame([patient_data])
        
        for col, encoder in self.label_encoders.items():
            if col in df.columns:
                df[col] = df[col].fillna("Unknown")
                
                if df[col].iloc[0] not in encoder.classes_:
                    print(f"⚠️  Неизвестное значение '{df[col].iloc[0]}' для {col}, используем '{encoder.classes_[0]}'")
                    df[col] = encoder.classes_[0]
                
                df[col] = encoder.transform(df[col])
        
        return df
    
    def predict(self, patient_data: dict, stage: int) -> dict:
        """
        Предсказание выживаемости для пациента
        
        Args:
            patient_data: словарь с данными пациента (исходные данные)
            stage: стадия рака (1, 2, 3 или 4)
            
        Returns:
            Словарь с предсказаниями и метаданными
        """
        if stage not in [1, 2, 3, 4]:
            raise ValueError(f"Stage должна быть 1, 2, 3 или 4. Получено: {stage}")
        
        processed_data = self.preprocess_data(patient_data)
        
        model = self.cox_models[stage]
        
        required_features = self.metadata[f'stage_{stage}']['feature_columns']
        
        X = processed_data[required_features]
        
        predicted_survival = model.predict_expectation(X).values[0]
        partial_hazard = model.predict_partial_hazard(X).values[0]
        
        return {
            'predicted_survival_months': float(predicted_survival),
            'predicted_survival_years': float(predicted_survival / 12),
            'partial_hazard': float(partial_hazard),
            'stage': stage,
            'model_c_index': self.metadata[f'stage_{stage}']['c_index'],
            'model_mae': self.metadata[f'stage_{stage}']['mae']
        }

predictor = CoxModelPredictor(models_dir="src/ml/cox_models")

