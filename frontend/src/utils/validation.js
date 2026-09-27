export function validateEmail(email) {
  const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return re.test(email);
}

export function validatePhone(phone) {
  return /^\d{7,15}$/.test(phone);
}

export function validateUrl(url) {
  if (!url) return true; // optional field
  const re = /^https?:\/\/[^\s]+\.[^\s]+$/;
  return re.test(url);
}

export function validateSellerRegistration(data) {
  const errors = {};

  if (!data.name?.trim()) errors.name = "Name is required.";
  if (!data.email?.trim()) errors.email = "Email is required.";
  else if (!validateEmail(data.email)) errors.email = "Enter a valid email address.";

  if (!data.businessName?.trim()) errors.businessName = "Business name is required.";

  if (!data.password) errors.password = "Password is required.";
  else if (data.password.length < 8) errors.password = "Password must be at least 8 characters.";

  if (!data.confirmPassword) errors.confirmPassword = "Please confirm your password.";
  else if (data.password !== data.confirmPassword) errors.confirmPassword = "Passwords do not match.";

  return errors;
}

export function validateBusinessProfile(data) {
  const errors = {};

  if (!data.businessName?.trim()) errors.businessName = "Business name is required.";
  if (!data.ownerName?.trim()) errors.ownerName = "Owner name is required.";

  if (!data.email?.trim()) errors.email = "Business email is required.";
  else if (!validateEmail(data.email)) errors.email = "Enter a valid email address.";

  if (!data.contactNumber?.trim()) errors.contactNumber = "Phone number is required.";
  else if (!validatePhone(data.contactNumber)) {
    errors.contactNumber = "Phone number must contain only digits (7–15 digits).";
  }

  if (!data.businessCategory?.trim()) errors.businessCategory = "Business category is required.";

  if (data.website && !validateUrl(data.website)) {
    errors.website = "Enter a valid URL (must start with http:// or https://).";
  }

  if (!data.description?.trim()) errors.description = "Business description is required.";

  return errors;
}