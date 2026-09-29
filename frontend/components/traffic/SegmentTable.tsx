'use client';

import React, { useMemo } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  createColumnHelper,
} from '@tanstack/react-table';
import { SegmentTraffic } from '@/types/api';
import { useTrafficStore } from '@/stores/useTrafficStore';
import { getSpeedBadge } from '@/lib/utils';
import { MapPin, Navigation, Eye } from 'lucide-react';

const columnHelper = createColumnHelper<SegmentTraffic>();

export function SegmentTable() {
  const { segments, selectedSegmentId, selectSegment } = useTrafficStore();

  const columns = useMemo(
    () => [
      columnHelper.accessor('segment_name', {
        header: () => (
          <span className="font-heading uppercase tracking-wider text-xs font-bold text-navy-950">
            Highway Corridor
          </span>
        ),
        cell: (info) => (
          <div className="flex items-center gap-2">
            <MapPin className="w-3.5 h-3.5 text-saffron-600 shrink-0" />
            <div>
              <span className="font-sans text-xs font-bold text-navy-950 block">
                {info.getValue()}
              </span>
              <span className="font-mono text-[10px] text-slate-500 block">
                ID: {info.row.original.road_segment_id}
              </span>
            </div>
          </div>
        ),
      }),
      columnHelper.accessor('cameras', {
        header: () => (
          <span className="font-heading uppercase tracking-wider text-xs font-bold text-navy-950">
            Active Nodes
          </span>
        ),
        cell: (info) => (
          <span className="font-mono text-xs text-slate-600 bg-tint px-2 py-0.5 rounded border border-border-warm tabular-nums font-semibold">
            {info.getValue()?.length || 0} Cameras
          </span>
        ),
      }),
      columnHelper.accessor('total_vehicles', {
        header: () => (
          <span className="font-heading uppercase tracking-wider text-xs font-bold text-navy-950">
            Volume Flow
          </span>
        ),
        cell: (info) => (
          <span className="font-mono text-xs font-bold text-navy-950 tabular-nums">
            {info.getValue().toLocaleString()} / hr
          </span>
        ),
      }),
      columnHelper.accessor('avg_speed_kmh', {
        header: () => (
          <span className="font-heading uppercase tracking-wider text-xs font-bold text-navy-950">
            Avg Velocity
          </span>
        ),
        cell: (info) => {
          const speed = info.getValue();
          const badge = getSpeedBadge(speed);
          return (
            <div className="flex items-center gap-2">
              <span
                className={`px-2 py-0.5 rounded-[2px] border font-mono text-xs font-bold tabular-nums ${badge.bg} ${badge.text} ${badge.border}`}
              >
                {speed.toFixed(1)} km/h
              </span>
            </div>
          );
        },
      }),
      columnHelper.accessor('congestion_status', {
        header: () => (
          <span className="font-heading uppercase tracking-wider text-xs font-bold text-navy-950">
            Flow Status
          </span>
        ),
        cell: (info) => {
          const status = info.getValue();
          const styles = {
            fluid: 'bg-emerald-50 text-emerald-700 border-emerald-700/30',
            heavy: 'bg-saffron-50 text-saffron-700 border-saffron-600/30',
            gridlock: 'bg-crimson-50 text-crimson-700 border-crimson-700/30 animate-pulse',
          };
          return (
            <span
              className={`inline-block px-2 py-0.5 rounded-[2px] border font-mono text-[11px] font-bold uppercase tracking-wider tabular-nums ${styles[status]}`}
            >
              {status}
            </span>
          );
        },
      }),
      columnHelper.display({
        id: 'action',
        header: () => (
          <span className="font-heading uppercase tracking-wider text-xs font-bold text-navy-950 text-right block">
            Inspect
          </span>
        ),
        cell: ({ row }) => (
          <div className="text-right">
            <button
              onClick={() => selectSegment(row.original.road_segment_id)}
              className="p-1 rounded text-slate-500 hover:text-navy-900 hover:bg-tint"
              title="Focus corridor on heatmap"
            >
              <Eye className="w-3.5 h-3.5" />
            </button>
          </div>
        ),
      }),
    ],
    [selectSegment]
  );

  const table = useReactTable({
    data: segments,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <div className="bg-surface border border-border-warm rounded-[4px] overflow-hidden shadow-gov-sm flex flex-col">
      <div className="bg-tint border-b border-border-warm px-4 py-2.5 flex items-center justify-between">
        <h4 className="font-heading font-bold text-xs uppercase tracking-wider text-navy-950">
          Key Arterial Highway Corridors ({segments.length} Segments)
        </h4>
        <span className="font-mono text-[10px] text-slate-500 uppercase">
          TanStack Table v8 High-Density
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse">
          <thead>
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id} className="bg-porcelain border-b border-border-warm">
                {headerGroup.headers.map((header) => (
                  <th key={header.id} className="px-4 py-2.5 select-none">
                    {flexRender(header.column.columnDef.header, header.getContext())}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {table.getRowModel().rows.map((row) => {
              const isSelected = selectedSegmentId === row.original.road_segment_id;
              return (
                <tr
                  key={row.id}
                  onClick={() => selectSegment(row.original.road_segment_id)}
                  className={`border-b border-border-subtle cursor-pointer transition-colors ${
                    isSelected ? 'bg-saffron-50/60 font-semibold' : 'hover:bg-tint'
                  }`}
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-4 py-2.5">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
