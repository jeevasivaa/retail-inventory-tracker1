#!/usr/bin/env python3
"""
Add sample data to the inventory database for testing
"""
import sqlite3
from pathlib import Path

DATABASE = Path("instance") / "inventory.db"

def add_sample_data():
    db = sqlite3.connect(str(DATABASE))
    db.row_factory = sqlite3.Row
    
    try:
        # Add sample categories
        categories = [
            ('Electronics', 'Electronic devices and accessories'),
            ('Clothing', 'Apparel and fashion items'),
            ('Books', 'Books and publications'),
            ('Food', 'Food and beverages'),
            ('Home & Garden', 'Home improvement and garden supplies')
        ]
        
        for name, desc in categories:
            try:
                db.execute('INSERT INTO categories (name, description) VALUES (?,?)', (name, desc))
            except sqlite3.IntegrityError:
                pass  # Already exists
        
        # Add sample suppliers
        suppliers = [
            ('TechCorp', 'orders@techcorp.com', '555-0101'),
            ('Fashion Plus', 'sales@fashionplus.com', '555-0102'),
            ('BookWorld', 'wholesale@bookworld.com', '555-0103'),
            ('FoodMart Wholesale', 'orders@foodmart.com', '555-0104'),
            ('Garden Supply Co', 'sales@gardensupply.com', '555-0105')
        ]
        
        for name, email, phone in suppliers:
            try:
                db.execute('INSERT INTO suppliers (name, contact_email, contact_phone) VALUES (?,?,?)', 
                          (name, email, phone))
            except sqlite3.IntegrityError:
                pass  # Already exists
        
        # Add sample stores (with basic columns that exist)
        stores = [
            ('Downtown Branch', '123 Main St, Downtown'),
            ('Mall Location', '456 Shopping Mall, Level 2'),
            ('Warehouse Store', '789 Industrial Ave')
        ]
        
        for name, location in stores:
            try:
                db.execute('INSERT INTO stores (name, location) VALUES (?,?)', 
                          (name, location))
            except sqlite3.IntegrityError:
                pass  # Already exists
        
        # Add sample products (with basic columns)
        products = [
            ('ELEC-001', 'Bluetooth Headphones', 'High-quality wireless headphones'),
            ('ELEC-002', 'Smartphone Case', 'Protective case for smartphones'),
            ('CLOTH-001', 'Cotton T-Shirt', 'Comfortable cotton t-shirt'),
            ('CLOTH-002', 'Jeans', 'Classic blue jeans'),
            ('BOOK-001', 'Python Programming', 'Learn Python programming'),
            ('BOOK-002', 'Web Development Guide', 'Complete guide to web development'),
            ('FOOD-001', 'Organic Apples', 'Fresh organic apples (per lb)'),
            ('FOOD-002', 'Whole Grain Bread', 'Healthy whole grain bread'),
            ('HOME-001', 'Garden Hose', '50ft garden hose'),
            ('HOME-002', 'Plant Fertilizer', 'All-purpose plant fertilizer')
        ]
        
        for sku, name, desc in products:
            try:
                db.execute('INSERT INTO products (sku, name, description) VALUES (?,?,?)', 
                          (sku, name, desc))
            except sqlite3.IntegrityError:
                pass  # Already exists
        
        # Add sample inventory
        # Get product and store IDs first
        products_data = db.execute('SELECT id, sku FROM products').fetchall()
        stores_data = db.execute('SELECT id, name FROM stores').fetchall()
        
        if products_data and stores_data:
            import random
            
            for product in products_data:
                for store in stores_data:
                    # Random inventory between 0-100
                    quantity = random.randint(0, 100)
                    try:
                        db.execute('INSERT INTO inventories (store_id, product_id, quantity) VALUES (?,?,?)', 
                                  (store['id'], product['id'], quantity))
                    except sqlite3.IntegrityError:
                        pass  # Already exists
        
        # Add sample transactions (with basic schema)
        if products_data and stores_data:
            import random
            from datetime import datetime, timedelta
            
            for _ in range(20):  # Add 20 random transactions
                product = random.choice(products_data)
                store = random.choice(stores_data)
                change = random.randint(-10, 20)  # More additions than subtractions
                
                try:
                    db.execute('INSERT INTO transactions (store_id, product_id, change, note) VALUES (?,?,?,?)', 
                              (store['id'], product['id'], change, 'Sample transaction'))
                except sqlite3.IntegrityError:
                    pass  # Skip on error
        
        db.commit()
        print("✅ Sample data added successfully!")
        
        # Print summary
        counts = {
            'categories': db.execute('SELECT COUNT(*) as count FROM categories').fetchone()['count'],
            'suppliers': db.execute('SELECT COUNT(*) as count FROM suppliers').fetchone()['count'],
            'stores': db.execute('SELECT COUNT(*) as count FROM stores').fetchone()['count'],
            'products': db.execute('SELECT COUNT(*) as count FROM products').fetchone()['count'],
            'inventory_items': db.execute('SELECT COUNT(*) as count FROM inventories').fetchone()['count'],
            'transactions': db.execute('SELECT COUNT(*) as count FROM transactions').fetchone()['count']
        }
        
        print("📊 Database Summary:")
        for table, count in counts.items():
            print(f"   {table.title()}: {count}")
        
    except Exception as e:
        print(f"❌ Error adding sample data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == '__main__':
    add_sample_data()