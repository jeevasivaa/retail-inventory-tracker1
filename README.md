# Retail Inventory Tracker# Retail Chain Inventory Tracker - Mini Project

...
A comprehensive inventory management system built with Flask, featuring user authentication, stock management, and real-time reporting capabilities.

## 🚀 Features

### 🔐 Authentication System
- **User Registration & Login**: Secure authentication with session management
- **Role-Based Access**: Admin, Manager, and User roles
- **Password Security**: SHA-256 hashed passwords
- **Demo Account**: Username: `admin`, Password: `admin123`

### 📦 Inventory Management
- **Product Management**: Full CRUD operations for products with categories and suppliers
- **Store Management**: Multi-store inventory tracking
- **Stock Operations**: Add, transfer, adjust inventory levels
- **Low Stock Alerts**: Automated notifications for reorder points

### 📊 Advanced Features
- **Stock Receiving**: Professional supplier receiving workflows
- **Bulk Operations**: Process multiple inventory changes simultaneously
- **Transaction History**: Complete audit trail of all stock movements
- **Reports & Analytics**: Category summaries, store performance, inventory valuation

### 💰 Financial Features
- **Multi-Currency Support**: Built-in rupee (₹) currency formatting
- **Cost Tracking**: Track product costs and inventory valuation
- **Pricing Management**: Separate cost and sell price management

### 🎨 Modern Interface
- **Responsive Design**: Mobile-friendly Bootstrap-based UI
- **Professional Dashboard**: Real-time statistics and alerts
- **Intuitive Navigation**: Clean, organized user interface
- **Flash Notifications**: User-friendly feedback system

## 🛠️ Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLite with automatic schema management
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Icons**: Font Awesome 6
- **Authentication**: Flask Sessions with secure password hashing

## 📋 Requirements

- Python 3.7+
- Flask 2.0+
- SQLite3 (included with Python)
- Modern web browser

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/retail-inventory-tracker.git
cd retail-inventory-tracker
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application
```bash
python app.py
```

### 4. Access the System
- Open your browser to `http://localhost:5000`
- Login with demo credentials: `admin` / `admin123`
- Start managing your inventory!

## 📁 Project Structure

```
retail-inventory-tracker/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── schema.sql            # Database schema
├── README.md             # Project documentation
├── .gitignore            # Git ignore rules
├── instance/             # Database files (auto-created)
│   └── inventory.db      # SQLite database
├── static/               # Static assets
│   ├── style.css         # Main stylesheet
│   └── app.js           # JavaScript functionality
└── templates/            # HTML templates
    ├── base.html         # Base template
    ├── login.html        # Login page
    ├── register.html     # Registration page
    ├── dashboard.html    # Dashboard/Home
    ├── products.html     # Product management
    ├── stores.html       # Store management
    ├── inventory.html    # Inventory overview
    ├── stock_receiving.html  # Stock receiving
    ├── reports.html      # Reports and analytics
    └── ...               # Additional templates
```

## 🔧 Configuration

### Environment Variables
The application uses the following configuration:
- `SECRET_KEY`: Flask secret key for sessions (change in production)
- `DATABASE_URL`: SQLite database path (defaults to `instance/inventory.db`)

### Default Users
The system creates a default admin user:
- **Username**: `admin`
- **Password**: `admin123`
- **Role**: `admin`

**Important**: Change the default password in production!

## 📊 Database Schema

The application automatically creates and manages the following tables:
- `users` - User accounts and authentication
- `stores` - Store locations and information
- `products` - Product catalog with pricing
- `categories` - Product categorization
- `suppliers` - Supplier information
- `inventories` - Stock levels per store/product
- `transactions` - All inventory movements
- `settings` - Application configuration

## 🚀 Deployment

### Development
```bash
python app.py
```
The application runs on `http://localhost:5000` with debug mode enabled.

### Production
For production deployment:
1. Set `DEBUG = False` in `app.py`
2. Change the default `SECRET_KEY`
3. Use a production WSGI server like Gunicorn:
```bash
pip install gunicorn
gunicorn app:app
```

### Docker Deployment
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 API Documentation

### Authentication Endpoints
- `GET /login` - Login page
- `POST /login` - Process login
- `GET /register` - Registration page
- `POST /register` - Create new user
- `GET /logout` - Logout user

### Main Application Routes
- `GET /` - Dashboard
- `GET /products` - Product management
- `GET /stores` - Store management
- `GET /inventory` - Inventory overview
- `GET /stock-receiving` - Stock receiving interface
- `GET /reports` - Reports and analytics

### API Endpoints
- `GET /api/inventories/<store_id>` - Get inventory for store
- `POST /api/inventory/add-stock` - Add stock to inventory
- `POST /api/inventory/bulk-add` - Bulk inventory operations
- `GET /api/alerts/low-stock` - Get low stock alerts

## 🔒 Security Features

- **Password Hashing**: SHA-256 secure password storage
- **Session Management**: Secure Flask session handling
- **Input Validation**: Form validation and sanitization
- **CSRF Protection**: Built-in Flask CSRF protection
- **Role-Based Access**: Multi-level user permissions

## 📈 Features Roadmap

- [ ] Advanced reporting with charts
- [ ] Email notifications for low stock
- [ ] Barcode scanning integration
- [ ] Multi-warehouse support
- [ ] API rate limiting
- [ ] Advanced user management
- [ ] Data export/import functionality
- [ ] Mobile app companion

## 🐛 Known Issues

- None currently reported. Please submit issues through GitHub.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

- **JEEVA S** - [GitHub Profile](https://github.com/jeevasivaa)

## 🙏 Acknowledgments

- Flask community for the excellent web framework
- Bootstrap team for the responsive CSS framework
- Font Awesome for the beautiful icons
- All contributors who help improve this project

## 💬 Support

For support, please open an issue on GitHub

---

**Built with ❤️ for efficient inventory management**
