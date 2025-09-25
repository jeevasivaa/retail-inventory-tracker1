// Modern Inventory Management App
class InventoryApp {
  constructor() {
    this.init();
  }

  init() {
    this.bindEventListeners();
    this.initializeComponents();
    this.showLoadingComplete();
  }

  bindEventListeners() {
    // Sidebar toggle for mobile
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.sidebar');
    
    if (sidebarToggle) {
      sidebarToggle.addEventListener('click', () => {
        sidebar.classList.toggle('open');
      });
    }

    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', (e) => {
      if (window.innerWidth <= 1024 && 
          !sidebar.contains(e.target) && 
          !sidebarToggle.contains(e.target) &&
          sidebar.classList.contains('open')) {
        sidebar.classList.remove('open');
      }
    });

    // Quick Add Modal
    this.initQuickAddModal();

    // Global search
    this.initGlobalSearch();

    // Flash message close buttons
    this.initFlashMessages();

    // Form validation
    this.initFormValidation();

    // AJAX forms
    this.initAjaxForms();

    // Auto-refresh functionality
    this.initAutoRefresh();

    // Keyboard shortcuts
    this.initKeyboardShortcuts();

    // Tooltips
    this.initTooltips();
  }

  initializeComponents() {
    // Initialize any charts or widgets
    this.initCharts();
    
    // Initialize data tables
    this.initDataTables();
    
    // Initialize real-time updates
    this.initRealTimeUpdates();
  }

  // Quick Add Modal functionality
  initQuickAddModal() {
    const quickAddBtn = document.getElementById('quickAddBtn');
    const modal = document.getElementById('quickAddModal');
    const closeModal = document.getElementById('closeModal');
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    if (quickAddBtn && modal) {
      quickAddBtn.addEventListener('click', () => {
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
      });

      closeModal.addEventListener('click', () => {
        modal.classList.remove('show');
        document.body.style.overflow = 'auto';
      });

      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          modal.classList.remove('show');
          document.body.style.overflow = 'auto';
        }
      });

      // Tab switching
      tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
          const tabName = btn.dataset.tab;
          
          // Update buttons
          tabBtns.forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          
          // Update content
          tabContents.forEach(content => {
            content.classList.remove('active');
            if (content.id === tabName + 'Tab') {
              content.classList.add('active');
            }
          });
        });
      });

      // Form submissions
      this.handleQuickAddForms();
    }
  }

  handleQuickAddForms() {
    const productForm = document.getElementById('quickAddProductForm');
    const storeForm = document.getElementById('quickAddStoreForm');

    if (productForm) {
      productForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await this.submitQuickAddForm(productForm, '/api/product');
      });
    }

    if (storeForm) {
      storeForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await this.submitQuickAddForm(storeForm, '/api/store');
      });
    }
  }

  async submitQuickAddForm(form, endpoint) {
    const formData = new FormData(form);
    
    try {
      this.showLoading();
      
      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        this.showAlert('success', 'Item added successfully!');
        form.reset();
        document.getElementById('quickAddModal').classList.remove('show');
        document.body.style.overflow = 'auto';
        
        // Refresh current page data
        this.refreshPageData();
      } else {
        const errorText = await response.text();
        this.showAlert('error', errorText || 'Failed to add item');
      }
    } catch (error) {
      this.showAlert('error', 'Network error occurred');
      console.error('Form submission error:', error);
    } finally {
      this.hideLoading();
    }
  }

  // Global Search functionality
  initGlobalSearch() {
    const searchInput = document.getElementById('globalSearch');
    if (searchInput) {
      let searchTimeout;
      
      searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
          this.performGlobalSearch(e.target.value);
        }, 300);
      });
    }
  }

  async performGlobalSearch(query) {
    if (query.length < 2) return;
    
    try {
      const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
      const results = await response.json();
      
      // Display search results
      this.displaySearchResults(results);
    } catch (error) {
      console.error('Search error:', error);
    }
  }

  displaySearchResults(results) {
    // Implementation for displaying search results
    console.log('Search results:', results);
  }

  // Flash Messages
  initFlashMessages() {
    const closeButtons = document.querySelectorAll('.alert-close');
    closeButtons.forEach(btn => {
      btn.addEventListener('click', () => {
        btn.parentElement.style.display = 'none';
      });
    });

    // Auto-hide after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
      if (!alert.classList.contains('alert-error')) {
        setTimeout(() => {
          alert.style.display = 'none';
        }, 5000);
      }
    });
  }

  // Form Validation
  initFormValidation() {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
      form.addEventListener('submit', (e) => {
        if (!this.validateForm(form)) {
          e.preventDefault();
        }
      });

      // Real-time validation
      const inputs = form.querySelectorAll('input[required], select[required]');
      inputs.forEach(input => {
        input.addEventListener('blur', () => {
          this.validateInput(input);
        });
      });
    });
  }

  validateForm(form) {
    let isValid = true;
    const inputs = form.querySelectorAll('input[required], select[required]');
    
    inputs.forEach(input => {
      if (!this.validateInput(input)) {
        isValid = false;
      }
    });

    return isValid;
  }

  validateInput(input) {
    const value = input.value.trim();
    const isValid = value !== '';
    
    input.classList.toggle('is-invalid', !isValid);
    input.classList.toggle('is-valid', isValid);
    
    return isValid;
  }

  // AJAX Forms
  initAjaxForms() {
    const ajaxForms = document.querySelectorAll('[data-ajax="true"]');
    ajaxForms.forEach(form => {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await this.submitAjaxForm(form);
      });
    });
  }

  async submitAjaxForm(form) {
    const formData = new FormData(form);
    const method = form.method || 'POST';
    const action = form.action;

    try {
      this.showLoading();
      
      const response = await fetch(action, {
        method: method,
        body: formData
      });

      if (response.ok) {
        const result = await response.json();
        this.handleAjaxSuccess(result);
      } else {
        const error = await response.text();
        this.handleAjaxError(error);
      }
    } catch (error) {
      this.handleAjaxError('Network error occurred');
    } finally {
      this.hideLoading();
    }
  }

  handleAjaxSuccess(result) {
    this.showAlert('success', result.message || 'Operation completed successfully');
    this.refreshPageData();
  }

  handleAjaxError(error) {
    this.showAlert('error', error || 'Operation failed');
  }

  // Auto-refresh functionality
  initAutoRefresh() {
    let autoRefreshInterval;
    const autoRefreshCheckbox = document.getElementById('autorefresh');
    
    if (autoRefreshCheckbox) {
      autoRefreshCheckbox.addEventListener('change', (e) => {
        if (e.target.checked) {
          this.startAutoRefresh();
        } else {
          this.stopAutoRefresh();
        }
      });

      // Start auto-refresh if checkbox is checked
      if (autoRefreshCheckbox.checked) {
        this.startAutoRefresh();
      }
    }
  }

  startAutoRefresh() {
    this.autoRefreshInterval = setInterval(() => {
      this.refreshPageData();
    }, 5000); // Refresh every 5 seconds
  }

  stopAutoRefresh() {
    if (this.autoRefreshInterval) {
      clearInterval(this.autoRefreshInterval);
      this.autoRefreshInterval = null;
    }
  }

  // Keyboard shortcuts
  initKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
      // Ctrl/Cmd + K for search
      if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.getElementById('globalSearch');
        if (searchInput) {
          searchInput.focus();
        }
      }

      // Ctrl/Cmd + N for new item
      if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
        e.preventDefault();
        const quickAddBtn = document.getElementById('quickAddBtn');
        if (quickAddBtn) {
          quickAddBtn.click();
        }
      }

      // Escape to close modals
      if (e.key === 'Escape') {
        const openModal = document.querySelector('.modal.show');
        if (openModal) {
          openModal.classList.remove('show');
          document.body.style.overflow = 'auto';
        }
      }
    });
  }

  // Tooltips
  initTooltips() {
    const tooltipElements = document.querySelectorAll('[data-tooltip]');
    tooltipElements.forEach(element => {
      element.addEventListener('mouseenter', (e) => {
        this.showTooltip(e.target, e.target.dataset.tooltip);
      });

      element.addEventListener('mouseleave', () => {
        this.hideTooltip();
      });
    });
  }

  showTooltip(element, text) {
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = text;
    document.body.appendChild(tooltip);

    const rect = element.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 5 + 'px';
  }

  hideTooltip() {
    const tooltip = document.querySelector('.tooltip');
    if (tooltip) {
      tooltip.remove();
    }
  }

  // Charts initialization
  initCharts() {
    // Initialize Chart.js charts if elements exist
    this.initInventoryChart();
    this.initSalesChart();
    this.initTrendChart();
  }

  initInventoryChart() {
    const ctx = document.getElementById('inventoryChart');
    if (ctx) {
      // Chart.js implementation
      new Chart(ctx, {
        type: 'doughnut',
        data: {
          labels: ['In Stock', 'Low Stock', 'Out of Stock'],
          datasets: [{
            data: [0, 0, 0],
            backgroundColor: ['#48BB78', '#ED8936', '#F56565']
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false
        }
      });
    }
  }

  initSalesChart() {
    const ctx = document.getElementById('salesChart');
    if (ctx) {
      new Chart(ctx, {
        type: 'line',
        data: {
          labels: [],
          datasets: [{
            label: 'Sales',
            data: [],
            borderColor: '#667EEA',
            backgroundColor: 'rgba(102, 126, 234, 0.1)',
            tension: 0.4
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: {
              beginAtZero: true
            }
          }
        }
      });
    }
  }

  initTrendChart() {
    const ctx = document.getElementById('trendChart');
    if (ctx) {
      new Chart(ctx, {
        type: 'bar',
        data: {
          labels: [],
          datasets: [{
            label: 'Inventory Movement',
            data: [],
            backgroundColor: '#764BA2'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false
        }
      });
    }
  }

  // Data Tables
  initDataTables() {
    // Add sorting, filtering, and pagination to tables
    const tables = document.querySelectorAll('table[data-table="true"]');
    tables.forEach(table => {
      this.enhanceTable(table);
    });
  }

  enhanceTable(table) {
    // Add sorting functionality
    const headers = table.querySelectorAll('th[data-sortable="true"]');
    headers.forEach(header => {
      header.style.cursor = 'pointer';
      header.addEventListener('click', () => {
        this.sortTable(table, header.cellIndex, header.dataset.sort);
      });
    });

    // Add search functionality
    this.addTableSearch(table);
  }

  sortTable(table, columnIndex, sortType = 'string') {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    rows.sort((a, b) => {
      const aValue = a.cells[columnIndex].textContent.trim();
      const bValue = b.cells[columnIndex].textContent.trim();
      
      if (sortType === 'number') {
        return parseFloat(aValue) - parseFloat(bValue);
      } else {
        return aValue.localeCompare(bValue);
      }
    });

    // Clear tbody and append sorted rows
    tbody.innerHTML = '';
    rows.forEach(row => tbody.appendChild(row));
  }

  addTableSearch(table) {
    const searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.placeholder = 'Search table...';
    searchInput.className = 'form-control mb-3';
    
    table.parentNode.insertBefore(searchInput, table);

    searchInput.addEventListener('input', (e) => {
      this.filterTable(table, e.target.value);
    });
  }

  filterTable(table, searchTerm) {
    const rows = table.querySelectorAll('tbody tr');
    const term = searchTerm.toLowerCase();

    rows.forEach(row => {
      const text = row.textContent.toLowerCase();
      row.style.display = text.includes(term) ? '' : 'none';
    });
  }

  // Real-time updates
  initRealTimeUpdates() {
    // WebSocket or polling for real-time data
    this.setupDataPolling();
  }

  setupDataPolling() {
    // Poll for updates every 30 seconds
    setInterval(() => {
      this.updateRealTimeData();
    }, 30000);
  }

  async updateRealTimeData() {
    try {
      const response = await fetch('/api/realtime-data');
      const data = await response.json();
      
      this.updateDashboardStats(data);
      this.updateNotifications(data);
    } catch (error) {
      console.error('Real-time update error:', error);
    }
  }

  updateDashboardStats(data) {
    // Update dashboard statistics
    const statCards = document.querySelectorAll('.stat-value');
    statCards.forEach(card => {
      const statType = card.dataset.stat;
      if (data[statType]) {
        this.animateNumber(card, parseInt(card.textContent), data[statType]);
      }
    });
  }

  animateNumber(element, start, end) {
    const duration = 1000;
    const startTime = performance.now();
    
    const animate = (currentTime) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      const current = Math.floor(start + (end - start) * progress);
      element.textContent = current.toLocaleString();
      
      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };
    
    requestAnimationFrame(animate);
  }

  updateNotifications(data) {
    const notificationBadge = document.querySelector('.notification-badge');
    if (notificationBadge && data.notifications) {
      notificationBadge.textContent = data.notifications;
      notificationBadge.style.display = data.notifications > 0 ? 'flex' : 'none';
    }
  }

  // Utility methods
  showLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
      overlay.classList.add('show');
    }
  }

  hideLoading() {
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
      overlay.classList.remove('show');
    }
  }

  showLoadingComplete() {
    // Hide initial loading after page is ready
    setTimeout(() => {
      this.hideLoading();
    }, 500);
  }

  showAlert(type, message) {
    const alertContainer = document.createElement('div');
    alertContainer.className = `alert alert-${type}`;
    alertContainer.innerHTML = `
      <i class="fas fa-${type === 'error' ? 'exclamation-circle' : type === 'success' ? 'check-circle' : 'info-circle'}"></i>
      ${message}
      <button class="alert-close">&times;</button>
    `;

    // Insert at top of page content
    const pageContent = document.querySelector('.page-content');
    if (pageContent) {
      pageContent.insertBefore(alertContainer, pageContent.firstChild);
    }

    // Add close functionality
    const closeBtn = alertContainer.querySelector('.alert-close');
    closeBtn.addEventListener('click', () => {
      alertContainer.remove();
    });

    // Auto-remove after 5 seconds
    setTimeout(() => {
      if (alertContainer.parentNode) {
        alertContainer.remove();
      }
    }, 5000);
  }

  refreshPageData() {
    // Refresh current page data based on current route
    const currentPath = window.location.pathname;
    
    if (currentPath === '/') {
      this.refreshDashboard();
    } else if (currentPath === '/products') {
      this.refreshProducts();
    } else if (currentPath === '/inventory') {
      this.refreshInventory();
    } else if (currentPath.startsWith('/store/')) {
      this.refreshStore();
    }
  }

  async refreshDashboard() {
    try {
      const response = await fetch('/api/report/summary');
      const data = await response.json();
      
      // Update dashboard elements
      this.updateDashboardTable(data);
    } catch (error) {
      console.error('Dashboard refresh error:', error);
    }
  }

  updateDashboardTable(data) {
    const reportTable = document.querySelector('#reportTable tbody');
    if (reportTable) {
      reportTable.innerHTML = '';
      data.forEach(item => {
        const row = document.createElement('tr');
        row.innerHTML = `
          <td>${item.sku}</td>
          <td>${item.name}</td>
          <td>${item.total_quantity || 0}</td>
        `;
        reportTable.appendChild(row);
      });
    }
  }

  async refreshProducts() {
    // Refresh products page data
    window.location.reload();
  }

  async refreshInventory() {
    // Refresh inventory page data
    window.location.reload();
  }

  async refreshStore() {
    // Refresh store page data
    const storeId = window.location.pathname.split('/').pop();
    try {
      const response = await fetch(`/api/inventories/${storeId}`);
      const data = await response.json();
      
      // Update store inventory table
      this.updateStoreInventoryTable(data);
    } catch (error) {
      console.error('Store refresh error:', error);
    }
  }

  updateStoreInventoryTable(data) {
    const invTable = document.querySelector('#invTable tbody');
    if (invTable) {
      invTable.innerHTML = '';
      data.forEach(item => {
        const row = document.createElement('tr');
        row.innerHTML = `
          <td>${item.sku}</td>
          <td>${item.name}</td>
          <td>${item.quantity}</td>
          <td><input type="number" min="-100000" max="100000" value="0" data-pid="${item.product_id}" class="delta form-control"></td>
          <td><button class="btn btn-primary btn-sm apply" data-pid="${item.product_id}">Apply</button></td>
        `;
        invTable.appendChild(row);
      });
    }
  }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  window.inventoryApp = new InventoryApp();
});

