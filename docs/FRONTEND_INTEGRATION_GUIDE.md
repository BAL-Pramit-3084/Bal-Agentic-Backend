# Frontend Integration Guide: Chatbot Visualizations

## Overview

The BAL-Agentic-Backend chatbot API returns structured data for rendering charts and tables. This guide shows frontend developers how to integrate with the API using React and Recharts.

---

## API Response Format

### Endpoint
```
POST /api/v1/chat
```

### Request
```json
{
  "message": "Show me furnace production for today",
  "department": "furnace"
}
```

### Response Structure
```json
{
  "success": true,
  "response": "Here's the furnace production data for today...",
  "visualizations": [
    {
      "type": "BAR_CHART",
      "title": "Daily Production by Furnace",
      "description": "Production in MT for each furnace",
      "data": {
        "labels": ["F1", "F2", "F3", "F4"],
        "datasets": [
          {
            "label": "Production (MT)",
            "data": [245.5, 312.8, 189.2, 278.4],
            "color": "#3B82F6"
          }
        ]
      },
      "config": {
        "xAxisLabel": "Furnace",
        "yAxisLabel": "Production (MT)",
        "showLegend": false,
        "showValues": true
      }
    }
  ],
  "tool_calls": [...],
  "department": "furnace",
  "timestamp": "2025-12-09T10:30:00"
}
```

---

## Visualization Types

| Type | Use Case | Required Data |
|------|----------|---------------|
| `TABLE` | Raw data display | `columns`, `rows` |
| `BAR_CHART` | Category comparisons | `labels`, `datasets` |
| `LINE_CHART` | Trends over time | `labels`, `datasets` |
| `PIE_CHART` | Proportions | `labels`, `values`, `colors` |
| `DONUT_CHART` | Proportions with center | `labels`, `values`, `colors` |
| `AREA_CHART` | Cumulative trends | `labels`, `datasets` |

---

## Installation

```bash
npm install recharts
# or
yarn add recharts
```

---

## React Implementation

### 1. Chat Service (API Call)

```typescript
// services/chatService.ts
export interface Visualization {
  type: 'TABLE' | 'BAR_CHART' | 'LINE_CHART' | 'PIE_CHART' | 'DONUT_CHART' | 'AREA_CHART';
  title: string;
  description?: string;
  data: {
    // For TABLE
    columns?: string[];
    rows?: (string | number)[][];
    // For charts
    labels?: string[];
    datasets?: {
      label: string;
      data: number[];
      color: string;
    }[];
    // For pie/donut
    values?: number[];
    colors?: string[];
  };
  config?: {
    xAxisLabel?: string;
    yAxisLabel?: string;
    showLegend?: boolean;
    showValues?: boolean;
    stacked?: boolean;
  };
}

export interface ChatResponse {
  success: boolean;
  response: string;
  visualizations: Visualization[] | null;
  department: string;
  timestamp: string;
}

export async function sendChatMessage(message: string, department: string): Promise<ChatResponse> {
  const response = await fetch('/api/v1/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${getToken()}` // If using auth
    },
    body: JSON.stringify({ message, department })
  });

  return response.json();
}
```

### 2. Visualization Renderer Component

```tsx
// components/VisualizationRenderer.tsx
import React from 'react';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer
} from 'recharts';
import { Visualization } from '../services/chatService';

interface Props {
  visualization: Visualization;
}

