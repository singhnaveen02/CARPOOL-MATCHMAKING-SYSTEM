# Carpool Matchmaking System - Frontend

React.js + Tailwind CSS frontend for the carpool application.

## Setup

```bash
npm install
npm run dev
```

Frontend runs at: http://localhost:3000

## Project Structure

```
src/
├── App.jsx                  # Main app component
├── main.jsx                 # Entry point
├── components/
│   ├── Auth/                # Login/signup forms
│   ├── Rides/               # Ride posting/search
│   ├── Matches/             # Match recommendations
│   ├── Dashboard/           # User dashboard
│   └── Common/              # Navbar, footer, etc.
├── pages/                   # Page components
├── services/
│   ├── api.js              # Axios config + interceptors
│   ├── authService.js
│   ├── rideService.js
│   └── userService.js
├── context/
│   └── AuthContext.jsx     # Auth state management
├── hooks/                   # Custom React hooks
├── utils/                   # Utilities
└── styles/                  # Tailwind CSS
```

## Phase 1 Status

- [x] Project scaffolding
- [x] Tailwind CSS setup
- [x] API client (axios)
- [x] Auth context
- [x] Basic page structure
- [ ] Login/signup forms (Phase 1B)
- [ ] Ride posting UI (Phase 1B)
- [ ] Ride search UI (Phase 1B)

## Available Scripts

- `npm run dev` - Start dev server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm test` - Run tests