// Legacy support for existing inline scripts
window.loadSummary = async function() {
  if (window.inventoryApp) {
    await window.inventoryApp.refreshDashboard();
  }
};

// Legacy inventory update function
document.addEventListener('click', async (e) => {
  if (e.target.classList.contains('apply')) {
    const pid = e.target.dataset.pid;
    const input = document.querySelector(`input.delta[data-pid='${pid}']`);
    const change = parseInt(input.value, 10) || 0;
    
    if (change === 0) return;
    
    const storeId = window.STORE_ID || window.location.pathname.split('/').pop();
    
    try {
      window.inventoryApp.showLoading();
      
      const response = await fetch('/api/inventory/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          store_id: storeId,
          product_id: pid,
          change: change,
          note: 'manual adjustment'
        })
      });

      if (response.ok) {
        window.inventoryApp.showAlert('success', 'Inventory updated successfully');
        input.value = '0';
        await window.inventoryApp.refreshStore();
      } else {
        const error = await response.json();
        window.inventoryApp.showAlert('error', error.error || 'Update failed');
      }
    } catch (error) {
      window.inventoryApp.showAlert('error', 'Network error occurred');
      console.error('Inventory update error:', error);
    } finally {
      window.inventoryApp.hideLoading();
    }
  }
});

console.log('✨ Inventory Pro - Advanced inventory management system loaded successfully!');
