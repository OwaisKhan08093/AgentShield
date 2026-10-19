import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import { Overview } from '@/pages/Overview';
import { Scenarios } from '@/pages/Scenarios';
import { ScenarioDetail } from '@/pages/ScenarioDetail';
import { RunsPlaceholder } from '@/pages/RunsPlaceholder';
import { DocsPlaceholder } from '@/pages/DocsPlaceholder';
import { NotFound } from '@/pages/NotFound';

export const App: React.FC = () => {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Overview />} />
        <Route path="/scenarios" element={<Scenarios />} />
        <Route path="/scenarios/:scenarioId" element={<ScenarioDetail />} />
        <Route path="/runs" element={<RunsPlaceholder />} />
        <Route path="/docs" element={<DocsPlaceholder />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Layout>
  );
};

export default App;
