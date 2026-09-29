'use client';

import React, { useMemo, useState } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  flexRender,
  createColumnHelper,
} from '@tanstack/react-table';
import { Camera } from '@/types/api';
import { useCameraStore } from '@/stores/useCameraStore';
import { Camera as CameraIcon, MapPin, Radio, Search, Plus } from 'lucide-react';

const columnHelper = createColumnHelper<Camera>();

interface CameraGridTableProps {
  onOpenAddModal: () => void;
}

export function CameraGridTable({ onOpenAddModal }: CameraGridTableProps) {
  const { cameras, selectedCamera, selectCamera } = useCameraStore();
  const [filterText, setFilterText] = useState('');

  const filteredCameras = useMemo(() => {
    if (!filterText.trim()) return cameras;
    const lower = filterText.toLowerCase();
    return cameras.filter(
      (c) =>
        c.id.toLowerCase().includes(lower) ||
        c.name.toLowerCase().includes(lower) ||
        (c.location_label && c.location_label.toLowerCase().includes(lower))
    );
  }, [cameras, filterText]);

  const columns = useMemo(
    () => [
      columnHelper.accessor('id', {
        header: () => (
          <span className="font-heading uppercase tracking-wider text-xs font-bold text-navy-950">
            Node ID
          </span>
        ),
        cell: (info) => (
          <span className="font-mono text-xs font-bold text-navy-950 bg-tint px-2 py-0.5 rounded border border-border-warm">
            {info.getValue()}
          </span>
        ),
      }),
      columnHelper.accessor('name', {
        header: () => (
          <span className="font-heading uppercase tracking-wider text-xs font-bold text-navy-950">
            Node Gantry & Corridor Name
          </span>
        ),
        cell: (info) => (
          <div>
            <span className="font-sans text-xs font-bold text-navy-950 block">
              {info.getValue()}
            </span>
            <span className="text-[11px] text-slate-500 font-mono">
              {info.row.original.location_label || 'Highway Node'}
            </span>
          </div>
        ),
      }),
      columnHelper.display({
        id: 'coordinates',
        header: () => (
          <span className="font-heading uppercase tracking-wider text-xs font-bold text-navy-950">
            WGS84 Coordinates
          </span>
        ),
        cell: ({ row }) => (
          <span className="font-mono text-xs text-slate-600 tabular-nums">
            {row.original.latitude.toFixed(4)}° N, {row.original.longitude.toFixed(4)}° E
          </span>
        ),
      }),
      columnHelper.accessor('road_segment_id', {
        header: () => (
          <span className="font-heading uppercase tracking-wider text-xs font-bold text-navy-950">
            Highway Segment
          </span>
        ),
        cell: (info) => (
          <span className="font-mono text-xs text-slate-700">
            {info.getValue() || 'Unassigned'}
          </span>
        ),
      }),
      columnHelper.accessor('is_active', {
        header: () => (
          <span className="font-heading uppercase tracking-wider text-xs font-bold text-navy-950">
            Telemetry Status
          </span>
        ),
        cell: (info) => {
          const active = info.getValue();
          return (
            <span
              className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-[2px] border font-mono text-[11px] font-bold uppercase tracking-wider ${
                active
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-700/30'
                  : 'bg-crimson-50 text-crimson-700 border-crimson-700/30'
              }`}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  active ? 'bg-emerald-600 animate-pulse' : 'bg-crimson-700'
                }`}
              />
              {active ? 'ONLINE 1080P' : 'OFFLINE'}
            </span>
          );
        },
      }),
    ],
    []
  );

  const table = useReactTable({
    data: filteredCameras,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  return (
    <div className="bg-surface border border-border-warm rounded-[4px] overflow-hidden shadow-gov-sm flex flex-col">
      <div className="bg-tint border-b border-border-warm px-4 py-2.5 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <CameraIcon className="w-4 h-4 text-navy-900" />
          <h4 className="font-heading font-bold text-xs uppercase tracking-wider text-navy-950">
            Registered ANPR Camera Nodes ({cameras.length} Active Gantries)
          </h4>
        </div>

        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              value={filterText}
              onChange={(e) => setFilterText(e.target.value)}
              placeholder="Filter camera nodes..."
              className="pl-8 pr-3 py-1 bg-surface border border-border-warm rounded-[3px] text-xs font-mono placeholder:text-slate-400 focus:outline-none focus:border-navy-900"
            />
          </div>

          <button
            onClick={onOpenAddModal}
            className="inline-flex items-center gap-1.5 px-3 py-1 bg-navy-900 hover:bg-navy-950 text-white rounded-[3px] font-heading font-bold text-xs uppercase tracking-wider shadow-sm transition-colors"
          >
            <Plus className="w-3.5 h-3.5 text-saffron-500" />
            <span>ADD CAMERA NODE</span>
          </button>
        </div>
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
              const isSelected = selectedCamera?.id === row.original.id;
              return (
                <tr
                  key={row.id}
                  onClick={() => selectCamera(row.original)}
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
