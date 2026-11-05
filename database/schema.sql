-- ============================================================================
-- Enterprise Mobile Application: Production MySQL 8.0 Schema
-- Character set: utf8mb4 for universal unicode & emoji support
-- ============================================================================

CREATE DATABASE IF NOT EXISTS app_database
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE app_database;

-- 1. Users Table: Core identity, roles & profile
CREATE TABLE IF NOT EXISTS users (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL UNIQUE,
    full_name VARCHAR(100) NULL,
    email VARCHAR(150) NULL UNIQUE,
    role ENUM('admin', 'manager', 'operator', 'auditor') NOT NULL DEFAULT 'operator',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_phone (phone_number),
    INDEX idx_users_role (role)
) ENGINE=InnoDB;

-- 2. OTP Verifications Table: Audited lifecycle, attempt tracking & rate limiting
CREATE TABLE IF NOT EXISTS otp_verifications (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    phone_number VARCHAR(20) NOT NULL,
    otp_hash VARCHAR(64) NOT NULL, -- SHA-256 hash of the generated 6-digit OTP
    attempts_count TINYINT UNSIGNED NOT NULL DEFAULT 0,
    max_attempts TINYINT UNSIGNED NOT NULL DEFAULT 3,
    status ENUM('pending', 'verified', 'expired', 'failed') NOT NULL DEFAULT 'pending',
    expires_at DATETIME NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_otp_phone_status (phone_number, status),
    INDEX idx_otp_expires (expires_at)
) ENGINE=InnoDB;

-- 3. Parties Master: Customers & Vendors
CREATE TABLE IF NOT EXISTS parties (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    party_type ENUM('customer', 'vendor') NOT NULL,
    name VARCHAR(150) NOT NULL,
    tax_identifier VARCHAR(50) NULL, -- GSTIN / VAT / EIN
    phone VARCHAR(20) NULL,
    email VARCHAR(150) NULL,
    billing_address TEXT NULL,
    credit_limit DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    current_balance DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_parties_type_name (party_type, name)
) ENGINE=InnoDB;

-- 4. Products Master: Items, Inventory & Pricing
CREATE TABLE IF NOT EXISTS products (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    sku VARCHAR(50) NOT NULL UNIQUE,
    barcode VARCHAR(64) NULL UNIQUE,
    name VARCHAR(150) NOT NULL,
    category VARCHAR(100) NOT NULL DEFAULT 'General',
    unit_of_measure VARCHAR(20) NOT NULL DEFAULT 'pcs',
    selling_price DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    cost_price DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    current_stock DECIMAL(12, 3) NOT NULL DEFAULT 0.000,
    reorder_level DECIMAL(12, 3) NOT NULL DEFAULT 10.000,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_products_sku (sku),
    INDEX idx_products_category (category),
    INDEX idx_products_stock (current_stock, reorder_level)
) ENGINE=InnoDB;

-- 5. Transactions Header Table: Invoices, Bills, Payments
CREATE TABLE IF NOT EXISTS transactions (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    transaction_number VARCHAR(50) NOT NULL UNIQUE, -- E.g., INV-2026-0001
    transaction_type ENUM('sales_invoice', 'purchase_bill', 'payment_in', 'payment_out') NOT NULL,
    transaction_date DATE NOT NULL,
    party_id BIGINT UNSIGNED NOT NULL,
    subtotal DECIMAL(14, 2) NOT NULL DEFAULT 0.00,
    tax_total DECIMAL(14, 2) NOT NULL DEFAULT 0.00,
    grand_total DECIMAL(14, 2) NOT NULL DEFAULT 0.00,
    payment_status ENUM('unpaid', 'partially_paid', 'paid', 'cancelled') NOT NULL DEFAULT 'unpaid',
    notes TEXT NULL,
    created_by BIGINT UNSIGNED NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_tx_party FOREIGN KEY (party_id) REFERENCES parties(id) ON DELETE RESTRICT,
    CONSTRAINT fk_tx_user FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT,
    INDEX idx_tx_date_type (transaction_date, transaction_type),
    INDEX idx_tx_party_status (party_id, payment_status)
) ENGINE=InnoDB;

-- 6. Transaction Items: Line Items with Taxes & Pricing
CREATE TABLE IF NOT EXISTS transaction_items (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    transaction_id BIGINT UNSIGNED NOT NULL,
    product_id BIGINT UNSIGNED NOT NULL,
    quantity DECIMAL(12, 3) NOT NULL,
    unit_price DECIMAL(12, 2) NOT NULL,
    tax_rate_percent DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
    line_total DECIMAL(14, 2) NOT NULL,
    CONSTRAINT fk_items_tx FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE,
    CONSTRAINT fk_items_product FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT,
    INDEX idx_tx_items_product (product_id)
) ENGINE=InnoDB;

-- 7. Audit Logs Table: Operational & Security Traceability
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT UNSIGNED NULL,
    action_type VARCHAR(50) NOT NULL, -- E.g., 'AUTH_LOGIN', 'CREATE_TRANSACTION'
    entity_name VARCHAR(50) NOT NULL,
    entity_id BIGINT UNSIGNED NULL,
    ip_address VARCHAR(45) NULL,
    details JSON NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_audit_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_audit_created (created_at),
    INDEX idx_audit_action (action_type)
) ENGINE=InnoDB;
