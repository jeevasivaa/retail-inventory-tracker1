# Enhanced Flask Inventory Management System with Authentication
import sqlite3
from flask import Flask, g, render_template, request, jsonify, redirect, url_for, flash, session
from pathlib import Path
from datetime import datetime, timedelta
import json
from functools import wraps
import hashlib
import secrets

# Project DB location
DATABASE = Path("instance") / "inventory.db"
DATABASE.parent.mkdir(exist_ok=True)

app = Flask(__name__)
app.config['DATABASE'] = str(DATABASE)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.secret_key = 'your-secret-key-change-in-production'  # Required for flash messages

# --- DB helpers ---
def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        with open('schema.sql', 'r', encoding='utf-8') as f:
            db.executescript(f.read())
        
        # Add enhanced schema
        enhanced_schema = """
        -- Enhanced tables for better functionality
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            contact_email TEXT,
            contact_phone TEXT,
            address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Add columns to existing products table if they don't exist
        ALTER TABLE products ADD COLUMN category_id INTEGER REFERENCES categories(id);
        ALTER TABLE products ADD COLUMN supplier_id INTEGER REFERENCES suppliers(id);
        ALTER TABLE products ADD COLUMN cost_price DECIMAL(10,2) DEFAULT 0.00;
        ALTER TABLE products ADD COLUMN sell_price DECIMAL(10,2) DEFAULT 0.00;
        ALTER TABLE products ADD COLUMN reorder_point INTEGER DEFAULT 0;
        ALTER TABLE products ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
        
        -- Add columns to stores table
        ALTER TABLE stores ADD COLUMN manager_name TEXT;
        ALTER TABLE stores ADD COLUMN phone TEXT;
        ALTER TABLE stores ADD COLUMN email TEXT;
        ALTER TABLE stores ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
        
        -- Enhanced transactions with transaction types
        CREATE TABLE IF NOT EXISTS transaction_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT
        );
        
        INSERT OR IGNORE INTO transaction_types (name, description) VALUES 
        ('manual', 'Manual inventory adjustment'),
        ('sale', 'Product sale'),
        ('purchase', 'Stock purchase'),
        ('return', 'Product return'),
        ('damage', 'Damaged goods'),
        ('theft', 'Theft/loss'),
        ('transfer', 'Store transfer');
        
        ALTER TABLE transactions ADD COLUMN transaction_type_id INTEGER REFERENCES transaction_types(id) DEFAULT 1;
        ALTER TABLE transactions ADD COLUMN reference_number TEXT;
        ALTER TABLE transactions ADD COLUMN user_id TEXT DEFAULT 'system';
        
        -- Settings table
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT NOT NULL UNIQUE,
            value TEXT NOT NULL,
            description TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        INSERT OR IGNORE INTO settings (key, value, description) VALUES 
        ('low_stock_threshold', '10', 'Default low stock alert threshold'),
        ('auto_refresh_interval', '30', 'Auto-refresh interval in seconds'),
        ('currency_symbol', '₹', 'Currency symbol for prices'),
        ('company_name', 'Inventory Pro', 'Company name'),
        ('notifications_enabled', '1', 'Enable notifications');
        
        -- Users table for authentication
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT DEFAULT 'user' CHECK (role IN ('admin', 'manager', 'user')),
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        );
        
        -- Create default admin user (password: admin123)
        INSERT OR IGNORE INTO users (username, email, password_hash, full_name, role) VALUES 
        ('admin', 'admin@inventory.com', '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9', 'System Administrator', 'admin');
        
        -- Sample data
        INSERT OR IGNORE INTO categories (name, description) VALUES 
        ('Electronics', 'Electronic devices and accessories'),
        ('Clothing', 'Apparel and fashion items'),
        ('Books', 'Books and publications'),
        ('Food', 'Food and beverages'),
        ('Home & Garden', 'Home improvement and garden supplies');
        
        INSERT OR IGNORE INTO suppliers (name, contact_email, contact_phone) VALUES 
        ('TechCorp', 'orders@techcorp.com', '555-0101'),
        ('Fashion Plus', 'sales@fashionplus.com', '555-0102'),
        ('BookWorld', 'wholesale@bookworld.com', '555-0103');
        """
        
        try:
            db.executescript(enhanced_schema)
            db.commit()
        except sqlite3.OperationalError as e:
            # Ignore column already exists errors
            if "duplicate column name" not in str(e).lower():
                print(f"Database enhancement error: {e}")

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv

def execute_db(query, args=()):
    """Execute a database query that doesn't return results"""
    db = get_db()
    cur = db.execute(query, args)
    db.commit()
    return cur.lastrowid

