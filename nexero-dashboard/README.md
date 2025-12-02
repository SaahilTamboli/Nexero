# Nexero VR Analytics Dashboard

A beautiful, professional dashboard for monitoring VR real estate property tours with real-time analytics, engagement metrics, and AI predictions.

## Features

✨ **Modern UI/UX**
- Clean, professional design with smooth animations
- Dark mode support with theme toggle
- Fully responsive (desktop, tablet, mobile)
- Intuitive navigation

📊 **Analytics & Visualizations**
- Real-time session monitoring
- Interactive charts (Chart.js)
- Engagement metrics and heatmaps
- Session trend analysis
- KPI cards with comparison metrics

🎯 **Key Metrics**
- Total VR sessions
- Average session duration
- Engagement rates
- Active properties tracking

🔄 **Live Updates**
- Auto-refresh every 5 minutes
- Manual refresh button
- Date range filtering (7, 30, 90, 365 days)

## Tech Stack

- **HTML5** - Semantic markup
- **Tailwind CSS** - Utility-first CSS framework (via CDN)
- **Vanilla JavaScript** - No frameworks, pure JS
- **Chart.js** - Data visualization library (CDN)
- **Backend** - FastAPI at https://nexero.onrender.com

## Getting Started

### Option 1: Open Directly

Simply open `index.html` in your browser:
```bash
# Windows
start index.html

# Mac
open index.html

# Linux
xdg-open index.html
```

### Option 2: Use Live Server (Recommended)

1. Install VS Code extension: [Live Server](https://marketplace.visualstudio.com/items?itemName=ritwickdey.LiveServer)
2. Right-click on `index.html`
3. Select "Open with Live Server"
4. Dashboard opens at `http://localhost:5500`

### Option 3: Python HTTP Server

```bash
# Python 3
python -m http.server 8000

# Open browser to http://localhost:8000
```

## Project Structure

```
nexero-dashboard/
├── index.html          # Main HTML structure
├── styles.css          # All styling (light/dark themes)
├── script.js           # Dashboard logic & API integration
└── README.md           # This file
```

## API Integration

The dashboard connects to your FastAPI backend at:
```
https://nexero.onrender.com/api/v1
```

### API Endpoints (Expected)

```javascript
GET /api/v1/sessions?days=30       // Get sessions for time period
GET /api/v1/analytics?days=30      // Get analytics summary
```

### Mock Data

Currently using mock data for development. The dashboard will automatically switch to real API when backend endpoints are ready.

## Customization

### Change Colors

Edit Tailwind config in `index.html`:

```javascript
tailwind.config = {
    darkMode: 'class',
    theme: {
        extend: {
            colors: {
                primary: '#3b82f6',    // Change primary color
                secondary: '#8b5cf6',  // Change secondary color
            }
        }
    }
}
```

Or use any Tailwind color utility classes directly in the HTML.

### Change API URL

Edit `script.js`:

```javascript
const API_BASE_URL = 'https://your-api-url.com/api/v1';
```

### Modify Charts

Chart configurations in `script.js`:
- `initSessionTrendsChart()` - Line chart for session trends
- `initEngagementChart()` - Bar chart for engagement metrics

## Features Breakdown

### Dashboard Pages

1. **Overview** - Main dashboard with KPIs and charts
2. **Sessions** - Session history and details
3. **Heatmaps** - Visual engagement heatmaps
4. **AI Insights** - Predictive analytics
5. **Properties** - Property management

### KPI Cards

- Total Sessions (with trend comparison)
- Average Session Time
- Engagement Rate
- Active Properties

### Charts

1. **Session Trends** - 30-day line chart showing daily sessions
2. **Engagement Metrics** - Bar chart showing zone visits

### Data Table

Recent sessions with:
- Session ID
- Property name
- Start time
- Duration
- Status badge (completed, active, pending)
- Action button (View Details)

## Dark Mode

Automatically remembers user preference using localStorage:
- Click moon/sun icon in sidebar
- Theme persists across sessions

## Browser Support

- ✅ Chrome/Edge (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Mobile browsers

## Performance

- Lightweight: ~50KB total (excluding Chart.js CDN)
- Fast load times
- Smooth animations (60fps)
- Optimized rendering

## Next Steps

1. **Connect Real API** - Replace mock data with actual FastAPI endpoints
2. **Add Authentication** - User login and session management
3. **Export Reports** - PDF/CSV export functionality
4. **Real-time Updates** - WebSocket integration for live data
5. **Advanced Filters** - Property, customer, date range filters
6. **AI Predictions** - Integrate ML model predictions

## Deployment

### Deploy to GitHub Pages

```bash
git init
git add .
git commit -m "Initial dashboard"
git branch -M main
git remote add origin https://github.com/yourusername/nexero-dashboard.git
git push -u origin main
```

Then enable GitHub Pages in repository settings.

### Deploy to Vercel

```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

### Deploy to Netlify

Drag and drop the folder to [Netlify Drop](https://app.netlify.com/drop)

## License

Proprietary - Nexero VR Analytics Platform

## Support

For issues or questions, contact the development team.

---

Built with ❤️ for property builders using VR technology
