'use client';

import React, { useMemo, useState } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  flexRender,
  createColumnHelper,
  SortingState,
} from '@tanstack/react-table';
import { VehicleObservation } from '@/types/api';
import { useVehicleStore } from '@/stores/useVehicleStore';
import { HsrpPlate } from '@/components/ui/HsrpPlate';
import { formatIST, getSpeedBadge, getConfidenceBadge } from '@/lib/utils';
import {
  ArrowUpDown,
  Eye,
  Crosshair,
  Camera,
  Layers,
} from 'lucide-react';

const columnHelper = createColumnHelper<VehicleObservation>();

export function HistoryTable() {
  const { history, selectedObservation, selectObservation } = useVehicleStore();
  const [sorting, setSorting] = useState<SortingState>([
    { id: 'observed_at', desc: true },
  ]);

  const columns = useMemo(
    () => [
      columnHelper.accessor('observed_at', {
        header: ({ column }) => (
          <button
            onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
            className="flex items-center gap-1.5 font-heading uppercase tracking-wider text-xs font-bold text-navy-950"
          >
            <span>Time (IST)</span>
            <ArrowUpDown className="w-3 h-3 text-slate-400" />
          </button>
        ),
        cell: (info) => (
          <span className="font-mono text-xs font-semibold text-slate-700 tabular-nums">
            {formatIST(info.getValue())}
          </span>
        ),
      }),
      columnHelper.accessor('camera_name', {
        header: () => (
          <span className="font-heading uppercase tracking-wider text-xs font-bold text-navy-950">
            Camera Node
          </span>
        ),
        cell: (info) => (
          <div className="flex items-center gap-2">
            <Camera className="w-3.5 h-3.5 text-slate-400 shrink-0" />
            <div>
              <span className="font-mono text-xs font-bold text-navy-950 block">
                {info.row.original.camera_id}
              </span>
              <span className="text-[11px] text-slate-500 truncate max-w-[200px] block">
                {info.getValue() || 'Corridor Junction'}
              </span>
            </div>
          </div>
        ),
      }),
      columnHelper.accessor('plate_text', {
        header: () => (
          <span className="font-heading uppercase tracking-wider text-xs font-bold text-navy-950">
            Detected Plate
          </span>
        ),
        cell: (info) => <HsrpPlate plateText={info.getValue()} size="sm" />,
      }),
      columnHelper.accessor('confidence', {
        header: () => (
          <span className="font-heading uppercase tracking-wider text-xs font-bold text-navy-950">
            OCR Confidence
          </span>
        ),
        cell: (info) => {
          const badge = getConfidenceBadge(info.getValue());
          return (
            <div className="flex items-center gap-2 min-w-[90px]">
              <div className="w-12 bg-border-subtle rounded-full h-1.5 overflow-hidden">
                <div
                  className={`h-full ${badge.barColor}`}
                  style={{ width: `${badge.pct}%` }}
                />
              </div>
              <span className={`font-mono text-xs font-bold tabular-nums ${badge.textColor}`}>
                {badge.label}
              </span>
            </div>
          );
        },
      }),
      columnHelper.accessor('speed_kmh', {
        header: () => (
          <span className="font-heading uppercase tracking-wider text-xs font-bold text-navy-950">
            Velocity
          </span>
        ),
        cell: (info) => {
          const speed = info.getValue();
          const badge = getSpeedBadge(speed);
          return (
            <span
              className={`inline-block px-2 py-0.5 rounded-[2px] border font-mono text-xs font-bold tabular-nums ${badge.bg} ${badge.text} ${badge.border}`}
            >
              {badge.label}
            </span>
          );
        },
      }),
      columnHelper.display({
        id: 'actions',
        header: () => (
          <span className="font-heading uppercase tracking-wider text-xs font-bold text-navy-950 text-right block">
            Actions
          </span>
        ),
        cell: ({ row }) => {
          const isSelected = selectedObservation?.id === row.original.id;
          return (
            <div className="flex items-center justify-end gap-1.5">
              <button
                onClick={() => selectObservation(row.original)}
                className={`p-1.5 rounded-[2px] border transition-colors ${
                  isSelected
                    ? 'bg-navy-900 text-white border-navy-950'
                    : 'text-slate-600 bg-porcelain border-border-warm hover:bg-tint hover:text-navy-900'
                }`}
                title="Inspect in CCTV HUD & Map"
              >
                <Crosshair className="w-3.5 h-3.5" />
              </button>
            </div>
          );
        },
      }),
    ],
    [selectedObservation, selectObservation]
  );

  const table = useReactTable({
    data: history,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  return (
    <div className="bg-surface border border-border-warm rounded-[4px] overflow-hidden shadow-gov-sm flex flex-col">
      <div className="bg-tint border-b border-border-warm px-4 py-2.5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-navy-900" />
          <h4 className="font-heading font-bold text-xs uppercase tracking-wider text-navy-950">
            Chronological Multi-Camera Sightings ({history.length} Records)
          </h4>
        </div>
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
            {table.getRowModel().rows.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="text-center py-6 text-slate-400 font-mono text-xs">
                  NO MULTI-CAMERA SIGHTINGS FOUND
                </td>
              </tr>
            ) : (
              table.getRowModel().rows.map((row) => {
                const isSelected = selectedObservation?.id === row.original.id;
                return (
                  <tr
                    key={row.id}
                    onClick={() => selectObservation(row.original)}
                    className={`border-b border-border-subtle cursor-pointer transition-colors ${
                      isSelected
                        ? 'bg-saffron-50/60 font-semibold'
                        : 'hover:bg-tint'
                    }`}
                  >
                    {row.getVisibleCells().map((cell) => (
                      <td key={cell.id} className="px-4 py-2.5">
                        {flexRender(cell.column.columnDef.cell, cell.getContext())}
                      </td>
                    ))}
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
