import React from 'react';
import { Users, AlertOctagon, TrendingUp, GitMerge, FileCheck } from 'lucide-react';

export default function KPICards({ metadata }) {
  const cards = [
    {
      title: 'Monitored Entities',
      value: metadata?.total_entities_monitored ? metadata.total_entities_monitored.toLocaleString() : '4,312',
      subtitle: 'Persons, Accounts & Phones',
      icon: Users,
      valueColor: 'text-slate-100'
    },
    {
      title: 'Active Typologies',
      value: metadata?.ground_truth_typologies_count || '8 Typologies',
      subtitle: 'Mule, Scatter, Structuring, Bursts',
      icon: AlertOctagon,
      valueColor: 'text-rose-400'
    },
    {
      title: 'OddBall Anomaly (A00055)',
      value: 'Top 1.1%',
      subtitle: 'Rank 6/532 · Scatter Hub',
      icon: TrendingUp,
      valueColor: 'text-amber-400'
    },
    {
      title: 'Link Prediction',
      value: '196 / 200',
      subtitle: '98% Intra-Syndicate Recovery',
      icon: GitMerge,
      valueColor: 'text-blue-400'
    },
    {
      title: 'Legal Admissibility',
      value: 'Section 63 BSA',
      subtitle: 'Digital Chain of Custody',
      icon: FileCheck,
      valueColor: 'text-emerald-400'
    }
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-3 px-6 py-3 bg-[#0a0f1d] border-b border-slate-800">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className="p-3 rounded-lg bg-slate-900/90 border border-slate-800/80 flex flex-col justify-between"
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
                {card.title}
              </span>
              <Icon className="w-3.5 h-3.5 text-slate-500" />
            </div>
            <div>
              <div className={`text-lg font-bold tracking-tight font-mono ${card.valueColor}`}>
                {card.value}
              </div>
              <div className="text-[10px] text-slate-400 mt-0.5 truncate">
                {card.subtitle}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
