import React from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Monitoring } from '@/pages/Monitoring';
import { Scans } from '@/pages/Scans';
import { LiveIndicator } from '@/components/LiveIndicator';

export const ScanWorkspace: React.FC = () => {
  const [params, setParams] = useSearchParams();
  const tab = params.get('tab') === 'history' ? 'history' : 'monitors';
  const select = (next: string) => {
    const updated = new URLSearchParams(params);
    updated.set('tab', next);
    setParams(updated);
  };

  return <div className="space-y-6">
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div className="flex items-center gap-3"><p className="text-sm text-muted-foreground">Manage monitoring plans and every execution record in one place.</p><LiveIndicator /></div>
      <Link to="/scans/new" className="rounded-lg bg-primary px-4 py-2 font-medium text-primary-foreground">New Scan</Link>
    </div>
    <div className="flex gap-1 border-b">
      <button onClick={() => select('monitors')} className={`px-5 py-3 text-sm font-medium ${tab === 'monitors' ? 'border-b-2 border-primary text-primary' : 'text-muted-foreground'}`}>Monitoring Plans</button>
      <button onClick={() => select('history')} className={`px-5 py-3 text-sm font-medium ${tab === 'history' ? 'border-b-2 border-primary text-primary' : 'text-muted-foreground'}`}>Task History</button>
    </div>
    {tab === 'monitors' ? <Monitoring embedded /> : <Scans embedded />}
  </div>;
};
