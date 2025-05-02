import { test, expect } from '@playwright/test';

test.describe('KharchaNP UI Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Go to the login page
    await page.goto('http://localhost:8080/login');
  });

  test('Login page UI elements', async ({ page }) => {
    // Check for logo and app name
    await expect(page.locator('h1:has-text("KharchaNP")')).toBeVisible();
    
    // Check for login form elements
    await expect(page.getByRole('heading', { name: 'Login' })).toBeVisible();
    await expect(page.getByLabel('Email')).toBeVisible();
    await expect(page.getByLabel('Password')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Sign In' })).toBeVisible();
    
    // Check for social login options
    await expect(page.getByRole('button', { name: 'Google' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Apple' })).toBeVisible();
    
    // Check for sign up link
    await expect(page.getByRole('link', { name: 'Sign up' })).toBeVisible();
  });

  test('Login functionality with valid credentials', async ({ page }) => {
    // Fill in login form with valid credentials
    await page.getByLabel('Email').fill('aashish@gmail.com');
    await page.getByLabel('Password').fill('Sapkota@11');
    
    // Click login button
    await page.getByRole('button', { name: 'Sign In' }).click();
    
    // Wait for navigation to dashboard
    await page.waitForURL('**/home');
    
    // Verify dashboard elements
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Add New Expense' })).toBeVisible();
  });

  test('Dashboard UI elements', async ({ page }) => {
    // Login first
    await page.getByLabel('Email').fill('aashish@gmail.com');
    await page.getByLabel('Password').fill('Sapkota@11');
    await page.getByRole('button', { name: 'Sign In' }).click();
    await page.waitForURL('**/home');
    
    // Check for dashboard elements
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
    
    // Check for summary cards
    await expect(page.getByText('Monthly Total')).toBeVisible();
    await expect(page.getByText('Largest Expense')).toBeVisible();
    await expect(page.getByText('Total Categories')).toBeVisible();
    await expect(page.getByText('Last 30 Days')).toBeVisible();
    
    // Check for expense chart
    await expect(page.getByRole('heading', { name: 'Expense Summary' })).toBeVisible();
    
    // Check for recent expenses section
    await expect(page.getByRole('heading', { name: 'Recent Expenses' })).toBeVisible();
    
    // Check for chatbot
    await expect(page.getByRole('heading', { name: 'Support Assistant' })).toBeVisible();
  });

  test('Sidebar navigation', async ({ page }) => {
    // Login first
    await page.getByLabel('Email').fill('aashish@gmail.com');
    await page.getByLabel('Password').fill('Sapkota@11');
    await page.getByRole('button', { name: 'Sign In' }).click();
    await page.waitForURL('**/home');
    
    // Navigate to Expenses page
    await page.getByRole('link', { name: 'Expenses' }).click();
    await page.waitForURL('**/expenses');
    await expect(page.getByRole('heading', { name: 'Expenses' })).toBeVisible();
    
    // Navigate to Reports page
    await page.getByRole('link', { name: 'Reports' }).click();
    await page.waitForURL('**/reports');
    
    // Navigate to Settings page
    await page.getByRole('link', { name: 'Settings' }).click();
    await page.waitForURL('**/settings');
    
    // Navigate back to Home page
    await page.getByRole('link', { name: 'Overview' }).click();
    await page.waitForURL('**/home');
    await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
  });

  test('Mobile responsiveness', async ({ page }) => {
    // Set viewport to mobile size
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Check login page on mobile
    await expect(page.locator('h1:has-text("KharchaNP")')).toBeVisible();
    await expect(page.getByRole('button', { name: 'Sign In' })).toBeVisible();
    
    // Login
    await page.getByLabel('Email').fill('aashish@gmail.com');
    await page.getByLabel('Password').fill('Sapkota@11');
    await page.getByRole('button', { name: 'Sign In' }).click();
    await page.waitForURL('**/home');
    
    // Check for mobile menu button
    await expect(page.getByRole('button', { name: 'Open menu' })).toBeVisible();
    
    // Open mobile menu
    await page.getByRole('button', { name: 'Open menu' }).click();
    
    // Check that sidebar is visible
    await expect(page.getByRole('link', { name: 'Expenses' })).toBeVisible();
    
    // Close mobile menu
    await page.getByRole('button', { name: 'Close menu' }).click();
    
    // Check that sidebar is hidden
    await expect(page.getByRole('link', { name: 'Expenses' })).not.toBeVisible();
  });
});
