from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime
import json
import os
import requests

app = Flask(__name__, template_folder='Templates', static_folder='Static')
app.secret_key = 'your-secret-key-change-in-production'

# Login credentials
VALID_USERNAME = 'test'
VALID_PASSWORD = 'test123'

# File to store user accounts
USERS_FILE = 'users.json'
APPOINTMENTS_FILE = 'appointments.json'

def load_users():
    """Load users from JSON file"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users):
    """Save users to JSON file"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def load_appointments():
    """Load all appointments from JSON file"""
    if os.path.exists(APPOINTMENTS_FILE):
        try:
            with open(APPOINTMENTS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_appointments(appointments_data):
    """Save all appointments to JSON file"""
    with open(APPOINTMENTS_FILE, 'w') as f:
        json.dump(appointments_data, f, indent=2)

def get_user_appointments(username):
    """Get appointments for a specific user"""
    all_appointments = load_appointments()
    return all_appointments.get(username, [])

def save_user_appointments(username, appointments):
    """Save appointments for a specific user"""
    all_appointments = load_appointments()
    all_appointments[username] = appointments
    save_appointments(all_appointments)

def verify_user(username, password):
    """Verify user credentials"""
    # Check default test account
    if username == VALID_USERNAME and password == VALID_PASSWORD:
        return True
    
    # Check registered users
    users = load_users()
    if username in users and users[username] == password:
        return True
    
    return False

def register_user(username, password):
    """Register a new user"""
    users = load_users()
    
    # Check if username already exists
    if username in users or username == VALID_USERNAME:
        return False
    
    users[username] = password
    save_users(users)
    return True

# ── Data ──────────────────────────────────────────────────────────────────────

# Get appointments for the logged-in user
def get_appointments():
    username = session.get('username', 'guest')
    return get_user_appointments(username)

pharmacies = [
    {
        'name': 'CVS Pharmacy',
        'address': '1500 S Memorial Dr, Greenville, NC 27834',
        'phone': '(252) 756-6900',
        'hours': 'Mon–Fri 8am–9pm, Sat–Sun 9am–6pm',
        'services': ['Prescriptions', 'Vaccinations', 'Health Screenings', '24-Hour Pharmacy'],
    },
    {
        'name': 'Walgreens Pharmacy',
        'address': '2410 Stantonsburg Rd, Greenville, NC 27834',
        'phone': '(252) 756-2191',
        'hours': 'Mon–Fri 8am–10pm, Sat–Sun 9am–6pm',
        'services': ['Prescriptions', 'Immunizations', 'Photo Services', 'Drive-Thru'],
    },
    {
        'name': 'Walmart Pharmacy',
        'address': '3040 Evans St, Greenville, NC 27834',
        'phone': '(252) 355-5116',
        'hours': 'Mon–Fri 9am–9pm, Sat 9am–7pm, Sun 10am–6pm',
        'services': ['Prescriptions', 'Flu Shots', 'Health Tests', 'Low-Cost Generics'],
    },
    {
        'name': 'Rite Aid Pharmacy',
        'address': '1755 W Arlington Blvd, Greenville, NC 27834',
        'phone': '(252) 756-4141',
        'hours': 'Mon–Fri 8am–9pm, Sat–Sun 9am–6pm',
        'services': ['Prescriptions', 'Wellness Programs', 'Vaccinations', 'Medication Therapy'],
    },
    {
        'name': 'Harris Teeter Pharmacy',
        'address': '3500 S Memorial Dr, Greenville, NC 27834',
        'phone': '(252) 355-0023',
        'hours': 'Mon–Fri 9am–8pm, Sat 9am–6pm, Sun 11am–5pm',
        'services': ['Prescriptions', 'Immunizations', 'Health Consultations', 'Specialty Medications'],
    },
    {
        'name': 'Food Lion Pharmacy',
        'address': '2406 E 10th St, Greenville, NC 27858',
        'phone': '(252) 758-4900',
        'hours': 'Mon–Fri 9am–8pm, Sat 9am–6pm, Sun 12pm–5pm',
        'services': ['Prescriptions', 'Flu Shots', 'Medication Counseling', 'Auto Refills'],
    },
]

health_guidelines = {
    '18-30': [
        'Blood pressure check',
        'BMI check',
        'Cholesterol screening',
        'Mental health screening',
    ],
    '31-50': [
        'Heart disease risk assessment',
        'Diabetes screening',
        'Mammogram',
        'Colonoscopy',
    ],
    '51+': [
        'Bone density test',
        'Vision and hearing test',
        'Flu and shingles vaccines',
        'Cognitive health checkup',
    ],
}

# ── Healthy range evaluators per test ─────────────────────────────────────────
# Each function receives (value_string, age_range) and returns True if healthy.

def _parse_bp(val):
    """Parse 'systolic/diastolic' or just systolic."""
    parts = val.replace(' ', '').split('/')
    try:
        sys = int(parts[0])
        dia = int(parts[1]) if len(parts) > 1 else None
        return sys, dia
    except (ValueError, IndexError):
        return None, None

def evaluate_health(test, value, age_range):
    t = test.lower()
    v = value.strip()

    if 'blood pressure' in t:
        sys, dia = _parse_bp(v)
        if sys is None:
            return None
        sys_ok = sys < 130
        dia_ok = (dia < 85) if dia is not None else True
        return sys_ok and dia_ok

    if 'bmi' in t:
        try:
            bmi = float(v)
            return 18.5 <= bmi <= 24.9
        except ValueError:
            return None

    if 'cholesterol' in t:
        try:
            chol = float(v)
            return chol < 200
        except ValueError:
            return None

    if 'diabetes' in t or 'blood sugar' in t or 'glucose' in t:
        try:
            glucose = float(v)
            return glucose < 100
        except ValueError:
            return None

    if 'bone density' in t or 't-score' in t:
        try:
            score = float(v)
            return score >= -1.0
        except ValueError:
            return None

    # For qualitative checks (mammogram, colonoscopy, vaccines, etc.)
    # treat any non-empty entry as "done" → green
    return True if v else None


# Mapping of health screenings to service categories
screening_to_service = {
    'Blood pressure check': ['Cardiology', 'Preventive Care', 'Family Medicine', 'General Medicine'],
    'BMI check': ['Preventive Care', 'Family Medicine', 'General Medicine', 'Nutrition'],
    'Cholesterol screening': ['Cardiology', 'Preventive Care', 'Family Medicine', 'General Medicine'],
    'Mental health screening': ['Mental Health', 'Family Medicine'],
    'Heart disease risk assessment': ['Cardiology', 'Preventive Care', 'General Medicine'],
    'Diabetes screening': ['Diabetes Management', 'Diabetes Care', 'Preventive Care', 'Family Medicine'],
    'Mammogram': ['Women\'s Health', 'Oncology', 'Imaging'],
    'Colonoscopy': ['Gastroenterology', 'General Surgery', 'Oncology'],
    'Bone density test': ['Orthopedics', 'Women\'s Health', 'Imaging'],
    'Vision and hearing test': ['Family Medicine', 'General Medicine'],
    'Flu and shingles vaccines': ['Preventive Care', 'Family Medicine', 'General Medicine'],
    'Cognitive health checkup': ['Neurology', 'Neuroscience', 'Mental Health', 'Family Medicine'],
}

providers = [
    {
        'name': 'City General Hospital',
        'specializations': ['General Medicine', 'Cardiology', 'Oncology'],
        'phone': '(555) 100-2000',
        'address': '100 Main St, Suite 1',
        'hours': 'Mon–Fri 7am–6pm',
        'details': [
            'Full-service emergency department open 24/7',
            'Advanced cardiac imaging and stress testing',
            'Oncology infusion center with specialist consultations',
            'In-house lab and radiology services',
        ],
    },
    {
        'name': 'Riverside Medical Center',
        'specializations': ['Preventive Care', 'Diabetes Management', 'Nutrition'],
        'phone': '(555) 200-3000',
        'address': '200 River Rd',
        'hours': 'Mon–Sat 8am–5pm',
        'details': [
            'Comprehensive annual wellness exams and health screenings',
            'Certified diabetes educators and continuous glucose monitoring support',
            'Registered dietitian consultations and meal planning',
            'Cholesterol and blood pressure management programs',
        ],
    },
    {
        'name': 'Northside Health Clinic',
        'specializations': ['Family Medicine', 'Mental Health', 'Pediatrics'],
        'phone': '(555) 300-4000',
        'address': '300 North Ave',
        'hours': 'Mon–Fri 8am–7pm, Sat 9am–1pm',
        'details': [
            'Primary care for all ages from newborns to seniors',
            'Licensed therapists offering individual and group counseling',
            'Pediatric immunizations and developmental screenings',
            'Telehealth appointments available',
        ],
    },
    {
        'name': 'ECU Health Medical Center',
        'specializations': ['Academic Medicine', 'Cardiology', 'Neurology', 'Orthopedics'],
        'phone': '(252) 847-4100',
        'address': '2100 Stantonsburg Rd, Greenville, NC 27834',
        'hours': 'Open 24/7 — Emergency & Inpatient Services',
        'details': [
            'Level I Trauma Center serving eastern North Carolina',
            'ECU Health Heart & Vascular Center with interventional cardiology',
            'Comprehensive stroke and neurology program',
            'Orthopedic surgery, joint replacement, and sports medicine',
            'Cancer care through ECU Health Cancer Center',
            'Teaching hospital affiliated with East Carolina University',
        ],
    },
    {
        'name': 'Vidant Beaufort Hospital',
        'specializations': ['Emergency Care', 'General Surgery', 'Family Medicine', 'Imaging'],
        'phone': '(252) 975-4100',
        'address': '628 E 12th St, Washington, NC 27889',
        'hours': 'Emergency 24/7, Outpatient Mon–Fri 8am–5pm',
        'details': [
            'Full-service community hospital in Beaufort County',
            'Emergency department with board-certified physicians',
            'Advanced diagnostic imaging including CT and MRI',
            'Outpatient surgery center and wound care clinic',
            'Primary care and specialty physician practices',
        ],
    },
    {
        'name': 'Carteret Health Care',
        'specializations': ['Coastal Medicine', 'Orthopedics', 'Women\'s Health', 'Rehabilitation'],
        'phone': '(252) 499-6000',
        'address': '3500 Arendell St, Morehead City, NC 28557',
        'hours': 'Emergency 24/7, Clinics Mon–Fri 8am–5pm',
        'details': [
            'Coastal community hospital serving Crystal Coast region',
            'Orthopedic and sports medicine specialists',
            'Women\'s health services including obstetrics and mammography',
            'Physical therapy and cardiac rehabilitation programs',
            'Walk-in urgent care and primary care network',
        ],
    },
    {
        'name': 'Onslow Memorial Hospital',
        'specializations': ['Emergency Medicine', 'Maternity Care', 'Cardiology', 'General Surgery'],
        'phone': '(910) 577-2345',
        'address': '317 Western Blvd, Jacksonville, NC 28546',
        'hours': 'Open 24/7 — Emergency & Inpatient Services',
        'details': [
            'Serving Jacksonville and Onslow County communities',
            'Family Birth Place with Level II nursery',
            'Cardiac catheterization lab and heart center',
            'Comprehensive cancer care and infusion services',
            'Multiple primary care and specialty clinics throughout the area',
        ],
    },
    {
        'name': 'Nash UNC Health Care',
        'specializations': ['Regional Healthcare', 'Oncology', 'Neuroscience', 'Bariatric Surgery'],
        'phone': '(252) 962-8000',
        'address': '2460 Curtis Ellis Dr, Rocky Mount, NC 27804',
        'hours': 'Emergency 24/7, Outpatient Mon–Fri 7am–6pm',
        'details': [
            'Regional medical center serving Nash and Edgecombe counties',
            'Comprehensive cancer center with radiation oncology',
            'Neuroscience center with stroke certification',
            'Bariatric surgery program and weight management',
            'Advanced wound care and hyperbaric medicine',
        ],
    },
    {
        'name': 'Wilson Medical Center',
        'specializations': ['Community Healthcare', 'Diabetes Care', 'Pulmonology', 'Gastroenterology'],
        'phone': '(252) 399-8040',
        'address': '1705 Tarboro St SW, Wilson, NC 27893',
        'hours': 'Emergency 24/7, Clinics Mon–Fri 8am–5pm',
        'details': [
            'Community hospital serving Wilson County',
            'Diabetes education and management programs',
            'Pulmonary function testing and sleep studies',
            'Endoscopy center and digestive health services',
            'Primary care medical group with multiple locations',
        ],
    },
    {
        'name': 'Outer Banks Hospital',
        'specializations': ['Coastal Emergency Care', 'Family Medicine', 'Urgent Care', 'Telemedicine'],
        'phone': '(252) 449-4500',
        'address': '4800 S Croatan Hwy, Nags Head, NC 27959',
        'hours': 'Emergency 24/7, Urgent Care 7 days 8am–8pm',
        'details': [
            'Only hospital serving the Outer Banks barrier islands',
            'Emergency services for residents and tourists',
            'Urgent care centers in Nags Head and Avon',
            'Telemedicine consultations with specialists',
            'Primary care and walk-in services year-round',
        ],
    },
]

# ── Routes ────────────────────────────────────────────────────────────────────

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        if verify_user(username, password):
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('index'))
        else:
            error = 'Invalid username or password'
    
    return render_template('login.html', error=error)