# --- Authentication helpers ---
def hash_password(password):
    """Hash a password for storing in the database"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, password_hash):
    """Verify a password against its hash"""
    return hashlib.sha256(password.encode()).hexdigest() == password_hash

def login_required(f):
    """Decorator to require authentication for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Get the current logged-in user"""
    if 'user_id' in session:
        return query_db('SELECT * FROM users WHERE id = ?', (session['user_id'],), one=True)
    return None

# --- Authentication Routes ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username and password are required.', 'error')
            return render_template('login.html')
        
        # Find user by username or email
        user = query_db('SELECT * FROM users WHERE (username = ? OR email = ?) AND is_active = 1', 
                       (username, username), one=True)
        
        if user and verify_password(password, user['password_hash']):
            # Login successful
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['full_name'] = user['full_name']
            
            # Update last login
            execute_db('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user['id'],))
            
            flash(f"Welcome back, {user['full_name']}!", 'success')
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('home'))
        else:
            flash('Invalid username/email or password.', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        full_name = request.form.get('full_name')
        
        # Validation
        if not all([username, email, password, confirm_password, full_name]):
            flash('All fields are required.', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'error')
            return render_template('register.html')
        
        # Check if username or email already exists
        existing_user = query_db('SELECT id FROM users WHERE username = ? OR email = ?', 
                                (username, email), one=True)
        if existing_user:
            flash('Username or email already exists.', 'error')
            return render_template('register.html')
        
        # Create new user
        password_hash = hash_password(password)
        try:
            user_id = execute_db('''INSERT INTO users (username, email, password_hash, full_name, role) 
                                   VALUES (?, ?, ?, ?, ?)''',
                               (username, email, password_hash, full_name, 'user'))
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash('Registration failed. Please try again.', 'error')
            print(f"Registration error: {e}")
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    """User logout"""
    user_name = session.get('full_name', 'User')
    session.clear()
    flash(f'Goodbye, {user_name}! You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/profile')
@login_required
def profile():
    """User profile page"""
    user = get_current_user()
    return render_template('profile.html', user=user)

# --- Enhanced Routes / Pages ---
@app.route('/')
@login_required
def home():
    """Enhanced dashboard with statistics"""
    try:
        # Get dashboard statistics
        total_products = query_db('SELECT COUNT(*) as count FROM products')[0]['count']
        total_stores = query_db('SELECT COUNT(*) as count FROM stores')[0]['count']
        
        # Low stock alerts with safe default
        try:
            low_stock_threshold_row = query_db('SELECT value FROM settings WHERE key=?', ('low_stock_threshold',), one=True)
            low_stock_threshold = int(low_stock_threshold_row['value']) if low_stock_threshold_row else 10
        except:
            low_stock_threshold = 10
            
        low_stock_items = query_db('''
            SELECT p.id, COALESCE(SUM(i.quantity), 0) as total_quantity
            FROM products p 
            LEFT JOIN inventories i ON p.id = i.product_id 
            GROUP BY p.id
            HAVING total_quantity <= ?
        ''', (low_stock_threshold,))
        
        low_stock_count = len(low_stock_items) if low_stock_items else 0
        
        # Total inventory value with safe default
        try:
            total_value_row = query_db('''
                SELECT COALESCE(SUM(i.quantity * COALESCE(p.cost_price, 0)), 0) as value
                FROM inventories i 
                JOIN products p ON i.product_id = p.id
            ''', one=True)
            total_value = total_value_row['value'] if total_value_row else 0
        except:
            total_value = 0
    
        # Recent transactions with safe default
        try:
            recent_transactions = query_db('''
                SELECT t.*, s.name as store_name, p.name as product_name, 
                       COALESCE(tt.name, 'manual') as transaction_type
                FROM transactions t
                JOIN stores s ON t.store_id = s.id
                JOIN products p ON t.product_id = p.id
                LEFT JOIN transaction_types tt ON t.transaction_type_id = tt.id
                ORDER BY t.created_at DESC
                LIMIT 10
            ''')
        except:
            recent_transactions = []
        
        # Top products by quantity with safe default
        try:
            top_products = query_db('''
                SELECT p.name, p.sku, COALESCE(SUM(i.quantity), 0) as total_quantity
                FROM products p
                LEFT JOIN inventories i ON p.id = i.product_id
                GROUP BY p.id
                ORDER BY total_quantity DESC
                LIMIT 5
            ''')
        except:
            top_products = []
        
        return render_template('dashboard.html', 
                             total_products=total_products,
                             total_stores=total_stores,
                             low_stock_count=low_stock_count,
                             total_value=total_value,
                             recent_transactions=recent_transactions,
                             top_products=top_products)
    
    except Exception as e:
        print(f"Dashboard error: {e}")
        # Fallback to simple dashboard
        return render_template('dashboard.html', 
                             total_products=0,
                             total_stores=0,
                             low_stock_count=0,
                             total_value=0,
                             recent_transactions=[],
                             top_products=[])

@app.route('/products')
@login_required
def products_page():
    """Enhanced products page with categories and suppliers"""
    try:
        products = query_db('''
            SELECT p.*, 
                   COALESCE(c.name, '') as category_name, 
                   COALESCE(s.name, '') as supplier_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN suppliers s ON p.supplier_id = s.id
            ORDER BY COALESCE(p.created_at, p.id) DESC
        ''')
    except Exception as e:
        print(f"Products query error: {e}")
        products = query_db('SELECT * FROM products ORDER BY id DESC')
    
    try:
        categories = query_db('SELECT * FROM categories ORDER BY name')
    except:
        categories = []
    
    try:
        suppliers = query_db('SELECT * FROM suppliers ORDER BY name')
    except:
        suppliers = []
    
    return render_template('products.html', 
                         products=products, 
                         categories=categories, 
                         suppliers=suppliers,
                         categories_json=json.dumps([dict(c) for c in (categories or [])]),
                         suppliers_json=json.dumps([dict(s) for s in (suppliers or [])]))

@app.route('/stores')
@login_required
def stores_page():
    """Enhanced stores management page"""
    try:
        stores = query_db('''
            SELECT s.*, 
                   COUNT(i.id) as product_count,
                   COALESCE(SUM(i.quantity * COALESCE(p.cost_price, 0)), 0) as total_value
            FROM stores s
            LEFT JOIN inventories i ON s.id = i.store_id
            LEFT JOIN products p ON i.product_id = p.id
            GROUP BY s.id, s.name, s.location, s.manager_name, s.phone, s.email, s.created_at
            ORDER BY COALESCE(s.created_at, s.id) DESC
        ''')
    except Exception as e:
        print(f"Stores query error: {e}")
        # Fallback to simple query
        stores = query_db('SELECT *, 0 as product_count, 0 as total_value FROM stores ORDER BY id DESC')
    
    return render_template('stores.html', stores=stores)

@app.route('/store/<int:store_id>')
@login_required
def store_view(store_id):
    """Enhanced individual store view"""
    store = query_db('SELECT * FROM stores WHERE id=?', (store_id,), one=True)
    if not store:
        flash('Store not found', 'error')
        return redirect(url_for('stores_page'))
    
    # Get store statistics
    inventory_count = query_db('SELECT COUNT(*) as count FROM inventories WHERE store_id=?', (store_id,), one=True)['count']
    total_value = query_db('''
        SELECT COALESCE(SUM(i.quantity * p.cost_price), 0) as value
        FROM inventories i 
        JOIN products p ON i.product_id = p.id
        WHERE i.store_id = ?
    ''', (store_id,), one=True)['value']
    
    return render_template('store.html', 
                         store=store,
                         inventory_count=inventory_count,
                         total_value=total_value)

@app.route('/stock-receiving')
@login_required
def stock_receiving_page():
    """Stock receiving and purchase order management page"""
    try:
        # Get suppliers, stores, and products for receiving
        suppliers = query_db('SELECT * FROM suppliers ORDER BY name')
        stores = query_db('SELECT * FROM stores ORDER BY name')
        products = query_db('SELECT * FROM products ORDER BY name')
        
        # Get recent receiving history (simplified for existing schema)
        recent_receipts = query_db('''
            SELECT 
                DATE(t.created_at) as date,
                'RCV-' || t.id as reference_number,
                'supplier' as type_name,
                'supplier' as type_class,
                'fas fa-truck' as type_icon,
                s.name as store_name,
                1 as item_count,
                0 as total_value,
                'completed' as status,
                'success' as status_class,
                t.id as id
            FROM transactions t
            JOIN stores s ON t.store_id = s.id
            WHERE t.change > 0 
            ORDER BY t.created_at DESC
            LIMIT 10
        ''')
        
        from datetime import date
        today = date.today().isoformat()
        
        return render_template('stock_receiving.html',
                             suppliers=suppliers or [],
                             stores=stores or [],
                             products=products or [],
                             recent_receipts=recent_receipts or [],
                             today=today)
    except Exception as e:
        print(f"Error in stock receiving page: {e}")
        from datetime import date
        return render_template('stock_receiving.html',
                             suppliers=[], stores=[], products=[], recent_receipts=[], today=date.today().isoformat())
    except Exception as e:
        print(f"Error in stock receiving page: {e}")
        return render_template('stock_receiving.html',
                             suppliers=[], stores=[], products=[], recent_receipts=[], today=date.today().isoformat())

@app.route('/inventory-management')
@login_required
def inventory_management_page():
    """Advanced inventory management page"""
    try:
        # Get inventory with full details
        inventory_items = query_db('''
            SELECT 
                i.store_id, i.product_id, i.quantity, i.last_updated,
                s.name as store_name, s.location as store_location,
                p.name as product_name, p.sku, p.reorder_point,
                c.id as category_id, c.name as category_name
            FROM inventories i
            JOIN stores s ON i.store_id = s.id
            JOIN products p ON i.product_id = p.id
            LEFT JOIN categories c ON p.category_id = c.id
            ORDER BY s.name, p.name
        ''')
        
        stores = query_db('SELECT * FROM stores ORDER BY name')
        products = query_db('SELECT * FROM products ORDER BY name')
        categories = query_db('SELECT * FROM categories ORDER BY name')
        
        return render_template('inventory_management.html',
                             inventory_items=inventory_items or [],
                             stores=stores or [],
                             products=products or [],
                             categories=categories or [])
    except Exception as e:
        print(f"Error in inventory management: {e}")
        return render_template('inventory_management.html',
                             inventory_items=[], stores=[], products=[], categories=[])

@app.route('/inventory')
@login_required
def inventory_page():
    """New bulk inventory management page"""
    try:
        # Get all inventory with store and product details
        inventories = query_db('''
            SELECT i.*, p.name as product_name, p.sku, 
                   COALESCE(p.reorder_point, 10) as reorder_point,
                   s.name as store_name, 
                   COALESCE(c.name, 'Uncategorized') as category_name,
                   CASE WHEN i.quantity <= COALESCE(p.reorder_point, 10) THEN 1 ELSE 0 END as low_stock
            FROM inventories i
            JOIN products p ON i.product_id = p.id
            JOIN stores s ON i.store_id = s.id
            LEFT JOIN categories c ON p.category_id = c.id
            ORDER BY low_stock DESC, i.last_updated DESC
        ''')
    except Exception as e:
        print(f"Inventory page error: {e}")
        inventories = []
    
    return render_template('inventory.html', inventories=inventories)

@app.route('/reports')
@login_required
def reports_page():
    """New reports and analytics page"""
    try:
        # Inventory summary by category
        category_summary = query_db('''
            SELECT COALESCE(c.name, 'Uncategorized') as category, 
                   COUNT(DISTINCT p.id) as product_count,
                   COALESCE(SUM(i.quantity), 0) as total_quantity,
                   COALESCE(SUM(i.quantity * COALESCE(p.cost_price, 0)), 0) as total_value
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN inventories i ON p.id = i.product_id
            GROUP BY COALESCE(c.id, 0), COALESCE(c.name, 'Uncategorized')
            ORDER BY total_value DESC
        ''')
    except Exception as e:
        print(f"Category summary error: {e}")
        category_summary = []
    
    try:
        # Store summary
        store_summary = query_db('''
            SELECT s.name as store_name,
                   COUNT(DISTINCT i.product_id) as unique_products,
                   COALESCE(SUM(i.quantity), 0) as total_items,
                   COALESCE(SUM(i.quantity * COALESCE(p.cost_price, 0)), 0) as total_value
            FROM stores s
            LEFT JOIN inventories i ON s.id = i.store_id
            LEFT JOIN products p ON i.product_id = p.id
            GROUP BY s.id, s.name
            ORDER BY total_value DESC
        ''')
    except Exception as e:
        print(f"Store summary error: {e}")
        store_summary = []
    
    try:
        # Transaction summary by type
        transaction_summary = query_db('''
            SELECT COALESCE(tt.name, 'manual') as transaction_type,
                   COUNT(t.id) as transaction_count,
                   SUM(t.change) as total_change
            FROM transactions t
            LEFT JOIN transaction_types tt ON t.transaction_type_id = tt.id
            WHERE t.created_at >= date('now', '-30 days')
            GROUP BY COALESCE(tt.id, 0), COALESCE(tt.name, 'manual')
            ORDER BY transaction_count DESC
        ''')
    except Exception as e:
        print(f"Transaction summary error: {e}")
        transaction_summary = []
    
    return render_template('reports.html',
                         category_summary=category_summary,
                         store_summary=store_summary,
                         transaction_summary=transaction_summary)

@app.route('/transactions')
@login_required
def transactions_page():
    """New transaction history page"""
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page
    
    # Get filters
    store_filter = request.args.get('store', '')
    product_filter = request.args.get('product', '')
    type_filter = request.args.get('type', '')
    
    # Build query with filters
    where_conditions = []
    params = []
    
    if store_filter:
        where_conditions.append('s.name LIKE ?')
        params.append(f'%{store_filter}%')
    
    if product_filter:
        where_conditions.append('p.name LIKE ?')
        params.append(f'%{product_filter}%')
    
    if type_filter:
        where_conditions.append('COALESCE(tt.name, "manual") = ?')
        params.append(type_filter)
    
    where_clause = 'WHERE ' + ' AND '.join(where_conditions) if where_conditions else ''
    
    try:
        transactions = query_db(f'''
            SELECT t.*, s.name as store_name, p.name as product_name, p.sku,
                   COALESCE(tt.name, 'manual') as transaction_type
            FROM transactions t
            JOIN stores s ON t.store_id = s.id
            JOIN products p ON t.product_id = p.id
            LEFT JOIN transaction_types tt ON t.transaction_type_id = tt.id
            {where_clause}
            ORDER BY t.created_at DESC
            LIMIT ? OFFSET ?
        ''', params + [per_page, offset])
    except Exception as e:
        print(f"Transactions query error: {e}")
        transactions = []
    
    # Get filter options
    try:
        stores = query_db('SELECT DISTINCT name FROM stores ORDER BY name')
    except:
        stores = []
    
    try:
        transaction_types = query_db('SELECT name FROM transaction_types ORDER BY name')
    except:
        transaction_types = [{'name': 'manual'}, {'name': 'purchase'}, {'name': 'return'}]
    
    return render_template('transactions.html',
                         transactions=transactions,
                         stores=stores,
                         transaction_types=transaction_types,
                         current_filters={
                             'store': store_filter,
                             'product': product_filter,
                             'type': type_filter
                         },
                         page=page)

@app.route('/settings')
@login_required
def settings_page():
    """New settings page"""
    try:
        settings = query_db('SELECT * FROM settings ORDER BY key')
    except:
        settings = []
    
    try:
        categories = query_db('SELECT * FROM categories ORDER BY name')
    except:
        categories = []
    
    try:
        suppliers = query_db('SELECT * FROM suppliers ORDER BY name')
    except:
        suppliers = []
    
    return render_template('settings.html',
                         settings=settings,
                         categories=categories,
                         suppliers=suppliers)

# --- Enhanced API endpoints ---
@app.route('/api/inventories/<int:store_id>')
def api_inventories(store_id):
    """Get inventory for a specific store"""
    rows = query_db('''
        SELECT i.id, p.id AS product_id, p.sku, p.name, i.quantity, i.last_updated,
               p.reorder_point, c.name as category_name,
               CASE WHEN i.quantity <= p.reorder_point THEN 1 ELSE 0 END as low_stock
        FROM inventories i 
        JOIN products p ON p.id = i.product_id
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE i.store_id = ?
        ORDER BY low_stock DESC, p.name
    ''', (store_id,))
    return jsonify([dict(r) for r in rows])

@app.route('/api/inventory/update', methods=['POST'])
def api_update_inventory():
    """Enhanced inventory update with transaction types"""
    data = request.get_json(force=True)
    try:
        store_id = int(data['store_id'])
        product_id = int(data['product_id'])
        change = int(data['change'])
    except (KeyError, TypeError, ValueError):
        return jsonify({'error': 'Invalid payload'}), 400

    note = data.get('note', '')
    transaction_type = data.get('transaction_type', 'manual')
    user_id = data.get('user_id', 'system')
    
    # Get transaction type ID
    transaction_type_row = query_db('SELECT id FROM transaction_types WHERE name=?', (transaction_type,), one=True)
    transaction_type_id = transaction_type_row['id'] if transaction_type_row else 1
    
    db = get_db()
    cur = db.execute('SELECT quantity FROM inventories WHERE store_id=? AND product_id=?', (store_id, product_id))
    row = cur.fetchone()
    
    if row:
        new_qty = row['quantity'] + change
        if new_qty < 0:
            return jsonify({'error': 'Insufficient stock'}), 400
        db.execute('UPDATE inventories SET quantity=?, last_updated=CURRENT_TIMESTAMP WHERE store_id=? AND product_id=?',
                   (new_qty, store_id, product_id))
    else:
        if change < 0:
            return jsonify({'error': 'Insufficient stock'}), 400
        db.execute('INSERT INTO inventories (store_id, product_id, quantity) VALUES (?,?,?)',
                   (store_id, product_id, change))
    
    # Generate reference number
    reference_number = f'TXN-{datetime.now().strftime("%Y%m%d%H%M%S")}-{store_id}-{product_id}'
    
    db.execute('''INSERT INTO transactions 
                  (store_id, product_id, change, note, transaction_type_id, reference_number, user_id) 
                  VALUES (?,?,?,?,?,?,?)''',
               (store_id, product_id, change, note, transaction_type_id, reference_number, user_id))
    db.commit()
    
    return jsonify({'status': 'ok', 'reference_number': reference_number})

@app.route('/api/inventory/item')
def api_get_inventory_item():
    """Get specific inventory item details"""
    store_id = request.args.get('store')
    product_id = request.args.get('product')
    
    if not store_id or not product_id:
        return jsonify({'error': 'Store and product IDs are required'}), 400
    
    try:
        item = query_db('''
            SELECT 
                i.quantity, i.last_updated,
                s.name as store_name, s.location as store_location,
                p.name as product_name, p.sku, p.reorder_point
            FROM inventories i
            JOIN stores s ON i.store_id = s.id
            JOIN products p ON i.product_id = p.id
            WHERE i.store_id = ? AND i.product_id = ?
        ''', (store_id, product_id), one=True)
        
        if not item:
            # Create zero inventory record for display
            store = query_db('SELECT name, location FROM stores WHERE id = ?', (store_id,), one=True)
            product = query_db('SELECT name, sku, reorder_point FROM products WHERE id = ?', (product_id,), one=True)
            
            if not store or not product:
                return jsonify({'error': 'Store or product not found'}), 404
            
            item = {
                'quantity': 0,
                'last_updated': None,
                'store_name': store['name'],
                'store_location': store.get('location', ''),
                'product_name': product['name'],
                'sku': product['sku'],
                'reorder_point': product.get('reorder_point', 0)
            }
        
        return jsonify(dict(item))
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/inventory/add-stock', methods=['POST'])
def api_add_stock():
    """Add stock to inventory with transaction recording"""
    data = request.get_json(force=True)
    try:
        store_id = int(data['store_id'])
        product_id = int(data['product_id'])
        quantity_to_add = int(data['quantity'])
        unit_cost = float(data.get('unit_cost', 0.0))
        supplier_id = data.get('supplier_id')
        reference_number = data.get('reference_number', '')
        notes = data.get('notes', 'Stock addition')
    except (KeyError, TypeError, ValueError):
        return jsonify({'error': 'Invalid payload - missing required fields'}), 400

    if quantity_to_add <= 0:
        return jsonify({'error': 'Quantity must be positive'}), 400
    
    user_id = data.get('user_id', 'user')
    
    db = get_db()
    
    try:
        # Get current inventory
        current_inventory = query_db('SELECT quantity FROM inventories WHERE store_id=? AND product_id=?',
                                   (store_id, product_id), one=True)
        
        if current_inventory:
            # Update existing inventory
            new_quantity = current_inventory['quantity'] + quantity_to_add
            db.execute('UPDATE inventories SET quantity=?, last_updated=CURRENT_TIMESTAMP WHERE store_id=? AND product_id=?',
                      (new_quantity, store_id, product_id))
        else:
            # Create new inventory record
            new_quantity = quantity_to_add
            db.execute('INSERT INTO inventories (store_id, product_id, quantity) VALUES (?,?,?)',
                      (store_id, product_id, quantity_to_add))
        
        # Generate reference number if not provided
        if not reference_number:
            reference_number = f'ADD-{datetime.now().strftime("%Y%m%d%H%M%S")}-{store_id}-{product_id}'
        
        # Create comprehensive note with all details
        full_note = f'{notes}'
        if reference_number:
            full_note += f' | Ref: {reference_number}'
        if user_id:
            full_note += f' | User: {user_id}'
        if unit_cost > 0:
            full_note += f' | Cost: ₹{unit_cost:.2f}'
        if supplier_id:
            full_note += f' | Supplier ID: {supplier_id}'
        
        # Record transaction using existing schema
        db.execute('''INSERT INTO transactions (store_id, product_id, change, note) VALUES (?,?,?,?)''',
                   (store_id, product_id, quantity_to_add, full_note))
        
        # Update product cost if provided
        if unit_cost > 0:
            try:
                db.execute('UPDATE products SET cost_price = ? WHERE id = ?', (unit_cost, product_id))
            except sqlite3.OperationalError:
                pass  # Ignore if cost_price column doesn't exist
        
        db.commit()
        
        return jsonify({
            'status': 'ok',
            'message': f'Added {quantity_to_add} units successfully',
            'new_quantity': new_quantity,
            'reference_number': reference_number
        })
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/inventory/quick-add', methods=['POST'])
def api_quick_add_stock():
    """Quick stock addition for simple use cases"""
    data = request.get_json(force=True)
    try:
        store_id = int(data['store_id'])
        product_id = int(data['product_id'])
        quantity = int(data['quantity'])
    except (KeyError, TypeError, ValueError):
        return jsonify({'error': 'Store ID, Product ID, and Quantity are required'}), 400

    if quantity <= 0:
        return jsonify({'error': 'Quantity must be positive'}), 400
    
    notes = data.get('notes', 'Quick stock addition')
    user_id = data.get('user_id', 'user')
    unit_cost = float(data.get('unit_cost', 0.0))
    supplier_id = data.get('supplier_id')
    
    db = get_db()
    
    try:
        # Get current inventory
        current_inventory = query_db('SELECT quantity FROM inventories WHERE store_id=? AND product_id=?',
                                   (store_id, product_id), one=True)
        
        if current_inventory:
            # Update existing inventory
            new_quantity = current_inventory['quantity'] + quantity
            db.execute('UPDATE inventories SET quantity=?, last_updated=CURRENT_TIMESTAMP WHERE store_id=? AND product_id=?',
                      (new_quantity, store_id, product_id))
        else:
            # Create new inventory record
            new_quantity = quantity
            db.execute('INSERT INTO inventories (store_id, product_id, quantity) VALUES (?,?,?)',
                      (store_id, product_id, quantity))
        
        # Generate reference number
        reference_number = f'QUICK-{datetime.now().strftime("%Y%m%d%H%M%S")}-{store_id}-{product_id}'
        
        # Create comprehensive note with all details
        full_note = f'{notes} | Ref: {reference_number} | User: {user_id}'
        if unit_cost > 0:
            full_note += f' | Cost: ₹{unit_cost:.2f}'
        if supplier_id:
            full_note += f' | Supplier ID: {supplier_id}'
        
        # Record transaction using existing schema
        db.execute('''INSERT INTO transactions (store_id, product_id, change, note) VALUES (?,?,?,?)''',
                   (store_id, product_id, quantity, full_note))
        
        # Update product cost if provided
        if unit_cost > 0:
            try:
                db.execute('UPDATE products SET cost_price = ? WHERE id = ?', (unit_cost, product_id))
            except sqlite3.OperationalError:
                pass  # Ignore if cost_price column doesn't exist
        
        db.commit()
        
        return jsonify({
            'status': 'ok',
            'message': f'Added {quantity} units successfully',
            'new_quantity': new_quantity,
            'reference_number': reference_number
        })
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/inventory/bulk-add', methods=['POST'])
def api_bulk_add_stock():
    """Bulk stock addition from CSV or form data"""
    data = request.get_json(force=True)
    items = data.get('items', [])
    
    if not items:
        return jsonify({'error': 'No items provided'}), 400
    
    db = get_db()
    success_count = 0
    errors = []
    results = []
    
    for idx, item in enumerate(items):
        try:
            store_id = int(item['store_id'])
            product_id = int(item['product_id'])
            quantity = int(item['quantity'])
            unit_cost = float(item.get('unit_cost', 0.0))
            notes = item.get('notes', f'Bulk addition item {idx + 1}')
            
            if quantity <= 0:
                errors.append(f'Item {idx + 1}: Quantity must be positive')
                continue
            
            # Get current inventory
            current = query_db('SELECT quantity FROM inventories WHERE store_id=? AND product_id=?', 
                             (store_id, product_id), one=True)
            
            if current:
                new_quantity = current['quantity'] + quantity
                db.execute('UPDATE inventories SET quantity=?, last_updated=CURRENT_TIMESTAMP WHERE store_id=? AND product_id=?',
                          (new_quantity, store_id, product_id))
            else:
                new_quantity = quantity
                db.execute('INSERT INTO inventories (store_id, product_id, quantity) VALUES (?,?,?)',
                          (store_id, product_id, quantity))
            
            # Record transaction
            reference_number = f'BULK-{datetime.now().strftime("%Y%m%d%H%M%S")}-{idx + 1}'
            full_note = f'{notes} | Ref: {reference_number} | User: bulk-user'
            if unit_cost > 0:
                full_note += f' | Cost: ₹{unit_cost:.2f}'
            
            db.execute('''INSERT INTO transactions (store_id, product_id, change, note) VALUES (?,?,?,?)''',
                       (store_id, product_id, quantity, full_note))
            
            # Update cost if provided
            if unit_cost > 0:
                try:
                    db.execute('UPDATE products SET cost_price = ? WHERE id = ?', (unit_cost, product_id))
                except:
                    pass
            
            results.append({
                'item': idx + 1,
                'store_id': store_id,
                'product_id': product_id,
                'quantity_added': quantity,
                'new_quantity': new_quantity,
                'reference_number': reference_number
            })
            
            success_count += 1
            
        except Exception as e:
            errors.append(f'Item {idx + 1}: {str(e)}')
    
    db.commit()
    
    return jsonify({
        'success_count': success_count,
        'errors': errors,
        'results': results,
        'status': 'completed'
    })

@app.route('/api/alerts/low-stock')
def api_low_stock_alerts():
    """Get low stock alerts"""
    try:
        low_stock_items = query_db('''
            SELECT 
                p.id as product_id, p.name as product_name, p.sku,
                p.reorder_point,
                s.id as store_id, s.name as store_name,
                COALESCE(i.quantity, 0) as current_quantity,
                c.name as category_name,
                sup.name as supplier_name,
                CASE 
                    WHEN COALESCE(i.quantity, 0) = 0 THEN 'out_of_stock'
                    WHEN COALESCE(i.quantity, 0) <= COALESCE(p.reorder_point, 0) THEN 'low_stock'
                    ELSE 'ok'
                END as alert_level
            FROM products p
            CROSS JOIN stores s
            LEFT JOIN inventories i ON p.id = i.product_id AND s.id = i.store_id
            LEFT JOIN categories c ON p.category_id = c.id
            LEFT JOIN suppliers sup ON p.supplier_id = sup.id
            WHERE COALESCE(i.quantity, 0) <= COALESCE(p.reorder_point, 0)
            ORDER BY 
                CASE 
                    WHEN COALESCE(i.quantity, 0) = 0 THEN 1
                    WHEN COALESCE(i.quantity, 0) <= COALESCE(p.reorder_point, 0) THEN 2
                    ELSE 3
                END,
                p.name
        ''')
        
        return jsonify([dict(item) for item in (low_stock_items or [])])
    except Exception as e:
        print(f"Low stock alerts error: {e}")
        return jsonify([]), 500

@app.route('/api/alerts/reorder-suggestions')
def api_reorder_suggestions():
    """Get reorder suggestions with quantities"""
    try:
        suggestions = query_db('''
            SELECT 
                p.id as product_id, p.name as product_name, p.sku,
                p.reorder_point,
                s.id as store_id, s.name as store_name,
                COALESCE(i.quantity, 0) as current_quantity,
                sup.name as supplier_name, sup.id as supplier_id,
                GREATEST(COALESCE(p.reorder_point, 0) * 2 - COALESCE(i.quantity, 0), 1) as suggested_quantity,
                COALESCE(p.cost_price, 0) as unit_cost
            FROM products p
            CROSS JOIN stores s
            LEFT JOIN inventories i ON p.id = i.product_id AND s.id = i.store_id
            LEFT JOIN suppliers sup ON p.supplier_id = sup.id
            WHERE COALESCE(i.quantity, 0) <= COALESCE(p.reorder_point, 0)
              AND COALESCE(p.reorder_point, 0) > 0
            ORDER BY 
                CASE WHEN COALESCE(i.quantity, 0) = 0 THEN 1 ELSE 2 END,
                p.name
        ''')
        
        return jsonify([dict(item) for item in (suggestions or [])])
    except Exception as e:
        print(f"Reorder suggestions error: {e}")
        return jsonify([]), 500

@app.route('/api/inventory/stock-level', methods=['POST'])
def api_set_stock_level():
    """Set specific stock level for a product in a store"""
    data = request.get_json(force=True)
    try:
        store_id = int(data['store_id'])
        product_id = int(data['product_id'])
        new_quantity = int(data['quantity'])
    except (KeyError, TypeError, ValueError):
        return jsonify({'error': 'Invalid payload'}), 400

    note = data.get('note', 'Stock level adjustment')
    transaction_type = data.get('transaction_type', 'manual')
    user_id = data.get('user_id', 'system')
    
    if new_quantity < 0:
        return jsonify({'error': 'Quantity cannot be negative'}), 400
    
    # Get transaction type ID
    transaction_type_row = query_db('SELECT id FROM transaction_types WHERE name=?', (transaction_type,), one=True)
    transaction_type_id = transaction_type_row['id'] if transaction_type_row else 1
    
    db = get_db()
    
    try:
        # Get current quantity
        cur = db.execute('SELECT quantity FROM inventories WHERE store_id=? AND product_id=?', (store_id, product_id))
        row = cur.fetchone()
        
        if row:
            old_quantity = row['quantity']
            change = new_quantity - old_quantity
            db.execute('UPDATE inventories SET quantity=?, last_updated=CURRENT_TIMESTAMP WHERE store_id=? AND product_id=?',
                       (new_quantity, store_id, product_id))
        else:
            old_quantity = 0
            change = new_quantity
            db.execute('INSERT INTO inventories (store_id, product_id, quantity) VALUES (?,?,?)',
                       (store_id, product_id, new_quantity))
        
        # Record transaction if there's a change
        if change != 0:
            reference_number = f'ADJ-{datetime.now().strftime("%Y%m%d%H%M%S")}-{store_id}-{product_id}'
            db.execute('''INSERT INTO transactions 
                          (store_id, product_id, change, note, transaction_type_id, reference_number, user_id) 
                          VALUES (?,?,?,?,?,?,?)''',
                       (store_id, product_id, change, note, transaction_type_id, reference_number, user_id))
        
        db.commit()
        return jsonify({
            'status': 'ok', 
            'old_quantity': old_quantity,
            'new_quantity': new_quantity,
            'change': change,
            'message': f'Stock level set to {new_quantity}'
        })
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/inventory/reorder-point', methods=['POST'])
def api_set_reorder_point():
    """Set reorder point for a product"""
    data = request.get_json(force=True)
    try:
        product_id = int(data['product_id'])
        reorder_point = int(data['reorder_point'])
    except (KeyError, TypeError, ValueError):
        return jsonify({'error': 'Invalid payload'}), 400
    
    if reorder_point < 0:
        return jsonify({'error': 'Reorder point cannot be negative'}), 400
    
    try:
        # Check if product exists
        product = query_db('SELECT * FROM products WHERE id=?', (product_id,), one=True)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        # Update reorder point
        try:
            execute_db('UPDATE products SET reorder_point = ? WHERE id = ?', (reorder_point, product_id))
        except sqlite3.OperationalError:
            # Column might not exist in older schema
            return jsonify({'error': 'Reorder point feature not available'}), 400
        
        return jsonify({
            'status': 'ok',
            'product_id': product_id,
            'reorder_point': reorder_point,
            'message': f'Reorder point set to {reorder_point}'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/transaction/<int:transaction_id>', methods=['DELETE'])
def api_delete_transaction(transaction_id):
    """Delete a transaction (admin only)"""
    try:
        # Check if transaction exists
        transaction = query_db('SELECT * FROM transactions WHERE id=?', (transaction_id,), one=True)
        if not transaction:
            return jsonify({'error': 'Transaction not found'}), 404
        
        # Reverse the inventory change
        db = get_db()
        
        # Get current inventory
        current_inventory = query_db('SELECT quantity FROM inventories WHERE store_id=? AND product_id=?',
                                   (transaction['store_id'], transaction['product_id']), one=True)
        
        if current_inventory:
            # Reverse the change
            new_quantity = current_inventory['quantity'] - transaction['change']
            if new_quantity < 0:
                return jsonify({'error': 'Cannot delete transaction: would result in negative inventory'}), 400
            
            if new_quantity == 0:
                db.execute('DELETE FROM inventories WHERE store_id=? AND product_id=?',
                          (transaction['store_id'], transaction['product_id']))
            else:
                db.execute('UPDATE inventories SET quantity=?, last_updated=CURRENT_TIMESTAMP WHERE store_id=? AND product_id=?',
                          (new_quantity, transaction['store_id'], transaction['product_id']))
        
        # Delete the transaction
        db.execute('DELETE FROM transactions WHERE id = ?', (transaction_id,))
        db.commit()
        
        return jsonify({'status': 'ok', 'message': 'Transaction deleted and inventory adjusted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/inventory/transfer', methods=['POST'])
def api_transfer_inventory():
    """Transfer inventory between stores"""
    data = request.get_json(force=True)
    try:
        from_store_id = int(data['from_store_id'])
        to_store_id = int(data['to_store_id'])
        product_id = int(data['product_id'])
        quantity = int(data['quantity'])
    except (KeyError, TypeError, ValueError):
        return jsonify({'error': 'Invalid payload'}), 400
    
    if quantity <= 0:
        return jsonify({'error': 'Quantity must be positive'}), 400
    
    note = data.get('note', f'Transfer between stores')
    user_id = data.get('user_id', 'system')
    
    # Get transaction type ID for transfer
    transaction_type_row = query_db('SELECT id FROM transaction_types WHERE name=?', ('transfer',), one=True)
    transaction_type_id = transaction_type_row['id'] if transaction_type_row else 1
    
    db = get_db()
    
    try:
        # Check source inventory
        source_inventory = query_db('SELECT quantity FROM inventories WHERE store_id=? AND product_id=?',
                                   (from_store_id, product_id), one=True)
        
        if not source_inventory or source_inventory['quantity'] < quantity:
            return jsonify({'error': 'Insufficient inventory in source store'}), 400
        
        # Reduce from source store
        new_source_qty = source_inventory['quantity'] - quantity
        if new_source_qty == 0:
            db.execute('DELETE FROM inventories WHERE store_id=? AND product_id=?', (from_store_id, product_id))
        else:
            db.execute('UPDATE inventories SET quantity=?, last_updated=CURRENT_TIMESTAMP WHERE store_id=? AND product_id=?',
                      (new_source_qty, from_store_id, product_id))
        
        # Add to destination store
        dest_inventory = query_db('SELECT quantity FROM inventories WHERE store_id=? AND product_id=?',
                                 (to_store_id, product_id), one=True)
        
        if dest_inventory:
            new_dest_qty = dest_inventory['quantity'] + quantity
            db.execute('UPDATE inventories SET quantity=?, last_updated=CURRENT_TIMESTAMP WHERE store_id=? AND product_id=?',
                      (new_dest_qty, to_store_id, product_id))
        else:
            db.execute('INSERT INTO inventories (store_id, product_id, quantity) VALUES (?,?,?)',
                      (to_store_id, product_id, quantity))
        
        # Record transactions
        reference_number = f'TRANSFER-{datetime.now().strftime("%Y%m%d%H%M%S")}-{from_store_id}-{to_store_id}'
        
        # Outbound transaction
        db.execute('''INSERT INTO transactions 
                      (store_id, product_id, change, note, transaction_type_id, reference_number, user_id) 
                      VALUES (?,?,?,?,?,?,?)''',
                   (from_store_id, product_id, -quantity, f'{note} (OUT)', transaction_type_id, reference_number, user_id))
        
        # Inbound transaction
        db.execute('''INSERT INTO transactions 
                      (store_id, product_id, change, note, transaction_type_id, reference_number, user_id) 
                      VALUES (?,?,?,?,?,?,?)''',
                   (to_store_id, product_id, quantity, f'{note} (IN)', transaction_type_id, reference_number, user_id))
        
        db.commit()
        
        return jsonify({
            'status': 'ok',
            'reference_number': reference_number,
            'message': f'Transferred {quantity} units from store {from_store_id} to store {to_store_id}'
        })
    except Exception as e:
        db.rollback()
        return jsonify({'error': str(e)}), 400

@app.route('/api/product', methods=['POST'])
def api_create_product():
    """Enhanced product creation"""
    data = request.form if request.form else request.get_json()
    sku = data.get('sku')
    name = data.get('name')
    desc = data.get('description', '')
    category_id = data.get('category_id')
    supplier_id = data.get('supplier_id')
    cost_price = data.get('cost_price', 0.00)
    sell_price = data.get('sell_price', 0.00)
    reorder_point = data.get('reorder_point', 0)
    
    if not sku or not name:
        if request.is_json:
            return jsonify({'error': 'SKU and name are required'}), 400
        flash('SKU and name are required', 'error')
        return redirect(url_for('products_page'))
    
    try:
        product_id = execute_db('''INSERT INTO products 
                      (sku, name, description, category_id, supplier_id, cost_price, sell_price, reorder_point) 
                      VALUES (?,?,?,?,?,?,?,?)''', 
                   (sku, name, desc, category_id or None, supplier_id or None, 
                    float(cost_price), float(sell_price), int(reorder_point)))
        
        if request.is_json:
            return jsonify({'status': 'ok', 'id': product_id, 'message': 'Product created successfully'})
        flash('Product added successfully', 'success')
    except sqlite3.IntegrityError:
        if request.is_json:
            return jsonify({'error': 'SKU already exists'}), 400
        flash('Error: SKU already exists', 'error')
    except Exception as e:
        if request.is_json:
            return jsonify({'error': str(e)}), 400
        flash(f'Error: {e}', 'error')
    
    return redirect(url_for('products_page'))

@app.route('/api/product/<int:product_id>', methods=['GET'])
def api_get_product(product_id):
    """Get individual product data"""
    try:
        product = query_db('''
            SELECT p.*, c.name as category_name, s.name as supplier_name
            FROM products p 
            LEFT JOIN categories c ON p.category_id = c.id 
            LEFT JOIN suppliers s ON p.supplier_id = s.id
            WHERE p.id = ?
        ''', (product_id,), one=True)
        
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        return jsonify(dict(product))
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/product/<int:product_id>', methods=['PUT'])
def api_update_product(product_id):
    """Update existing product"""
    data = request.get_json()
    
    # Check if product exists
    product = query_db('SELECT * FROM products WHERE id=?', (product_id,), one=True)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    # Build update query dynamically
    update_fields = []
    params = []
    
    for field in ['sku', 'name', 'description', 'category_id', 'supplier_id', 'cost_price', 'sell_price', 'reorder_point']:
        if field in data:
            update_fields.append(f'{field} = ?')
            params.append(data[field])
    
    if not update_fields:
        return jsonify({'error': 'No fields to update'}), 400
    
    params.append(product_id)
    
    try:
        execute_db(f'UPDATE products SET {', '.join(update_fields)} WHERE id = ?', params)
        return jsonify({'status': 'ok', 'message': 'Product updated successfully'})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'SKU already exists'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/product/<int:product_id>', methods=['DELETE'])
def api_delete_product(product_id):
    """Delete product"""
    try:
        # Check if product exists
        product = query_db('SELECT * FROM products WHERE id=?', (product_id,), one=True)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        
        # Delete related data first
        execute_db('DELETE FROM inventories WHERE product_id = ?', (product_id,))
        execute_db('DELETE FROM transactions WHERE product_id = ?', (product_id,))
        execute_db('DELETE FROM products WHERE id = ?', (product_id,))
        
        return jsonify({'status': 'ok', 'message': 'Product deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/store', methods=['POST'])
def api_create_store():
    """Enhanced store creation"""
    data = request.form if request.form else request.get_json()
    name = data.get('name')
    location = data.get('location', '')
    manager_name = data.get('manager_name', '')
    phone = data.get('phone', '')
    email = data.get('email', '')
    
    if not name:
        if request.is_json:
            return jsonify({'error': 'Store name is required'}), 400
        flash('Store name is required', 'error')
        return redirect(url_for('stores_page'))
    
    try:
        # First try with all columns
        try:
            store_id = execute_db('INSERT INTO stores (name, location, manager_name, phone, email) VALUES (?,?,?,?,?)', 
                       (name, location, manager_name, phone, email))
        except sqlite3.OperationalError:
            # Fallback to basic columns if enhanced columns don't exist
            store_id = execute_db('INSERT INTO stores (name, location) VALUES (?,?)', 
                       (name, location))
        
        if request.is_json:
            return jsonify({'status': 'ok', 'id': store_id, 'message': 'Store created successfully'})
        flash('Store added successfully', 'success')
    except sqlite3.IntegrityError:
        if request.is_json:
            return jsonify({'error': 'Store name already exists'}), 400
        flash('Error: Store name already exists', 'error')
    except Exception as e:
        if request.is_json:
            return jsonify({'error': str(e)}), 400
        flash(f'Error: {e}', 'error')
    
    return redirect(url_for('stores_page'))

@app.route('/api/stores')
def api_get_stores():
    """Get all stores"""
    try:
        stores = query_db('SELECT id, name, location FROM stores ORDER BY name')
        return jsonify([dict(s) for s in (stores or [])])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/store/<int:store_id>', methods=['GET'])
def api_get_store(store_id):
    """Get individual store data"""
    try:
        store = query_db('SELECT * FROM stores WHERE id = ?', (store_id,), one=True)
        
        if not store:
            return jsonify({'error': 'Store not found'}), 404
        
        return jsonify(dict(store))
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/store/<int:store_id>', methods=['PUT'])
def api_update_store(store_id):
    """Update existing store"""
    data = request.get_json()
    
    # Check if store exists
    store = query_db('SELECT * FROM stores WHERE id=?', (store_id,), one=True)
    if not store:
        return jsonify({'error': 'Store not found'}), 404
    
    # Build update query dynamically
    update_fields = []
    params = []
    
    for field in ['name', 'location', 'manager_name', 'phone', 'email']:
        if field in data:
            update_fields.append(f'{field} = ?')
            params.append(data[field])
    
    if not update_fields:
        return jsonify({'error': 'No fields to update'}), 400
    
    params.append(store_id)
    
    try:
        execute_db(f'UPDATE stores SET {', '.join(update_fields)} WHERE id = ?', params)
        return jsonify({'status': 'ok', 'message': 'Store updated successfully'})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Store name already exists'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/store/<int:store_id>', methods=['DELETE'])
def api_delete_store(store_id):
    """Delete store"""
    try:
        # Check if store exists
        store = query_db('SELECT * FROM stores WHERE id=?', (store_id,), one=True)
        if not store:
            return jsonify({'error': 'Store not found'}), 404
        
        # Delete related data first
        execute_db('DELETE FROM inventories WHERE store_id = ?', (store_id,))
        execute_db('DELETE FROM transactions WHERE store_id = ?', (store_id,))
        execute_db('DELETE FROM stores WHERE id = ?', (store_id,))
        
        return jsonify({'status': 'ok', 'message': 'Store deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/category', methods=['POST'])
def api_create_category():
    """New category creation endpoint"""
    data = request.get_json() if request.is_json else request.form
    name = data.get('name')
    description = data.get('description', '')
    
    if not name:
        return jsonify({'error': 'Category name is required'}), 400
    
    try:
        category_id = execute_db('INSERT INTO categories (name, description) VALUES (?,?)', (name, description))
        return jsonify({'status': 'ok', 'id': category_id, 'message': 'Category created successfully'})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Category name already exists'}), 400

@app.route('/api/category/<int:category_id>', methods=['PUT'])
def api_update_category(category_id):
    """Update existing category"""
    data = request.get_json()
    
    # Check if category exists
    category = query_db('SELECT * FROM categories WHERE id=?', (category_id,), one=True)
    if not category:
        return jsonify({'error': 'Category not found'}), 404
    
    # Build update query dynamically
    update_fields = []
    params = []
    
    for field in ['name', 'description']:
        if field in data:
            update_fields.append(f'{field} = ?')
            params.append(data[field])
    
    if not update_fields:
        return jsonify({'error': 'No fields to update'}), 400
    
    params.append(category_id)
    
    try:
        execute_db(f'UPDATE categories SET {', '.join(update_fields)} WHERE id = ?', params)
        return jsonify({'status': 'ok', 'message': 'Category updated successfully'})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Category name already exists'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/category/<int:category_id>', methods=['DELETE'])
def api_delete_category(category_id):
    """Delete category"""
    try:
        # Check if category exists
        category = query_db('SELECT * FROM categories WHERE id=?', (category_id,), one=True)
        if not category:
            return jsonify({'error': 'Category not found'}), 404
        
        # Check if category is being used
        products_using = query_db('SELECT COUNT(*) as count FROM products WHERE category_id = ?', (category_id,), one=True)
        if products_using and products_using['count'] > 0:
            return jsonify({'error': f'Cannot delete category. {products_using["count"]} products are using this category.'}), 400
        
        execute_db('DELETE FROM categories WHERE id = ?', (category_id,))
        return jsonify({'status': 'ok', 'message': 'Category deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/supplier/<int:supplier_id>', methods=['PUT'])
def api_update_supplier(supplier_id):
    """Update existing supplier"""
    data = request.get_json()
    
    # Check if supplier exists
    supplier = query_db('SELECT * FROM suppliers WHERE id=?', (supplier_id,), one=True)
    if not supplier:
        return jsonify({'error': 'Supplier not found'}), 404
    
    # Build update query dynamically
    update_fields = []
    params = []
    
    for field in ['name', 'contact_email', 'contact_phone', 'address']:
        if field in data:
            update_fields.append(f'{field} = ?')
            params.append(data[field])
    
    if not update_fields:
        return jsonify({'error': 'No fields to update'}), 400
    
    params.append(supplier_id)
    
    try:
        execute_db(f'UPDATE suppliers SET {', '.join(update_fields)} WHERE id = ?', params)
        return jsonify({'status': 'ok', 'message': 'Supplier updated successfully'})
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Supplier name already exists'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/supplier/<int:supplier_id>', methods=['DELETE'])
def api_delete_supplier(supplier_id):
    """Delete supplier"""
    try:
        # Check if supplier exists
        supplier = query_db('SELECT * FROM suppliers WHERE id=?', (supplier_id,), one=True)
        if not supplier:
            return jsonify({'error': 'Supplier not found'}), 404
        
        # Check if supplier is being used
        products_using = query_db('SELECT COUNT(*) as count FROM products WHERE supplier_id = ?', (supplier_id,), one=True)
        if products_using and products_using['count'] > 0:
            return jsonify({'error': f'Cannot delete supplier. {products_using["count"]} products are using this supplier.'}), 400
        
        execute_db('DELETE FROM suppliers WHERE id = ?', (supplier_id,))
        return jsonify({'status': 'ok', 'message': 'Supplier deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/transactions')
def api_transactions():
    """Enhanced transactions endpoint with filtering"""
    limit = min(int(request.args.get('limit', 200)), 1000)  # Max 1000 records
    store_id = request.args.get('store_id')
    product_id = request.args.get('product_id')
    transaction_type = request.args.get('transaction_type')
    days = int(request.args.get('days', 30))
    
    where_conditions = ['t.created_at >= date("now", "-' + str(days) + ' days")']
    params = []
    
    if store_id:
        where_conditions.append('t.store_id = ?')
        params.append(store_id)
    
    if product_id:
        where_conditions.append('t.product_id = ?')
        params.append(product_id)
    
    if transaction_type:
        where_conditions.append('tt.name = ?')
        params.append(transaction_type)
    
    where_clause = 'WHERE ' + ' AND '.join(where_conditions)
    params.append(limit)
    
    rows = query_db(f'''
        SELECT t.*, s.name AS store_name, p.sku, p.name AS product_name, 
               tt.name as transaction_type, t.reference_number
        FROM transactions t
        JOIN stores s ON s.id = t.store_id
        JOIN products p ON p.id = t.product_id
        JOIN transaction_types tt ON t.transaction_type_id = tt.id
        {where_clause}
        ORDER BY t.created_at DESC
        LIMIT ?
    ''', params)
    
    return jsonify([dict(r) for r in rows])

@app.route('/api/analytics/dashboard')
def api_analytics_dashboard():
    """New analytics endpoint for dashboard"""
    try:
        # Sales by month (last 6 months) - simplified for initial version
        sales_data = []
        
        # Inventory turnover - simplified
        turnover_data = query_db('''
            SELECT p.name, p.sku,
                   COALESCE(SUM(i.quantity), 0) as current_stock
            FROM products p
            LEFT JOIN inventories i ON p.id = i.product_id
            GROUP BY p.id
            ORDER BY current_stock DESC
            LIMIT 10
        ''')
        
        # Low stock alerts with safe default
        try:
            low_stock_threshold_row = query_db('SELECT value FROM settings WHERE key=?', ('low_stock_threshold',), one=True)
            low_stock_threshold = int(low_stock_threshold_row['value']) if low_stock_threshold_row else 10
        except:
            low_stock_threshold = 10
            
        low_stock_data = query_db('''
            SELECT p.name, p.sku, COALESCE(SUM(i.quantity), 0) as current_stock, 
                   COALESCE(p.reorder_point, 10) as reorder_point
            FROM products p
            LEFT JOIN inventories i ON p.id = i.product_id
            GROUP BY p.id
            HAVING current_stock <= COALESCE(p.reorder_point, ?) OR current_stock <= ?
            ORDER BY current_stock ASC
            LIMIT 20
        ''', (low_stock_threshold, low_stock_threshold))
        
        return jsonify({
            'sales_data': sales_data,
            'turnover_data': [dict(r) for r in turnover_data],
            'low_stock_data': [dict(r) for r in low_stock_data]
        })
    except Exception as e:
        print(f"Analytics error: {e}")
        return jsonify({
            'sales_data': [],
            'turnover_data': [],
            'low_stock_data': []
        })

@app.route('/api/search')
def api_search():
    """New global search endpoint"""
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify({'results': []})
    
    # Search products
    products = query_db('''
        SELECT 'product' as type, id, sku as code, name, description
        FROM products 
        WHERE name LIKE ? OR sku LIKE ? OR description LIKE ?
        LIMIT 10
    ''', (f'%{query}%', f'%{query}%', f'%{query}%'))
    
    # Search stores
    stores = query_db('''
        SELECT 'store' as type, id, name, location as code, location as description
        FROM stores 
        WHERE name LIKE ? OR location LIKE ?
        LIMIT 5
    ''', (f'%{query}%', f'%{query}%'))
    
    results = [dict(r) for r in products] + [dict(r) for r in stores]
    
    return jsonify({'results': results})

@app.route('/api/settings/update', methods=['POST'])
def api_update_settings():
    """Update system settings"""
    data = request.get_json(force=True)
    
    for key, value in data.items():
        execute_db('UPDATE settings SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE key = ?', 
                   (str(value), key))
    
    return jsonify({'status': 'ok', 'message': 'Settings updated successfully'})

@app.route('/api/realtime-data')
def api_realtime_data():
    """Real-time data for dashboard updates with error handling"""
    try:
        # Get recent transaction count (last 5 minutes)
        try:
            recent_transactions = query_db('''
                SELECT COUNT(*) as count FROM transactions 
                WHERE created_at >= datetime('now', '-5 minutes')
            ''', one=True)['count']
        except:
            recent_transactions = 0
        
        # Low stock count with fallback
        try:
            low_stock_threshold = int(query_db('SELECT value FROM settings WHERE key=?', ('low_stock_threshold',), one=True)['value'])
        except:
            low_stock_threshold = 5  # Default threshold
        
        try:
            low_stock_count = query_db('''
                SELECT COUNT(*) as count FROM (
                    SELECT p.id
                    FROM products p
                    LEFT JOIN inventories i ON p.id = i.product_id
                    GROUP BY p.id
                    HAVING COALESCE(SUM(i.quantity), 0) <= COALESCE(p.reorder_point, ?)
                       AND COALESCE(SUM(i.quantity), 0) > 0
                ) as low_stock
            ''', (low_stock_threshold,), one=True)['count']
        except:
            low_stock_count = 0
        
        notifications = recent_transactions + low_stock_count
        
        return jsonify({
            'notifications': notifications,
            'total_products': query_db('SELECT COUNT(*) as count FROM products', one=True)['count'],
            'total_stores': query_db('SELECT COUNT(*) as count FROM stores', one=True)['count'],
            'recent_transactions': recent_transactions,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"Realtime data error: {e}")
        return jsonify({
            'notifications': 0,
            'total_products': 0,
            'total_stores': 0,
            'recent_transactions': 0,
            'timestamp': datetime.now().isoformat()
        })

@app.route('/api/report/summary')
def api_report_summary():
    """Enhanced summary report"""
    try:
        rows = query_db('''
            SELECT p.id AS product_id, p.sku, p.name, 
                   COALESCE(SUM(i.quantity), 0) AS total_quantity,
                   COALESCE(p.reorder_point, 0) as reorder_point,
                   CASE WHEN COALESCE(SUM(i.quantity), 0) <= COALESCE(p.reorder_point, 0) AND COALESCE(SUM(i.quantity), 0) > 0 THEN 1 ELSE 0 END as low_stock,
                   COALESCE(c.name, '') as category_name
            FROM products p 
            LEFT JOIN inventories i ON p.id = i.product_id
            LEFT JOIN categories c ON p.category_id = c.id
            GROUP BY p.id
            ORDER BY low_stock DESC, total_quantity ASC
        ''')
        return jsonify([dict(r) for r in (rows or [])])
    except Exception as e:
        print(f"Report summary error: {e}")
        return jsonify([]), 500

if __name__ == '__main__':
    if not DATABASE.exists():
        init_db()
        print('✅ Initialized enhanced database at', DATABASE)
    else:
        # Update existing database with enhancements
        with app.app_context():
            try:
                init_db()
                print('✅ Enhanced existing database at', DATABASE)
            except Exception as e:
                print(f'⚠️  Database enhancement note: {e}')
    
    print('🚀 Starting Enhanced Inventory Management System...')
    app.run(debug=True, host='0.0.0.0', port=5000)
