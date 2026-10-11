// Shared validation helpers for Register, Login, and Seller Profile forms.
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
  return validateRequired(value);
}

export function validateUrl(url) {
  if (!url) return null;

  const re = /^https?:\/\/[^\s]+\.[^\s]+$/;

  if (!re.test(url)) {
    return "Enter a valid URL (must start with http:// or https://).";
  }

  return null;
}


/**
 * Validates the full registration form.
 * Returns an object keyed by field name; a field is omitted if valid.
 */
export function validateRegisterForm({
  name,
  email,
  phone,
  password,
  confirmPassword,
  agreedToTerms
}) {
  const errors = {};

  const nameError = validateRequired(name);
  if (nameError) errors.name = nameError;

  const emailError = validateEmail(email);
  if (emailError) errors.email = emailError;

  const phoneError = validatePhone(phone);
  if (phoneError) errors.phone = phoneError;

  const passwordError = validatePassword(password);
  if (passwordError) errors.password = passwordError;

  const confirmError = validateConfirmPassword(
    password,
    confirmPassword
  );
  if (confirmError) errors.confirmPassword = confirmError;

  if (!agreedToTerms) {
    errors.agreedToTerms =
      "You must agree to the Terms & Conditions and Privacy Policy";
  }

  return errors;
}


/**
 * Validates the seller registration form.
 * Kept for compatibility with the existing SellerRegister page.
 */
export function validateSellerRegistration(data) {
  const errors = {};

  if (!data.name?.trim()) {
    errors.name = "Name is required.";
  }

  if (!data.email?.trim()) {
    errors.email = "Email is required.";
  } else if (!validateEmail(data.email)) {
    errors.email = "Enter a valid email address.";
  }

  if (!data.businessName?.trim()) {
    errors.businessName = "Business name is required.";
  }

  if (!data.password) {
    errors.password = "Password is required.";
  } else if (data.password.length < 8) {
    errors.password = "Password must be at least 8 characters.";
  }

  if (!data.confirmPassword) {
    errors.confirmPassword = "Please confirm your password.";
  } else if (data.password !== data.confirmPassword) {
    errors.confirmPassword = "Passwords do not match.";
  }

  return errors;
}


/**
 * Validates the business profile form.
 */
export function validateBusinessProfile(data) {
  const errors = {};

  if (!data.businessName?.trim()) {
    errors.businessName = "Business name is required.";
  }

  if (!data.ownerName?.trim()) {
    errors.ownerName = "Owner name is required.";
  }

  if (!data.email?.trim()) {
    errors.email = "Business email is required.";
  } else if (!validateEmail(data.email)) {
    errors.email = "Enter a valid email address.";
  }

  if (!data.contactNumber?.trim()) {
    errors.contactNumber = "Phone number is required.";
  } else if (!/^\d{7,15}$/.test(data.contactNumber)) {
    errors.contactNumber =
      "Phone number must contain only digits (7–15 digits).";
  }

  if (!data.businessCategory?.trim()) {
    errors.businessCategory = "Business category is required.";
  }

  if (data.website && !validateUrl(data.website)) {
    errors.website =
      "Enter a valid URL (must start with http:// or https://).";
  }

  if (!data.description?.trim()) {
    errors.description = "Business description is required.";
  }

  return errors;
}


/**
 * Validates the full login form.
 */
export function validateLoginForm({ email, password }) {
  const errors = {};

  const emailError = validateEmail(email);
  if (emailError) errors.email = emailError;

  const passwordError = validateRequired(password);
  if (passwordError) errors.password = passwordError;

  return errors;
}