import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { ScannerTab } from './components/ScannerTab';
import { ExperimentsTab } from './components/ExperimentsTab';
import { DatasetsTab } from './components/DatasetsTab';
import { MethodologyTab } from './components/MethodologyTab';
import { Footer } from './components/Footer';
import type { ModelDetails, SystemHealth } from './types/api';
import { ApiService } from './services/api';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'scanner' | 'experiments' | 'datasets' | 'methodology'>('scanner');
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [healthError, setHealthError] = useState<boolean>(false);
  const [models, setModels] = useState<ModelDetails[]>([]);
  const [defaultModelId, setDefaultModelId] = useState<string>('tfidf_logistic_regression');

  useEffect(() => {
    const initTelemetry = async () => {
      try {
        const healthData = await ApiService.getHealth();
        setHealth(healthData);
        setHealthError(false);
      } catch {
        setHealthError(true);
      }

      try {
        const modelsData = await ApiService.getModels();
        setModels(modelsData.models);
        if (modelsData.default_model) {
          setDefaultModelId(modelsData.default_model);
        }
      } catch {
        // Fallback placeholder models if backend is not yet started
        setModels([
          {
            id: 'tfidf_logistic_regression',
            name: 'TF-IDF + Logistic Regression',
            type: 'classical',
            description: 'TF-IDF n-gram vectorizer with balanced Logistic Regression.',
            status: 'ready',
            version: '1.0.0',
            training_dataset: 'Devign (Human-written C/C++)',
          },
          {
            id: 'tfidf_linear_svm',
            name: 'TF-IDF + Linear SVM',
            type: 'classical',
            description: 'TF-IDF n-gram vectorizer with balanced Linear SVM.',
            status: 'ready',
            version: '1.0.0',
            training_dataset: 'Devign (Human-written C/C++)',
          },
          {
            id: 'codebert',
            name: 'Microsoft CodeBERT (Fine-Tuned)',
            type: 'transformer',
            description: 'Contextual code representation model with binary classification head.',
            status: 'checkpoint_missing',
            version: '1.0.0',
            training_dataset: 'Devign / LLMVul',
          },
        ]);
      }
    };

    initTelemetry();
  }, []);

  return (
    <div className="min-h-screen bg-[#080d1a] text-slate-100 flex flex-col justify-between selection:bg-sky-500/30 selection:text-sky-200">
      <div>
        <Header
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          health={health}
          healthError={healthError}
        />

        <main className="max-w-7xl mx-auto px-4 lg:px-8 py-8">
          {activeTab === 'scanner' && (
            <ScannerTab models={models} defaultModelId={defaultModelId} />
          )}

          {activeTab === 'experiments' && <ExperimentsTab />}

          {activeTab === 'datasets' && <DatasetsTab />}

          {activeTab === 'methodology' && <MethodologyTab />}
        </main>
      </div>

      <Footer />
    </div>
  );
};

export default App;
