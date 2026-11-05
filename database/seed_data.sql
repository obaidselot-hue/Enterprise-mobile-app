-- ============================================================================
-- Enterprise Mobile Application: Initial Seed Data
-- ============================================================================

USE app_database;

-- 1. Initial Administrative & Operator Users
INSERT INTO users (id, phone_number, full_name, email, role, is_active) VALUES
(1, '+14155552671', 'Administrator', 'admin@enterprise.local', 'admin', TRUE),
(2, '+14155558888', 'Alex Morgan (Manager)', 'alex@enterprise.local', 'manager', TRUE),
(3, '+14155559999', 'Sam Taylor (Operator)', 'sam@enterprise.local', 'operator', TRUE)
ON DUPLICATE KEY UPDATE full_name=VALUES(full_name);

-- 2. Master Parties: Customers & Vendors
INSERT INTO parties (id, party_type, name, tax_identifier, phone, email, billing_address, credit_limit, current_balance) VALUES
(1, 'customer', 'Acme Industrial Solutions', 'US-EIN-123456789', '+14155551001', 'accounts@acmeind.com', '100 Market St, San Francisco, CA', 50000.00, 12450.00),
(2, 'customer', 'Apex Logistics Corp', 'US-EIN-987654321', '+14155551002', 'finance@apexlogistics.com', '450 Tech Way, San Jose, CA', 25000.00, 4800.00),
(3, 'customer', 'Cascade Retail Hub', 'US-EIN-555666777', '+14155551003', 'billing@cascaderetail.com', '789 Broadway, Seattle, WA', 15000.00, 0.00),
(4, 'vendor', 'Pacific Tech Components', 'US-EIN-444333222', '+14155552001', 'orders@pacifictech.com', '12 Industrial Parkway, Fremont, CA', 0.00, -8200.00),
(5, 'vendor', 'Global Hardware Supplies', 'US-EIN-111222333', '+14155552002', 'sales@globalhardware.com', '88 Distribution Blvd, Dallas, TX', 0.00, -14500.00)
ON DUPLICATE KEY UPDATE name=VALUES(name);

-- 3. Master Products
INSERT INTO products (id, sku, barcode, name, category, unit_of_measure, selling_price, cost_price, current_stock, reorder_level) VALUES
(1, 'PRD-SN-001', '8901234567890', 'Industrial IoT Sensor Pro', 'Sensors', 'pcs', 145.00, 85.00, 45.000, 10.000),
(2, 'PRD-GW-002', '8901234567891', 'Wireless Edge Gateway X2', 'Networking', 'pcs', 320.00, 195.00, 18.000, 5.000),
(3, 'PRD-CB-003', '8901234567892', 'Shielded Fieldbus Cable 50m', 'Cabling', 'roll', 75.00, 42.00, 120.000, 20.000),
(4, 'PRD-PS-004', '8901234567893', 'DIN-Rail Power Supply 24V', 'Power', 'pcs', 88.00, 52.00, 8.000, 15.000),
(5, 'PRD-RL-005', '8901234567894', '4-Channel Solid State Relay', 'Automation', 'pcs', 62.00, 36.00, 3.000, 10.000)
ON DUPLICATE KEY UPDATE name=VALUES(name);

-- 4. Initial Transactions
INSERT INTO transactions (id, transaction_number, transaction_type, transaction_date, party_id, subtotal, tax_total, grand_total, payment_status, notes, created_by) VALUES
(1, 'INV-2026-0001', 'sales_invoice', '2026-10-15', 1, 4350.00, 391.50, 4741.50, 'paid', 'Quarterly replenishment order', 1),
(2, 'INV-2026-0002', 'sales_invoice', '2026-10-28', 2, 7040.00, 633.60, 7673.60, 'unpaid', 'Project expansion Phase 1', 2),
(3, 'PUR-2026-0001', 'purchase_bill', '2026-10-10', 4, 8200.00, 738.00, 8938.00, 'partially_paid', 'Component restock batch #882', 1)
ON DUPLICATE KEY UPDATE transaction_number=VALUES(transaction_number);

-- 5. Transaction Line Items
INSERT INTO transaction_items (transaction_id, product_id, quantity, unit_price, tax_rate_percent, line_total) VALUES
(1, 1, 30.000, 145.00, 9.00, 4741.50),
(2, 2, 22.000, 320.00, 9.00, 7673.60),
(3, 1, 50.000, 85.00, 9.00, 4632.50),
(3, 4, 45.000, 52.00, 9.00, 2550.60);
