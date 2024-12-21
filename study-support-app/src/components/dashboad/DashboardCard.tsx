import React from 'react';
import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

interface DashboardCardProps {
  title: string;
  description: string;
  icon: LucideIcon;
  href: string;
  stats: string;
}

const DashboardCard: React.FC<DashboardCardProps> = ({
  title,
  description,
  icon: Icon,
  href,
  stats
}) => {
  return (
    <Link href={href}>
      <div className="h-full p-6 bg-white rounded-lg shadow-sm border border-gray-100 
                    transition-all duration-200 hover:shadow-md">
        <div className="flex items-center justify-between">
          <Icon className="h-8 w-8 text-blue-500" />
          <ArrowRight className="h-5 w-5 text-gray-400" />
        </div>
        <h3 className="mt-4 text-lg font-semibold text-gray-900">{title}</h3>
        <p className="mt-2 text-sm text-gray-600">{description}</p>
        <div className="mt-4 inline-flex items-center px-2.5 py-0.5 rounded-full 
                      text-xs font-medium bg-blue-100 text-blue-800">
          {stats}
        </div>
      </div>
    </Link>
  );
};

export default DashboardCard;