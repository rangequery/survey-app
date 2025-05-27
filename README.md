# SurveyApp - Advanced Survey Application

![Django](https://img.shields.io/badge/Django-5.2.1-green.svg)
![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange.svg)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 📋 Overview

SurveyApp is a comprehensive web-based survey platform built with Django that allows users to create, distribute, and analyze customized surveys. The application offers a wide range of question types, conditional logic, and powerful analytics tools to help users collect and interpret data effectively.

Whether you're conducting market research, gathering customer feedback, or collecting academic data, SurveyApp provides the flexibility and features needed for professional survey management.

## ✨ Features

### Survey Creation and Management
- Intuitive survey builder with drag-and-drop interface
- Multiple question types (text, multiple choice, rating scales, date/time, etc.)
- Conditional logic to create dynamic surveys
- Customizable themes and branding options
- Survey templates for quick starts
- Preview functionality before publishing

### Response Collection
- Public and private survey options
- Password protection for sensitive surveys
- Anonymous response collection
- Progress saving for respondents
- Mobile-friendly responsive design
- QR code generation for easy sharing

### Analysis and Reporting
- Real-time results dashboard
- Interactive charts and graphs with Chart.js
- Response filtering and segmentation
- Cross-tabulation analysis
- Export to CSV, Excel, and PDF formats
- Statistical analysis tools

### User Management
- User registration and authentication
- Customizable user profiles
- Team collaboration with permission levels
- Activity tracking and notifications
- Admin dashboard for system management

## 🛠️ Technologies

- **Backend**: Python 3.9, Django 5.2.1
- **Database**: MySQL 8.0
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5.3
- **Data Visualization**: Chart.js
- **Caching**: Redis
- **Deployment**: Vercel
- **Additional Libraries**: 
  - Flatpickr (date/time picker)
  - Pickr (color picker)
  - Django REST Framework (API)

## 📥 Installation

### Prerequisites
- Python 3.9 or higher
- MySQL 8.0 or higher
- Redis (for caching)
- pip (Python package manager)
- virtualenv (recommended)
- Git

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/benzhirou/SurveyApp.git
   cd SurveyApp
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the database**
   ```bash
   # Create MySQL database
   mysql -u root -p
   CREATE DATABASE survey_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'survey_user'@'localhost' IDENTIFIED BY 'password';
   GRANT ALL PRIVILEGES ON survey_db.* TO 'survey_user'@'localhost';
   FLUSH PRIVILEGES;
   EXIT;
   ```

5. **Configure environment variables**
   ```bash
   # Copy the example environment file
   cp .env.example .env
   # Edit the .env file with your database credentials and other settings
   ```

6. **Apply migrations**
   ```bash
   python manage.py migrate
   ```

7. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

8. **Run the development server**
   ```bash
   python manage.py runserver
   ```

9. **Access the application**
   - Open your browser and navigate to `http://127.0.0.1:8000`

## 🚀 Usage

### Creating Your First Survey
1. Register for an account or log in
2. Click "Create New Survey" from the dashboard
3. Add your survey title and description
4. Use the drag-and-drop interface to add questions
5. Configure question types and validation rules
6. Preview your survey before publishing
7. Share the survey link or QR code with respondents

### Managing Responses
1. View real-time responses in the dashboard
2. Filter and segment responses by criteria
3. Generate charts and visualizations
4. Export data in various formats
5. Analyze trends and patterns

## 📊 API Documentation

SurveyApp includes a RESTful API for integration with external applications:

- **Authentication**: Token-based authentication
- **Surveys**: CRUD operations for surveys
- **Responses**: Submit and retrieve survey responses
- **Analytics**: Access survey statistics and reports

For detailed API documentation, visit `/api/docs/` after running the application.

## 🧪 Testing

Run the test suite to ensure everything is working correctly:

```bash
# Run all tests
python manage.py test

# Run tests with coverage
coverage run --source='.' manage.py test
coverage report
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_NAME=survey_db
DATABASE_USER=survey_user
DATABASE_PASSWORD=password
DATABASE_HOST=localhost
DATABASE_PORT=3306
REDIS_URL=redis://localhost:6379
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Production Deployment

For production deployment on Vercel:

1. Configure your `vercel.json` file
2. Set up environment variables in Vercel dashboard
3. Connect your GitHub repository
4. Deploy with automatic builds

## 🤝 Contributing

We welcome contributions to SurveyApp! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guidelines
- Write tests for new features
- Update documentation as needed
- Ensure all tests pass before submitting

## 🐛 Troubleshooting

### Common Issues

**Database Connection Error**
- Verify MySQL is running
- Check database credentials in `.env` file
- Ensure database exists and user has proper permissions

**Static Files Not Loading**
- Run `python manage.py collectstatic`
- Check `STATIC_URL` and `STATIC_ROOT` settings

**Redis Connection Error**
- Ensure Redis server is running
- Verify Redis URL in settings

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


## 🙏 Acknowledgments

- Django community for the excellent framework
- Bootstrap team for the responsive UI components
- Chart.js for beautiful data visualizations
- All contributors who have helped improve this project

---

Made with ❤️ by [rangequery](https://github.com/benzhirou)
