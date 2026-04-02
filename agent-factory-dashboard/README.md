# Mosaic Dashboard - Agent Factory

A clean, data-focused analytics dashboard for Digital FTEs (Full-Time Equivalents) built with Next.js 16 and React 19.

**Design Inspiration**: Professional analytics dashboards with emphasis on typography, data visualization, and clear information hierarchy.

## ✨ Design Philosophy

### Core Principles
- **Typography First** - Clear font hierarchy with Inter font family
- **Data Visualization** - Professional charts with clean grids and tooltips
- **Color Consistency** - Blue primary, semantic colors for status
- **White Space** - Generous padding for readability
- **Subtle Borders** - Light borders for structure without visual noise

### Color Palette

| Color | Usage | Hex |
|-------|-------|-----|
| Blue 600 | Primary actions, links | #2563eb |
| Slate 900 | Primary text | #0f172a |
| Slate 600 | Secondary text | #475569 |
| Slate 500 | Muted text | #64748b |
| Green 600 | Success states | #059669 |
| Yellow 600 | Warning states | #d97706 |
| Red 600 | Error states | #dc2626 |

### Typography Scale

| Element | Size | Weight | Line Height |
|---------|------|--------|-------------|
| H1 | 1.875rem (30px) | 600 | 1.3 |
| H2 | 1.5rem (24px) | 600 | 1.3 |
| H3 | 1.25rem (20px) | 600 | 1.4 |
| Body | 1rem (16px) | 400 | 1.6 |
| Small | 0.875rem (14px) | 400/500 | 1.5 |
| Tiny | 0.75rem (12px) | 400/500 | 1.4 |

## 🎨 Features

### Data Visualization
- **Area Charts** - Conversation trends with gradient fills
- **Line Charts** - Performance metrics over time
- **Bar Charts** - Channel distribution
- **Pie/Donut Charts** - Status distribution
- **Custom Tooltips** - Clean, shadowed tooltips

### Components
- **Stat Cards** - Value-focused with trend indicators
- **Data Tables** - Clean rows with hover states
- **Status Badges** - Color-coded semantic indicators
- **Sidebar Navigation** - Clean, organized navigation
- **Header Bar** - Search, notifications, user profile

### UX Features
- **Auto-refresh** - Every 30 seconds
- **Connection Status** - Visual indicators
- **Error Recovery** - One-click retry
- **Loading States** - Skeleton screens
- **Responsive Grid** - Adapts to screen size

## 🛠 Tech Stack

- **Framework**: Next.js 16.1.6
- **React**: 19.2.3
- **TypeScript**: 5.x
- **Styling**: Tailwind CSS v4
- **Charts**: Recharts
- **Icons**: Lucide React
- **Font**: Inter (Google Fonts)

## 🚀 Getting Started

### Prerequisites

- Node.js 20+
- npm or yarn
- Backend API running at `http://localhost:8000`

### Installation

1. **Install dependencies:**
```bash
npm install
```

2. **Configure environment:**
```bash
# Create .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

3. **Run development server:**
```bash
npm run dev
```

4. **Open in browser:**
```
http://localhost:3000
```

## 📁 Project Structure

```
agent-factory-dashboard/
├── app/
│   ├── layout.tsx           # Root layout with Sidebar
│   ├── page.tsx             # Main dashboard
│   └── globals.css          # Mosaic design system
├── components/
│   ├── Sidebar.tsx          # Navigation sidebar
│   ├── Header.tsx           # Top header
│   ├── MetricsOverview.tsx  # Stat cards
│   ├── ChartsSection.tsx    # Charts (Area, Line, Bar, Pie)
│   ├── RecentTickets.tsx    # Data table
│   ├── SLABreachesPanel.tsx # Alert panel
│   ├── FTEInstancesPanel.tsx# Status panel
│   └── ErrorBanner.tsx      # Error states
├── contexts/
│   └── DashboardContext.tsx # Global state
└── types/
    └── index.ts             # TypeScript types
```

## 📊 Chart Specifications

### Area Chart (Conversations Trend)
- Gradient fill opacity: 0.1 → 0
- Stroke width: 2px
- Colors: Blue (#2563eb), Green (#059669)
- Grid: Dashed horizontal lines

### Line Chart (Performance)
- No dots on line
- Stroke width: 2px
- Colors: Amber (#d97706), Red (#dc2626)

### Bar Chart (Channels)
- Border radius: 4px top corners
- Max bar width: 60px
- Fill: Blue (#2563eb)

### Donut Chart (Status)
- Inner radius: 80px
- Outer radius: 110px
- Padding angle: 2 degrees
- Stroke: White 2px

## 🎯 Design Tokens

### Border Radius
```css
--radius-sm: 0.375rem (6px)
--radius: 0.5rem (8px)
--radius-lg: 0.75rem (12px)
--radius-xl: 1rem (16px)
```

### Shadows
```css
--shadow-sm: 0 1px 3px rgba(0,0,0,0.1)
--shadow-md: 0 4px 6px rgba(0,0,0,0.1)
--shadow-lg: 0 10px 15px rgba(0,0,0,0.1)
--shadow-xl: 0 20px 25px rgba(0,0,0,0.1)
```

### Spacing Scale
- Base: 0.25rem (4px)
- Components: 0.5rem, 1rem, 1.5rem, 2rem
- Sections: 3rem, 4rem, 6rem

## 📱 Responsive Breakpoints

| Breakpoint | Min Width | Layout |
|------------|-----------|--------|
| Mobile | < 768px | Single column |
| Tablet | 768px - 1024px | 2 column grid |
| Desktop | > 1024px | 3 column grid |

## 🔧 Customization

### Change Primary Color

Edit `app/globals.css`:
```css
:root {
  --primary-600: #2563eb; /* Change to your color */
}
```

### Modify Chart Colors

Edit chart components:
```typescript
const COLORS = ['#2563eb', '#059669', '#d97706', '#dc2626'];
```

### Adjust Refresh Interval

Edit `contexts/DashboardContext.tsx`:
```typescript
const interval = setInterval(refreshMetrics, 30000); // ms
```

## 📝 Available Scripts

```bash
npm run dev      # Development server
npm run build    # Production build
npm start        # Production server
npm run lint     # Code linting
```

## 🎨 Component Guidelines

### Stat Cards
- Large value (3xl, semibold)
- Uppercase label (sm, medium)
- Trend indicator with icon
- Icon badge with background color

### Data Tables
- Header: Slate-50 background
- Row height: 64px minimum
- Hover: Slate-50 background
- Padding: 16px horizontal

### Charts
- Minimum height: 280px
- Grid: Dashed, slate-200
- Tooltip: White with shadow
- Font: 12-13px Inter

## 📄 License

MIT

---

Built with focus on **clarity**, **data visualization**, and **professional aesthetics**.
