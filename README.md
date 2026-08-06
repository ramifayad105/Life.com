# Preventive Care Dashboard

A Flask-based web application that helps users manage their preventive healthcare by displaying upcoming appointments, providing age-based health guidelines, and finding healthcare providers near their location.

## Live Demo

🌐 [https://life-preventive-care.azurewebsites.net](https://life-preventive-care.azurewebsites.net)

## Features

- **Upcoming Appointments**: View, reschedule, and cancel scheduled medical appointments
- **Book Appointments**: Get age-based health screening recommendations and book directly with providers
- **Location-Based Provider Search**: Automatically finds healthcare providers near the user using browser geolocation and the NPI Registry API
- **Pharmacy Finder**: Browse local pharmacies and their services
- **User Accounts**: Register and login with personalized appointment data
- **Dark/Light Mode**: Toggle between themes in settings

## Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, Jinja2 templating
- **APIs**: NPI Registry (provider search), OpenStreetMap Nominatim (reverse geocoding)
- **Hosting**: Azure App Service (Free tier, auto-deploys via GitHub Actions)
- **Testing**: pytest, Hypothesis (property-based testing)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/ramifayad105/Life.com.git
cd Life.com
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Start the Flask development server:
```bash
python app.py
```

2. Open your browser and navigate to:
```
http://127.0.0.1:8080
```

3. Login with default credentials:
   - Username: `test`
   - Password: `test123`

4. Interact with the dashboard:
   - View and manage your appointments
   - Select your age range to get personalized health screening recommendations
   - Allow location access to find healthcare providers near you
   - Browse local pharmacies

## Testing

Run the test suite:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=. --cov-report=html
```

## Project Structure

```
Life.com/
├── app.py                 # Main Flask application with routes and API
├── Templates/
│   ├── home.html          # Dashboard template
│   ├── login.html         # Login page
│   └── register.html      # Registration page
├── Static/
│   ├── style.css          # Stylesheet
│   └── favicon.svg        # Favicon
├── tests/
│   ├── conftest.py        # Test configuration
│   ├── test_properties.py # Property-based tests
│   ├── test_unit.py       # Unit tests
│   └── test_integration.py # Integration tests
├── .github/
│   └── workflows/
│       └── master_life-preventive-care.yml  # CI/CD pipeline
├── requirements.txt       # Python dependencies
├── startup.txt            # Azure App Service startup command
└── README.md              # This file
```

## Deployment

The app auto-deploys to Azure App Service on every push to `master` via GitHub Actions. The workflow builds the app, installs dependencies, and deploys using a publish profile.

## License

MIT
