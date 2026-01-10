import React, {useState} from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Linking,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import {authService} from '../../services/authService';
import {legalService} from '../../services/legalService';

const RegisterScreen = ({navigation}: any) => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [apartmentNumber, setApartmentNumber] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [termsAccepted, setTermsAccepted] = useState(false);
  const [privacyAccepted, setPrivacyAccepted] = useState(false);
  const [consentVersion, setConsentVersion] = useState('1.0');

  // Load consent version on mount
  React.useEffect(() => {
    loadConsentVersion();
  }, []);

  const loadConsentVersion = async () => {
    try {
      const versionInfo = await legalService.getLegalVersion();
      setConsentVersion(versionInfo.version);
    } catch (error) {
      console.error('Error loading consent version:', error);
      // Use default version if API fails
    }
  };

  const handleRegister = async () => {
    if (!name || !email || !password || !apartmentNumber) {
      Alert.alert('Error', 'Please fill all required fields');
      return;
    }

    if (password !== confirmPassword) {
      Alert.alert('Error', 'Passwords do not match');
      return;
    }

    if (password.length < 6) {
      Alert.alert('Error', 'Password must be at least 6 characters');
      return;
    }

    // Validate consent (REQUIRED for registration)
    if (!termsAccepted || !privacyAccepted) {
      Alert.alert(
        'Consent Required',
        'You must accept both Terms of Service and Privacy Policy to create an account.',
      );
      return;
    }

    setLoading(true);
    try {
      const registerData = {
        email,
        password,
        name,
        apartment_number: apartmentNumber,
        phone_number: phoneNumber || undefined,
        role: 'member' as const,
        terms_accepted: termsAccepted,
        privacy_accepted: privacyAccepted,
        consent_version: consentVersion,
      };

      await authService.register(registerData);

      Alert.alert(
        'Success',
        'Account created successfully!',
        [{text: 'OK', onPress: () => navigation.navigate('Login')}],
      );
    } catch (error: any) {
      let errorMessage = 'Registration failed. Please try again.';
      if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      } else if (error.message) {
        errorMessage = error.message;
      }
      Alert.alert('Registration Error', errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const openTerms = () => {
    navigation.navigate('TermsOfService');
  };

  const openPrivacy = () => {
    navigation.navigate('PrivacyPolicy');
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.header}>
          <Icon name="person-add" size={60} color="#007AFF" />
          <Text style={styles.title}>Create Account</Text>
          <Text style={styles.subtitle}>Join your apartment community</Text>
        </View>

        <View style={styles.form}>
          <View style={styles.inputContainer}>
            <Icon name="person-outline" size={20} color="#666" style={styles.inputIcon} />
            <TextInput
              style={styles.input}
              placeholder="Full Name *"
              value={name}
              onChangeText={setName}
              autoCapitalize="words"
            />
          </View>

          <View style={styles.inputContainer}>
            <Icon name="mail-outline" size={20} color="#666" style={styles.inputIcon} />
            <TextInput
              style={styles.input}
              placeholder="Email *"
              value={email}
              onChangeText={setEmail}
              keyboardType="email-address"
              autoCapitalize="none"
              autoCorrect={false}
            />
          </View>

          <View style={styles.inputContainer}>
            <Icon name="home-outline" size={20} color="#666" style={styles.inputIcon} />
            <TextInput
              style={styles.input}
              placeholder="Apartment Number *"
              value={apartmentNumber}
              onChangeText={setApartmentNumber}
            />
          </View>

          <View style={styles.inputContainer}>
            <Icon name="call-outline" size={20} color="#666" style={styles.inputIcon} />
            <TextInput
              style={styles.input}
              placeholder="Phone Number (Optional)"
              value={phoneNumber}
              onChangeText={setPhoneNumber}
              keyboardType="phone-pad"
            />
          </View>

          <View style={styles.inputContainer}>
            <Icon name="lock-closed-outline" size={20} color="#666" style={styles.inputIcon} />
            <TextInput
              style={styles.input}
              placeholder="Password *"
              value={password}
              onChangeText={setPassword}
              secureTextEntry={!showPassword}
              autoCapitalize="none"
            />
            <TouchableOpacity
              onPress={() => setShowPassword(!showPassword)}
              style={styles.eyeIcon}>
              <Icon
                name={showPassword ? 'eye-outline' : 'eye-off-outline'}
                size={20}
                color="#666"
              />
            </TouchableOpacity>
          </View>

          <View style={styles.inputContainer}>
            <Icon name="lock-closed-outline" size={20} color="#666" style={styles.inputIcon} />
            <TextInput
              style={styles.input}
              placeholder="Confirm Password *"
              value={confirmPassword}
              onChangeText={setConfirmPassword}
              secureTextEntry={!showPassword}
              autoCapitalize="none"
            />
          </View>

          {/* Legal Consent Section */}
          <View style={styles.consentSection}>
            <Text style={styles.consentTitle}>Legal Consent (Required)</Text>
            
            <TouchableOpacity
              style={styles.checkboxContainer}
              onPress={() => setTermsAccepted(!termsAccepted)}
              activeOpacity={0.7}>
              <View style={[styles.checkbox, termsAccepted && styles.checkboxChecked]}>
                {termsAccepted && <Icon name="checkmark" size={16} color="#FFF" />}
              </View>
              <Text style={styles.checkboxLabel}>
                I accept the{' '}
                <Text style={styles.linkText} onPress={openTerms}>
                  Terms of Service
                </Text>
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.checkboxContainer}
              onPress={() => setPrivacyAccepted(!privacyAccepted)}
              activeOpacity={0.7}>
              <View style={[styles.checkbox, privacyAccepted && styles.checkboxChecked]}>
                {privacyAccepted && <Icon name="checkmark" size={16} color="#FFF" />}
              </View>
              <Text style={styles.checkboxLabel}>
                I accept the{' '}
                <Text style={styles.linkText} onPress={openPrivacy}>
                  Privacy Policy
                </Text>
              </Text>
            </TouchableOpacity>

            <Text style={styles.consentNote}>
              By registering, you agree to our Terms of Service and Privacy Policy as required by
              the Digital Personal Data Protection Act, 2023.
            </Text>
          </View>

          <TouchableOpacity
            style={[styles.button, loading && styles.buttonDisabled]}
            onPress={handleRegister}
            disabled={loading}>
            <Text style={styles.buttonText}>
              {loading ? 'Creating Account...' : 'Register'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.linkButton}
            onPress={() => navigation.navigate('Login')}>
            <Text style={styles.linkText}>
              Already have an account? <Text style={styles.linkTextBold}>Login</Text>
            </Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  scrollContent: {
    flexGrow: 1,
    padding: 20,
    paddingTop: 40,
  },
  header: {
    alignItems: 'center',
    marginBottom: 30,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#007AFF',
    marginTop: 15,
  },
  subtitle: {
    fontSize: 14,
    color: '#666',
    marginTop: 5,
  },
  form: {
    width: '100%',
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#DDD',
    borderRadius: 10,
    marginBottom: 12,
    paddingHorizontal: 15,
    backgroundColor: '#F9F9F9',
  },
  inputIcon: {
    marginRight: 10,
  },
  input: {
    flex: 1,
    height: 50,
    fontSize: 16,
    color: '#333',
  },
  eyeIcon: {
    padding: 5,
  },
  consentSection: {
    marginTop: 10,
    marginBottom: 20,
    padding: 15,
    backgroundColor: '#F5F5F7',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  consentTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1D1D1F',
    marginBottom: 12,
  },
  checkboxContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: 6,
    borderWidth: 2,
    borderColor: '#007AFF',
    marginRight: 10,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#FFF',
  },
  checkboxChecked: {
    backgroundColor: '#007AFF',
    borderColor: '#007AFF',
  },
  checkboxLabel: {
    flex: 1,
    fontSize: 14,
    color: '#1D1D1F',
    lineHeight: 20,
  },
  linkText: {
    color: '#007AFF',
    fontWeight: '600',
    textDecorationLine: 'underline',
  },
  consentNote: {
    fontSize: 12,
    color: '#666',
    marginTop: 8,
    lineHeight: 16,
    fontStyle: 'italic',
  },
  button: {
    backgroundColor: '#007AFF',
    borderRadius: 10,
    height: 50,
    justifyContent: 'center',
    alignItems: 'center',
    marginTop: 10,
  },
  buttonDisabled: {
    backgroundColor: '#A0C4FF',
  },
  buttonText: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: 'bold',
  },
  linkButton: {
    alignItems: 'center',
    marginTop: 20,
  },
  linkTextBold: {
    color: '#007AFF',
    fontWeight: 'bold',
  },
});

export default RegisterScreen;
