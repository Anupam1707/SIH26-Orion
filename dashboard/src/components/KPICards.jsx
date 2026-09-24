import React from 'react';
import { Users, AlertOctagon, TrendingUp, GitMerge, FileCheck } from 'lucide-react';

export default function KPICards({ metadata }) {
  const cards = [
    {
      title: 'Monitored Entities',
      value: metadata?.total_entities_monitored ? metadata.total_entities_monitored.toLocaleString() : '4,312',
      subtitle: 'Persons, Accounts & Phones',
      icon: Users,
      color: 'from-blue-500/20 to-indigo-500/20 text-sky-400 border-sky-500/30'
    },
    {
      title: 'Active Typologies',
      value: metadata?.ground_truth_typologies_count || '8 Planted',
      subtitle: 'Mule, Scatter, Structuring, Bursts',
      icon: AlertOctagon,
      color: 'from-rose-500/20 to-red-500/20 text-rose-400 border-rose-500/30'
    },
    {
      title: 'OddBall Anomaly (A00055)',
      value: 'Top 1.1%',
      subtitle: 'Rank 6/532 · Unsupervised Scatter',
      icon: TrendingUp,
      color: 'from-amber-500/20 to-yellow-500/20 text-amber-400 border-amber-500/30'
    },
    {
      title: 'Link Prediction Precision',
      value: '196 / 200',
      subtitle: '98% Intra-Syndicate Tie Recovery',
      icon: GitMerge,
      color: 'from-purple-500/20 to-violet-500/20 text-purple-400 border-purple-500/30'
    },
    {
      title: 'Evidentiary Compliance',
      value: 'Section 63 BSA',
      subtitle: 'Cryptographic Chain of Custody',
      icon: FileCheck,
      color: 'from-emerald-500/20 to-teal-500/20 text-emerald-400 border-emerald-500/30'
    }
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-3 p-4 bg-[#0a0e1a]/80 border-b border-slate-800">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className={`p-3 rounded-xl bg-gradient-to-br ${card.color} border backdrop-blur-sm flex flex-col justify-between transition-all hover:scale-[1.02]`}
          >
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[11px] font-semibold text-slate-300 uppercase tracking-wider">
                {card.title}
              </span>
              <Icon className="w-4 h-4 opacity-80" />
            </div>
            <div>
              <div className="text-xl font-extrabold text-white tracking-tight mono">
                {card.value}
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5 font-medium truncate">
                {card.subtitle}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
