import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { CategoryStat } from '@/types';

interface CategoryPieChartProps {
  data: CategoryStat[];
}

const COLORS = [
  '#22c55e', '#16a34a', '#15803d', '#166534', '#14532d',
  '#4ade80', '#86efac', '#bbf7d0', '#dcfce7', '#f0fdf4',
];

export const CategoryPieChart = ({ data }: CategoryPieChartProps) => {
  if (!data || data.length === 0) {
    return (
      <div className="card h-80 flex items-center justify-center">
        <p className="text-gray-500">No expense data for this period</p>
      </div>
    );
  }

  const chartData = data.map((item) => ({
    name: item.category,
    value: Number(item.amount),
  }));

  return (
    <div className="card">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">
        Expenses by Category
      </h3>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {chartData.map((_entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip 
              formatter={(value: number) => [`$${value.toFixed(2)}`, 'Amount']}
            />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};