@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    success = None
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        # Validation
        if not username or not password:
            error = 'Username and password are required'
        elif len(username) < 3:
            error = 'Username must be at least 3 characters'
        elif len(password) < 6:
            error = 'Password must be at least 6 characters'
        elif password != confirm_password:
            error = 'Passwords do not match'
        elif register_user(username, password):
            success = 'Account created successfully! You can now login.'
        else:
            error = 'Username already exists'
    
    return render_template('register.html', error=error, success=success)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))


@app.route('/home', methods=['GET', 'POST'])
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    username = session.get('username', 'guest')
    selected_age = None
    recommended_tests = []
    selected_screening = None
    filtered_providers = []
    user_values = {}
    health_status = {}
    unhealthy_tests = []
    saved = False
    appointments = get_user_appointments(username)
    
    # Ensure all appointments have IDs and raw_date
    for idx, appt in enumerate(appointments):
        if 'id' not in appt:
            appt['id'] = idx
        if 'raw_date' not in appt:
            # Try to parse the formatted date back to raw format
            try:
                date_obj = datetime.strptime(appt['date'], '%B %d, %Y')
                appt['raw_date'] = date_obj.strftime('%Y-%m-%d')
            except:
                appt['raw_date'] = datetime.now().strftime('%Y-%m-%d')
    
    # Save updated appointments back to file
    if appointments:
        save_user_appointments(username, appointments)
    
    active_tab = request.args.get('tab', 'appointments')

    if request.method == 'POST':
        selected_age = request.form.get('age_range', '')
        selected_screening = request.form.get('screening', '')
        recommended_tests = health_guidelines.get(selected_age, [])

        # Filter providers based on selected screening
        if selected_screening and selected_screening in screening_to_service:
            required_services = screening_to_service[selected_screening]
            for provider in providers:
                # Check if provider offers any of the required services
                if any(service in provider['specializations'] for service in required_services):
                    filtered_providers.append(provider)
        
        any_values = any(
            request.form.get(t.lower().replace(' ', '_'), '').strip()
            for t in recommended_tests
        )

        if any_values:
            for test in recommended_tests:
                key = test.lower().replace(' ', '_')
                val = request.form.get(key, '').strip()
                if val:
                    user_values[test] = val
                    result = evaluate_health(test, val, selected_age)
                    health_status[test] = result
                    if result is False:
                        unhealthy_tests.append(test)
            saved = True

    return render_template(
        'home.html',
        appointments=appointments,
        providers=providers,
        pharmacies=pharmacies,
        selected_age=selected_age,
        recommended_tests=recommended_tests,
        selected_screening=selected_screening,
        filtered_providers=filtered_providers,
        user_values=user_values,
        health_status=health_status,
        unhealthy_tests=unhealthy_tests,
        saved=saved,
        today=datetime.now().strftime('%Y-%m-%d'),
        active_tab=active_tab,
        theme=session.get('theme', 'light'),
    )


