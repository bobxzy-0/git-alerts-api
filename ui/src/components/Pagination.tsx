import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';

type PaginationProps = { count: number; page: number; pageSize: number; onPageChange: (page: number) => void };

export const Pagination: React.FC<PaginationProps> = ({ count, page, pageSize, onPageChange }) => {
  const totalPages = Math.max(1, Math.ceil(count / pageSize));
  if (count <= pageSize) return null;
  const firstItem = (page - 1) * pageSize + 1;
  const lastItem = Math.min(page * pageSize, count);

  return <div className="flex flex-wrap items-center justify-between gap-3 border-t px-4 py-3 text-sm">
    <span className="text-muted-foreground">Showing {firstItem}–{lastItem} of {count}</span>
    <div className="flex items-center gap-2">
      <button type="button" onClick={() => onPageChange(page - 1)} disabled={page <= 1} className="inline-flex items-center gap-1 rounded-md border px-3 py-1.5 disabled:cursor-not-allowed disabled:opacity-50"><ChevronLeft className="h-4 w-4" /> Previous</button>
      <span className="min-w-24 text-center">Page {page} of {totalPages}</span>
      <button type="button" onClick={() => onPageChange(page + 1)} disabled={page >= totalPages} className="inline-flex items-center gap-1 rounded-md border px-3 py-1.5 disabled:cursor-not-allowed disabled:opacity-50">Next <ChevronRight className="h-4 w-4" /></button>
    </div>
  </div>;
};
