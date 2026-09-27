// Shared validation helpers for Register and Login forms.
// No React/DOM dependency so these stay easily testable in isolation.

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function validateRequired(value) {
  if (!value || value.trim().length === 0) {
    return "This field is required";
  }
  return null;
}

export function validateEmail(value) {
  const requiredError = validateRequired(value);
  if (requiredError) return requiredError;

  if (!EMAIL_REGEX.test(value.trim())) {
    return "Enter a valid email address";
  }
  return null;
}

export function validatePassword(value) {
  const requiredError = validateRequired(value);
  if (requiredError) return requiredError;

  if (value.length < 8) {
    return "Password must be at least 8 characters";
  }
  return null;
}

export function validateConfirmPassword(password, confirmPassword) {
  const requiredError = validateRequired(confirmPassword);
  if (requiredError) return requiredError;

  if (password !== confirmPassword) {
    return "Passwords do not match";
  }
  return null;
}

export function validatePhone(value) {
  // Required, non-empty only — no format/pattern enforced per current requirements.
  return validateRequired(value);
}

/**
 * Validates the full registration form.
 * Returns an object keyed by field name; a field is omitted if valid.
 */
export function validateRegisterForm({ name, email, phone, password, confirmPassword, agreedToTerms }) {
  const errors = {};

  const nameError = validateRequired(name);
  if (nameError) errors.name = nameError;

  const emailError = validateEmail(email);
  if (emailError) errors.email = emailError;

  const phoneError = validatePhone(phone);
  if (phoneError) errors.phone = phoneError;

  const passwordError = validatePassword(password);
  if (passwordError) errors.password = passwordError;

  const confirmError = validateConfirmPassword(password, confirmPassword);
  if (confirmError) errors.confirmPassword = confirmError;

  if (!agreedToTerms) {
    errors.agreedToTerms = "You must agree to the Terms & Conditions and Privacy Policy";
  }

  return errors;
}

/**
 * Validates the full login form.
 * Returns an object keyed by field name; a field is omitted if valid.
 */
export function validateLoginForm({ email, password }) {
  const errors = {};

  const emailError = validateEmail(email);
  if (emailError) errors.email = emailError;

  const passwordError = validateRequired(password);
  if (passwordError) errors.password = passwordError;

  return errors;
}