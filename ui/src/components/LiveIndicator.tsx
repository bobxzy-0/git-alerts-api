import React from 'react';

export const LiveIndicator: React.FC<{ intervalSeconds?: number }> = ({ intervalSeconds = 5 }) => (
  <span className="inline-flex items-center gap-2 rounded-full border bg-card px-3 py-1 text-xs text-muted-foreground" title={`Refreshes every ${intervalSeconds} seconds while visible`}>
    <span className="relative flex h-2 w-2"><span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60"/><span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500"/></span>
    Live · {intervalSeconds}s
  </span>
);
