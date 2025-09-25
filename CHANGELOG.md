# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release preparation for GitHub

## [2.0.0] - 2025-09-25

### Added
- **Authentication System**: Complete user registration, login, and logout functionality
- **Role-Based Access Control**: Admin, Manager, and User roles
- **Password Security**: SHA-256 hashed password storage
- **Session Management**: Secure Flask session handling
- **Professional UI**: Modern Bootstrap-based interface with responsive design
- **Stock Receiving**: Advanced supplier receiving workflows
- **Bulk Operations**: Process multiple inventory changes simultaneously
- **Currency Support**: Built-in rupee (₹) formatting throughout the application
- **User Profile Management**: Complete user profile system
- **Enhanced Navigation**: Dynamic user information in sidebar
- **Flash Messaging**: User-friendly notification system

### Changed
- **Complete UI Overhaul**: Migrated to modern Bootstrap 5 design
- **Database Schema**: Enhanced with users table and additional fields
- **Security Enhancement**: All routes now require authentication
- **Currency Display**: Changed from USD ($) to Indian Rupee (₹)
- **Enhanced Error Handling**: Improved error messages and validation

### Security
- **Authentication Protection**: All main routes require user login
- **Password Hashing**: Secure SHA-256 password storage
- **Session Security**: Secure session management with proper logout
- **Input Validation**: Enhanced form validation and sanitization

## [1.0.0] - 2024-XX-XX

### Added
- **Basic Inventory Management**: Core inventory tracking functionality
- **Product Management**: Add, edit, and manage products with SKUs
- **Store Management**: Multi-store inventory support
- **Transaction History**: Complete audit trail of inventory changes
- **Dashboard**: Basic statistics and overview
- **SQLite Database**: Local database with automatic schema creation
- **Web Interface**: Simple HTML/CSS interface

### Features
- Multi-store inventory tracking
- Product catalog management
- Stock level monitoring
- Transaction recording
- Basic reporting

---

## Version History

- **v2.0.0**: Authentication system, modern UI, advanced features
- **v1.0.0**: Basic inventory management system

## Migration Notes

### Upgrading from v1.0.0 to v2.0.0
- **Database Migration**: Users table will be automatically created
- **Authentication Required**: All routes now require login
- **Default Admin**: Username: `admin`, Password: `admin123`
- **UI Changes**: Complete interface redesign with Bootstrap 5
- **Currency**: All prices now display in Indian Rupee (₹)

For detailed upgrade instructions, see the [README.md](README.md) file.