export const VisualizationRenderer: React.FC<Props> = ({ visualization }) => {
  const { type, title, description, data, config } = visualization;

  // Render header
  const Header = () => (
    <div className="mb-4">
      <h3 className="text-lg font-semibold text-gray-800">{title}</h3>
      {description && <p className="text-sm text-gray-500">{description}</p>}
    </div>
  );

  // TABLE
  if (type === 'TABLE') {
    return (
      <div className="bg-white rounded-lg shadow p-4">
        <Header />
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                {data.columns?.map((col, i) => (
                  <th key={i} className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {data.rows?.map((row, i) => (
                <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                  {row.map((cell, j) => (
                    <td key={j} className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {cell}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  }

  // Transform data for Recharts
  const chartData = data.labels?.map((label, index) => {
    const point: any = { name: label };
    data.datasets?.forEach(dataset => {
      point[dataset.label] = dataset.data[index];
    });
    return point;
  });

  // BAR_CHART
  if (type === 'BAR_CHART') {
    return (
      <div className="bg-white rounded-lg shadow p-4">
        <Header />
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" label={{ value: config?.xAxisLabel, position: 'bottom' }} />
            <YAxis label={{ value: config?.yAxisLabel, angle: -90, position: 'insideLeft' }} />
            <Tooltip />
            {config?.showLegend && <Legend />}
            {data.datasets?.map((dataset, i) => (
              <Bar key={i} dataKey={dataset.label} fill={dataset.color} />
            ))}
          </BarChart>
        </ResponsiveContainer>
      </div>
    );
  }

  // LINE_CHART
  if (type === 'LINE_CHART') {
    return (
      <div className="bg-white rounded-lg shadow p-4">
        <Header />
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" label={{ value: config?.xAxisLabel, position: 'bottom' }} />
            <YAxis label={{ value: config?.yAxisLabel, angle: -90, position: 'insideLeft' }} />
            <Tooltip />
            {config?.showLegend && <Legend />}
            {data.datasets?.map((dataset, i) => (
              <Line
                key={i}
                type="monotone"
                dataKey={dataset.label}
                stroke={dataset.color}
                strokeWidth={2}
                dot={{ fill: dataset.color }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    );
  }

  // AREA_CHART
  if (type === 'AREA_CHART') {
    return (
      <div className="bg-white rounded-lg shadow p-4">
        <Header />
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            {config?.showLegend && <Legend />}
            {data.datasets?.map((dataset, i) => (
              <Area
                key={i}
                type="monotone"
                dataKey={dataset.label}
                fill={dataset.color}
                stroke={dataset.color}
                fillOpacity={0.3}
              />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      </div>
    );
  }

  // PIE_CHART / DONUT_CHART
  if (type === 'PIE_CHART' || type === 'DONUT_CHART') {
    const pieData = data.labels?.map((label, index) => ({
      name: label,
      value: data.values?.[index] || 0,
      color: data.colors?.[index] || '#8884d8'
    }));

    return (
      <div className="bg-white rounded-lg shadow p-4">
        <Header />
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={pieData}
              cx="50%"
              cy="50%"
              innerRadius={type === 'DONUT_CHART' ? 60 : 0}
              outerRadius={100}
              paddingAngle={2}
              dataKey="value"
              label={config?.showValues ? ({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%` : false}
            >
              {pieData?.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip />
            {config?.showLegend && <Legend />}
          </PieChart>
        </ResponsiveContainer>
      </div>
    );
  }

  return <div>Unsupported visualization type: {type}</div>;
};
```

### 3. Chat Component with Visualizations

```tsx
// components/ChatWindow.tsx
import React, { useState } from 'react';
import { sendChatMessage, ChatResponse, Visualization } from '../services/chatService';
import { VisualizationRenderer } from './VisualizationRenderer';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  visualizations?: Visualization[];
}

export const ChatWindow: React.FC<{ department: string }> = ({ department }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await sendChatMessage(input, department);

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.response,
        visualizations: response.visualizations || undefined
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Sorry, an error occurred. Please try again.'
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, index) => (
          <div key={index} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-3xl ${msg.role === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-100'} rounded-lg p-4`}>
              {/* Text Response */}
              <p className="whitespace-pre-wrap">{msg.content}</p>

              {/* Visualizations */}
              {msg.visualizations && msg.visualizations.length > 0 && (
                <div className="mt-4 space-y-4">
                  {msg.visualizations.map((viz, vizIndex) => (
                    <VisualizationRenderer key={vizIndex} visualization={viz} />
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg p-4">
              <div className="animate-pulse">Thinking...</div>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t p-4">
        <div className="flex space-x-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
            placeholder="Ask about your data..."
            className="flex-1 border rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleSend}
            disabled={loading}
            className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 disabled:opacity-50"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
};
```

---

## Example Queries & Expected Outputs

### Query 1: Category Comparison
**User:** "Show me production by furnace for today"

**Expected Visualization:**
```json
{
  "type": "BAR_CHART",
  "title": "Daily Production by Furnace",
  "data": {
    "labels": ["Furnace 1", "Furnace 2", "Furnace 3"],
    "datasets": [{
      "label": "Production (MT)",
      "data": [245, 312, 189],
      "color": "#3B82F6"
    }]
  }
}
```

### Query 2: Trend Over Time
**User:** "Show me weekly food waste trend"

**Expected Visualization:**
```json
{
  "type": "LINE_CHART",
  "title": "Weekly Food Waste Trend",
  "data": {
    "labels": ["Mon", "Tue", "Wed", "Thu", "Fri"],
    "datasets": [{
      "label": "Waste (kg)",
      "data": [12, 15, 10, 18, 14],
      "color": "#10B981"
    }]
  }
}
```

### Query 3: Distribution
**User:** "Show waste distribution by type"

**Expected Visualization:**
```json
{
  "type": "PIE_CHART",
  "title": "Waste Distribution",
  "data": {
    "labels": ["Food", "Paper", "Plastic"],
    "values": [45, 30, 25],
    "colors": ["#3B82F6", "#10B981", "#F59E0B"]
  }
}
```

### Query 4: Tabular Data
**User:** "List all food waste entries for this week"

**Expected Visualization:**
```json
{
  "type": "TABLE",
  "title": "Food Waste Records",
  "data": {
    "columns": ["Date", "Location", "Waste (kg)", "Status"],
    "rows": [
      ["2025-12-01", "Canteen A", 12.5, "Normal"],
      ["2025-12-02", "Canteen A", 15.2, "High"]
    ]
  }
}
```

---

## Styling Tips

### Default Color Palette
```typescript
const COLORS = {
  blue: '#3B82F6',
  green: '#10B981',
  yellow: '#F59E0B',
  red: '#EF4444',
  purple: '#8B5CF6',
  pink: '#EC4899',
  cyan: '#06B6D4',
  orange: '#F97316'
};
```

### Responsive Design
```tsx
// Always wrap charts in ResponsiveContainer
<ResponsiveContainer width="100%" height={300}>
  <BarChart data={data}>
    ...
  </BarChart>
</ResponsiveContainer>
```

---

## Error Handling

```typescript
// Handle cases where visualization data is malformed
const renderVisualization = (viz: Visualization) => {
  try {
    // Validate required fields
    if (!viz.type || !viz.data) {
      console.warn('Invalid visualization data:', viz);
      return <div>Unable to render visualization</div>;
    }

    return <VisualizationRenderer visualization={viz} />;
  } catch (error) {
    console.error('Visualization render error:', error);
    return <div>Error rendering chart</div>;
  }
};
```

---

## Alternative: Using Chart.js

If you prefer Chart.js over Recharts:

```bash
npm install react-chartjs-2 chart.js
```

```tsx
import { Bar, Line, Pie, Doughnut } from 'react-chartjs-2';

// Transform API data to Chart.js format
const toChartJsData = (visualization: Visualization) => ({
  labels: visualization.data.labels,
  datasets: visualization.data.datasets?.map(ds => ({
    label: ds.label,
    data: ds.data,
    backgroundColor: ds.color,
    borderColor: ds.color
  })) || []
});
```

---

## Support

For questions about the API response format, contact the backend team.

For visualization rendering issues, refer to:
- [Recharts Documentation](https://recharts.org/)
- [Chart.js Documentation](https://www.chartjs.org/)
