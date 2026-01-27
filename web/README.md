# Gas Station Monitoring Frontend

React + TypeScript frontend for the Gas Station Monitoring system.

## Quick Start

### 1. Install Dependencies
```bash
npm install
```

### 2. Development Server
```bash
npm run dev
```

### 3. Access
- Frontend: http://localhost:5173

## Build for Production

```bash
npm run build
npm run preview
```

## Structure

```
web/
├── package.json           Dependencies
├── vite.config.ts         Vite config
├── index.html             HTML entry
├── tsconfig.json          TypeScript config
│
├── src/
│   ├── components/        React components
│   │   ├── AdminDashboard.tsx
│   │   ├── AllCars.tsx
│   │   ├── CarTable.tsx
│   │   ├── EmployeeDashboard.tsx
│   │   ├── Login.tsx
│   │   ├── UnpaidCars.tsx
│   │   ├── PaymentModal.tsx
│   │   └── ui/            Shadcn UI components
│   │
│   ├── styles/
│   │   ├── globals.css
│   │   └── index.css
│   │
│   ├── api.ts             API calls
│   ├── App.tsx            Main app
│   ├── main.tsx           Entry point
│   └── index.css          Styles
│
├── node_modules/          Node dependencies
└── build/                 Production build
```

## Components

### Pages
- **Login** - User authentication
- **AllCars** - View all vehicles with real-time data
- **UnpaidCars** - View unpaid vehicles only
- **AdminDashboard** - Analytics and statistics
- **EmployeeDashboard** - Employee performance tracking

### Features
- Real-time vehicle detection display
- License plate image viewing
- Payment status tracking
- Analytics charts
- Responsive design
- Dark mode support

## API Integration

Backend API at: `http://localhost:8000/api/`

### API Calls (in src/api.ts)
- `getCarsWithAnalysis()` - Get all cars with analysis
- `getDetectedVehicles()` - Get detected vehicles
- `markCarAsPaid(vehicleId)` - Mark vehicle as paid
- `markCarAsUnpaid(vehicleId)` - Mark vehicle as unpaid

## Technologies

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Shadcn UI** - Component library
- **Recharts** - Charts and graphs
- **Lucide React** - Icons

## Environment Variables

Create `.env` file:
```env
VITE_API_URL=http://localhost:8000
```

## Styles

- **Tailwind CSS** - Utility-first CSS
- **Dark Mode** - Built-in dark mode
- **Responsive** - Mobile-friendly design

## Icons

Using Lucide React icons:
- `Clock` - Time
- `Car` - Vehicle
- `DollarSign` - Payment
- `TrendingUp` - Analytics
- `Camera` - Image capture

## Charts

Using Recharts for visualization:
- Line charts for trends
- Bar charts for comparisons
- Pie charts for distribution

## Development

### Add New Component
```bash
npm install
# Create component in src/components/
# Import and use in App.tsx
```

### Hot Module Replacement (HMR)
Changes auto-reload in development

### Build
```bash
npm run build
# Output in dist/
```

## Performance

- Code splitting with Vite
- Image optimization
- CSS minimization
- Tree shaking

## Deployment

### Static Hosting
```bash
npm run build
# Deploy dist/ folder
```

### Docker
```bash
docker build -t gas-station-web .
docker run -p 3000:80 gas-station-web
```

### Environment
- Development: `npm run dev`
- Production: `npm run build && npm run preview`

## Notes

- All API calls go to backend at port 8000
- CORS must be enabled on backend
- Frontend expects images from backend static folders
- Real-time data updates when vehicles are detected
