import React from 'react';

export const LiveIndicator: React.FC<{ intervalSeconds?: number }> = ({ intervalSeconds = 5 }) => (
  <span className="inline-flex items-center gap-2 rounded-full border bg-card px-3 py-1 text-xs text-muted-foreground" title={`前台每 ${intervalSeconds} 秒自动刷新，切回页面时立即刷新`}>
    <span className="relative flex h-2 w-2"><span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60"/><span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500"/></span>
    实时更新 · {intervalSeconds}s
  </span>
);
