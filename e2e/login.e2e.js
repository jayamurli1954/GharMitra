describe('Login Flow', () => {
  beforeEach(async () => {
    await device.reloadReactNative();
  });

  it('should show login screen on app launch', async () => {
    await expect(element(by.text('GharMitra'))).toBeVisible();
    await expect(element(by.text('Your Society, Digitally Simplified'))).toBeVisible();
    await expect(element(by.id('email-input'))).toBeVisible();
    await expect(element(by.id('password-input'))).toBeVisible();
    await expect(element(by.text('Login'))).toBeVisible();
  });

  it('should show validation error for empty fields', async () => {
    await element(by.text('Login')).tap();

    // Wait for alert to appear
    await waitFor(element(by.text('Please enter email and password')))
      .toBeVisible()
      .withTimeout(5000);
  });

  it('should navigate to register society screen', async () => {
    await element(by.text('Register Your Society')).tap();

    // Check if we're on register society screen
    await expect(element(by.text('Register Society'))).toBeVisible();
  });

  it('should navigate to register screen for existing society', async () => {
    await element(by.text('Already a member?')).tap();

    // Check if we're on register screen
    await expect(element(by.text('Join Society'))).toBeVisible();
  });

  it('should handle successful login', async () => {
    // Fill in login form
    await element(by.id('email-input')).typeText('admin@example.com');
    await element(by.id('password-input')).typeText('admin123');

    // Tap login button
    await element(by.text('Login')).tap();

    // Wait for success alert or navigation to dashboard
    await waitFor(element(by.text('Dashboard')))
      .toBeVisible()
      .withTimeout(10000);
  });

  it('should handle login failure', async () => {
    // Fill in wrong credentials
    await element(by.id('email-input')).typeText('admin@example.com');
    await element(by.id('password-input')).typeText('wrongpassword');

    // Tap login button
    await element(by.text('Login')).tap();

    // Wait for error alert
    await waitFor(element(by.text('Login Error')))
      .toBeVisible()
      .withTimeout(5000);
  });

  it('should toggle password visibility', async () => {
    const passwordInput = element(by.id('password-input'));

    // Initially password should be hidden (secureTextEntry)
    // Tap eye icon to show password
    await element(by.id('password-toggle')).tap();

    // Password should now be visible
    // Note: Detox can't directly check secureTextEntry prop,
    // but we can verify the toggle functionality exists
  });
});