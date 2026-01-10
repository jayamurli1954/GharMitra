/**
 * Encryption utility for sensitive data fields
 * Uses AES-256 encryption for encrypting storage locations and verification notes
 * Compatible with backend Fernet encryption
 */

import CryptoJS from 'crypto-js';

// Get encryption key from environment (or secure storage in production)
// In production, this should be stored securely (e.g., React Native Keychain)
const ENCRYPTION_KEY = process.env.ENCRYPTION_KEY || 'dev-key-only-change-in-prod';

/**
 * Encrypt a string using AES-256
 * @param text - The plaintext string to encrypt
 * @returns Encrypted string (base64 encoded)
 */
export const encrypt = (text: string): string => {
  if (!text) return '';
  
  try {
    const encrypted = CryptoJS.AES.encrypt(text, ENCRYPTION_KEY).toString();
    return encrypted;
  } catch (error) {
    console.error('Encryption error:', error);
    throw new Error('Failed to encrypt data');
  }
};

/**
 * Decrypt an AES-256 encrypted string
 * @param encryptedText - The encrypted string to decrypt
 * @returns Decrypted plaintext string
 */
export const decrypt = (encryptedText: string): string => {
  if (!encryptedText) return '';
  
  try {
    const decrypted = CryptoJS.AES.decrypt(encryptedText, ENCRYPTION_KEY);
    return decrypted.toString(CryptoJS.enc.Utf8);
  } catch (error) {
    console.error('Decryption error:', error);
    throw new Error('Failed to decrypt data');
  }
};

/**
 * One-way hash for comparison purposes (e.g., verifying data integrity)
 * @param text - The string to hash
 * @returns SHA-256 hash of the string
 */
export const hash = (text: string): string => {
  return CryptoJS.SHA256(text).toString();
};