@app.route('/book-appointment', methods=['POST'])
def book_appointment():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    username = session.get('username', 'guest')
    provider_name = request.form.get('provider_name', '')
    appointment_date = request.form.get('appointment_date', '')
    appointment_time = request.form.get('appointment_time', '')
    purpose = request.form.get('purpose', '')
    
    if provider_name and appointment_date and appointment_time and purpose:
        # Get existing appointments for this user
        appointments = get_user_appointments(username)
        
        # Format date to be more readable (e.g., "April 10, 2026")
        try:
            date_obj = datetime.strptime(appointment_date, '%Y-%m-%d')
            formatted_date = date_obj.strftime('%B %d, %Y')
        except:
            formatted_date = appointment_date
        
        # Add new appointment with unique ID
        new_appointment = {
            'id': len(appointments),
            'date': formatted_date,
            'raw_date': appointment_date,
            'time': appointment_time,
            'hospital': provider_name,
            'purpose': purpose,
        }
        appointments.append(new_appointment)
        
        # Save back to file
        save_user_appointments(username, appointments)
    
    return redirect(url_for('index', tab='appointments'))


@app.route('/cancel-appointment/<int:appointment_id>', methods=['POST', 'GET'])
def cancel_appointment(appointment_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    username = session.get('username', 'guest')
    appointments = get_user_appointments(username)
    
    # Remove appointment by ID
    appointments = [appt for appt in appointments if appt.get('id') != appointment_id]
    
    # Re-index appointments
    for idx, appt in enumerate(appointments):
        appt['id'] = idx
    
    save_user_appointments(username, appointments)
    
    return redirect(url_for('index', tab='appointments'))


@app.route('/reschedule-appointment/<int:appointment_id>', methods=['POST'])
def reschedule_appointment(appointment_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    username = session.get('username', 'guest')
    new_date = request.form.get('appointment_date', '')
    new_time = request.form.get('appointment_time', '')
    
    if new_date and new_time:
        appointments = get_user_appointments(username)
        
        # Find and update the appointment
        for appt in appointments:
            if appt.get('id') == appointment_id:
                try:
                    date_obj = datetime.strptime(new_date, '%Y-%m-%d')
                    appt['date'] = date_obj.strftime('%B %d, %Y')
                    appt['raw_date'] = new_date
                except:
                    appt['date'] = new_date
                    appt['raw_date'] = new_date
                appt['time'] = new_time
                break
        
        save_user_appointments(username, appointments)
    
    return redirect(url_for('index', tab='appointments'))


@app.route('/toggle-theme', methods=['POST'])
def toggle_theme():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    current_theme = session.get('theme', 'light')
    new_theme = 'dark' if current_theme == 'light' else 'light'
    session['theme'] = new_theme
    session.modified = True
    
    return redirect(url_for('index', tab='settings'))


@app.route('/api/nearby-providers')
def nearby_providers():
    """Search for healthcare providers near a location using NPI Registry API"""
    city = request.args.get('city', '')
    state = request.args.get('state', '')
    
    if not city or not state:
        return jsonify({'providers': [], 'error': 'City and state are required'})
    
    try:
        # Query the free NPI Registry API
        params = {
            'version': '2.1',
            'city': city,
            'state': state,
            'taxonomy_description': 'hospital',
            'limit': 10,
        }
        resp = requests.get('https://npiregistry.cms.hhs.gov/api/', params=params, timeout=10)
        data = resp.json()
        
        results = []
        if data.get('result_count', 0) > 0:
            for result in data.get('results', []):
                # Get the practice address
                addresses = result.get('addresses', [])
                practice_addr = None
                for addr in addresses:
                    if addr.get('address_purpose') == 'LOCATION':
                        practice_addr = addr
                        break
                if not practice_addr and addresses:
                    practice_addr = addresses[0]
                
                # Build provider info
                name = ''
                if result.get('basic', {}).get('organization_name'):
                    name = result['basic']['organization_name']
                else:
                    first = result.get('basic', {}).get('first_name', '')
                    last = result.get('basic', {}).get('last_name', '')
                    name = f"{first} {last}".strip()
                
                # Get taxonomies (specializations)
                taxonomies = result.get('taxonomies', [])
                specs = [t.get('desc', '') for t in taxonomies if t.get('desc')]
                
                address_str = ''
                phone = ''
                if practice_addr:
                    addr_parts = [
                        practice_addr.get('address_1', ''),
                        practice_addr.get('city', ''),
                        practice_addr.get('state', ''),
                        practice_addr.get('postal_code', '')[:5],
                    ]
                    address_str = ', '.join(p for p in addr_parts if p)
                    phone = practice_addr.get('telephone_number', '')
                
                if name:
                    results.append({
                        'name': name,
                        'address': address_str,
                        'phone': phone,
                        'specializations': specs[:4],
                    })
        
        return jsonify({'providers': results})
    
    except Exception as e:
        return jsonify({'providers': [], 'error': str(e)})


if __name__ == '__main__':
    # host='0.0.0.0' allows access from other devices on the network
    # Using port 8080 to avoid conflict with macOS AirPlay Receiver on port 5000
    # Access from other devices: http://YOUR_IP_ADDRESS:8080
    app.run(debug=True, host='0.0.0.0', port=8080)
