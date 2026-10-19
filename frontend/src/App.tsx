import React from 'react';
import { Routes, Route } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import { Overview } from '@/pages/Overview';
import { ScenariosPlaceholder } from '@/pages/ScenariosPlaceholder';
import { RunsPlaceholder } from '@/pages/RunsPlaceholder';
import { DocsPlaceholder } from '@/pages/DocsPlaceholder';
import { NotFound } from '@/pages/NotFound';

export const App: React.FC = () => {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Overview />} />
        <Route path="/scenarios" element={<ScenariosPlaceholder />} />
        <Route path="/runs" element={<RunsPlaceholder />} />
        <Route path="/docs" element={<DocsPlaceholder />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Layout>
  );
};

export default App;
