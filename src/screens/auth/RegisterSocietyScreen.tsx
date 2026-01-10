import React, { useState } from 'react';
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
  ActivityIndicator,
  Image,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import { societyService } from '../../services/societyService';
import { authService } from '../../services/authService';

const RegisterSocietyScreen = ({ navigation, onRegistrationSuccess }: any) => {
  // Admin details
  const [adminName, setAdminName] = useState('');
  const [adminEmail, setAdminEmail] = useState('');
  const [adminPhone, setAdminPhone] = useState('');
  const [adminPassword, setAdminPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // Society details
  const [societyName, setSocietyName] = useState('');
  const [societyAddress, setSocietyAddress] = useState('');
  const [registrationNo, setRegistrationNo] = useState('');
  const [panNo, setPanNo] = useState('');

  // Document URLs (will be uploaded to Cloudinary first)
  const [regCertUrl, setRegCertUrl] = useState('');
  const [panCardUrl, setPanCardUrl] = useState('');

  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const totalSteps = 3;

  const validateStep1 = () => {
    if (!adminName || !adminEmail || !adminPassword) {
      Alert.alert('Error', 'Please fill all required admin details');
      return false;
    }
    if (adminPassword.length < 6) {
      Alert.alert('Error', 'Password must be at least 6 characters');
      return false;
    }
    if (adminPassword !== confirmPassword) {
      Alert.alert('Error', 'Passwords do not match');
      return false;
    }
    return true;
  };

  const validateStep2 = () => {
    if (!societyName) {
      Alert.alert('Error', 'Please enter society name');
      return false;
    }
    return true;
  };

  const handleRegister = async () => {
    if (!validateStep1() || !validateStep2()) {
      return;
    }

    setLoading(true);
    try {
      const registrationData = {
        admin_name: adminName,
        admin_email: adminEmail,
        admin_phone: adminPhone || undefined,
        admin_password: adminPassword,
        society_name: societyName,
        society_address: societyAddress || undefined,
        registration_no: registrationNo || undefined,
        pan_no: panNo || undefined,
        reg_cert_url: regCertUrl || undefined,
        pan_card_url: panCardUrl || undefined,
      };

      const response = await societyService.registerSociety(registrationData);

      // Store token and user data
      await authService.setToken(response.access_token);
      await authService.setUser(response.user);

      Alert.alert(
        'Success',
        `Welcome! Your society "${societyName}" has been registered successfully. You are now the Super Admin.`,
        [
          {
            text: 'OK',
            onPress: () => {
              if (onRegistrationSuccess) {
                onRegistrationSuccess();
              }
            },
          },
        ],
      );
    } catch (error: any) {
      console.error('Registration error:', error);
      let errorMessage = 'Registration failed. Please try again.';

      if (error.response) {
        const status = error.response.status;
        const detail = error.response.data?.detail || error.response.data?.message;

        if (status === 400) {
          errorMessage = detail || 'Invalid registration data';
        } else if (status === 409) {
          errorMessage = detail || 'Society or email already exists';
        } else if (status >= 500) {
          errorMessage = 'Server error. Please try again later.';
        } else {
          errorMessage = detail || errorMessage;
        }
      }

      Alert.alert('Registration Error', errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const renderStep1 = () => (
    <View>
      <Text style={styles.stepTitle}>Admin Details</Text>
      <Text style={styles.stepSubtitle}>Enter your details as the first administrator</Text>

      <View style={styles.inputContainer}>
        <Icon name="person-outline" size={20} color="#666" style={styles.inputIcon} />
        <TextInput
          style={styles.input}
          placeholder="Full Name *"
          value={adminName}
          onChangeText={setAdminName}
          autoCapitalize="words"
        />
      </View>

      <View style={styles.inputContainer}>
        <Icon name="mail-outline" size={20} color="#666" style={styles.inputIcon} />
        <TextInput
          style={styles.input}
          placeholder="Email *"
          value={adminEmail}
          onChangeText={setAdminEmail}
          keyboardType="email-address"
          autoCapitalize="none"
          autoCorrect={false}
        />
      </View>

      <View style={styles.inputContainer}>
        <Icon name="call-outline" size={20} color="#666" style={styles.inputIcon} />
        <TextInput
          style={styles.input}
          placeholder="Phone Number (Optional)"
          value={adminPhone}
          onChangeText={setAdminPhone}
          keyboardType="phone-pad"
        />
      </View>

      <View style={styles.inputContainer}>
        <Icon name="lock-closed-outline" size={20} color="#666" style={styles.inputIcon} />
        <TextInput
          style={styles.input}
          placeholder="Password *"
          value={adminPassword}
          onChangeText={setAdminPassword}
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
    </View>
  );

  const renderStep2 = () => (
    <View>
      <Text style={styles.stepTitle}>Society Details</Text>
      <Text style={styles.stepSubtitle}>Enter your society information</Text>

      <View style={styles.inputContainer}>
        <Icon name="business-outline" size={20} color="#666" style={styles.inputIcon} />
        <TextInput
          style={styles.input}
          placeholder="Society Name *"
          value={societyName}
          onChangeText={setSocietyName}
          autoCapitalize="words"
        />
      </View>

      <View style={styles.inputContainer}>
        <Icon name="location-outline" size={20} color="#666" style={styles.inputIcon} />
        <TextInput
          style={[styles.input, styles.textArea]}
          placeholder="Society Address (Optional)"
          value={societyAddress}
          onChangeText={setSocietyAddress}
          multiline
          numberOfLines={3}
          textAlignVertical="top"
        />
      </View>

      <View style={styles.inputContainer}>
        <Icon name="document-text-outline" size={20} color="#666" style={styles.inputIcon} />
        <TextInput
          style={styles.input}
          placeholder="Registration Number (Optional)"
          value={registrationNo}
          onChangeText={setRegistrationNo}
          autoCapitalize="characters"
        />
      </View>

      <View style={styles.inputContainer}>
        <Icon name="card-outline" size={20} color="#666" style={styles.inputIcon} />
        <TextInput
          style={styles.input}
          placeholder="PAN Number (Optional)"
          value={panNo}
          onChangeText={setPanNo}
          autoCapitalize="characters"
          maxLength={10}
        />
      </View>
    </View>
  );

  const renderStep3 = () => (
    <View>
      <Text style={styles.stepTitle}>Optional Documents</Text>
      <Text style={styles.stepSubtitle}>
        You can upload these documents later from settings
      </Text>

      <View style={styles.infoBox}>
        <Icon name="information-circle" size={24} color="#007AFF" />
        <View style={styles.infoContent}>
          <Text style={styles.infoText}>
            Document upload functionality will be available after registration.
            You can upload Registration Certificate and PAN Card from the settings page.
          </Text>
        </View>
      </View>
    </View>
  );

  const handleNext = () => {
    if (currentStep === 1 && !validateStep1()) {
      return;
    }
    if (currentStep === 2 && !validateStep2()) {
      return;
    }
    if (currentStep < totalSteps) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      style={styles.container}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 0}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
        keyboardShouldPersistTaps="handled">
        <View style={styles.header}>
          <Image
            source={require('../../assets/images/app-icon.png')}
            style={styles.logo}
            resizeMode="contain"
          />
          <Text style={styles.appTitle}>GharMitra</Text>
          <Text style={styles.appSubtitle}>Your Society, Digitally Simplified</Text>
          <Text style={styles.appTagline}>Accounting and Management</Text>
        </View>
        <View style={styles.titleContainer}>
          <Text style={styles.title}>Register Your Society</Text>
        </View>

        {/* Progress Indicator */}
        <View style={styles.progressContainer}>
          {[1, 2, 3].map(step => (
            <View key={step} style={styles.progressStep}>
              <View
                style={[
                  styles.progressCircle,
                  currentStep >= step && styles.progressCircleActive,
                ]}>
                <Text
                  style={[
                    styles.progressText,
                    currentStep >= step && styles.progressTextActive,
                  ]}>
                  {step}
                </Text>
              </View>
              {step < totalSteps && (
                <View
                  style={[
                    styles.progressLine,
                    currentStep > step && styles.progressLineActive,
                  ]}
                />
              )}
            </View>
          ))}
        </View>

        <View style={styles.form}>
          {currentStep === 1 && renderStep1()}
          {currentStep === 2 && renderStep2()}
          {currentStep === 3 && renderStep3()}

          <View style={styles.buttonContainer}>
            {currentStep > 1 && (
              <TouchableOpacity
                style={[styles.button, styles.buttonSecondary]}
                onPress={handleBack}
                disabled={loading}>
                <Text style={styles.buttonSecondaryText}>Back</Text>
              </TouchableOpacity>
            )}

            {currentStep < totalSteps ? (
              <TouchableOpacity
                style={[styles.button, styles.buttonPrimary]}
                onPress={handleNext}
                disabled={loading}>
                <Text style={styles.buttonPrimaryText}>Next</Text>
              </TouchableOpacity>
            ) : (
              <TouchableOpacity
                style={[styles.button, styles.buttonPrimary, loading && styles.buttonDisabled]}
                onPress={handleRegister}
                disabled={loading}>
                {loading ? (
                  <ActivityIndicator color="#FFF" />
                ) : (
                  <Text style={styles.buttonPrimaryText}>Register Society</Text>
                )}
              </TouchableOpacity>
            )}
          </View>

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
    paddingTop: 30,
  },
  header: {
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 20,
    width: '100%',
    alignSelf: 'center',
  },
  logo: {
    width: 120, // Updated to use app icon size
    height: 120, // Updated to use app icon size
    alignSelf: 'center',
    marginBottom: 10,
    borderRadius: 24, // Rounded corners
  },
  appTitle: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#007AFF',
    marginTop: 10,
    textAlign: 'center',
  },
  appSubtitle: {
    fontSize: 18,
    color: '#007AFF',
    textAlign: 'center',
    fontWeight: '700', // Bold
    marginTop: 5,
  },
  appTagline: {
    fontSize: 16,
    color: '#666',
    textAlign: 'center',
    fontWeight: '400', // Normal text
    marginTop: 5,
    marginBottom: 10,
  },
  titleContainer: {
    alignItems: 'center',
    marginBottom: 25,
    marginTop: 8,
  },
  title: {
    fontSize: 26,
    fontWeight: 'bold',
    color: '#007AFF',
  },
  taglineContainer: {
    alignItems: 'center',
    marginBottom: 35,
    marginTop: 8,
    width: 120,
    alignSelf: 'center',
  },
  subtitle: {
    fontSize: 15,
    color: '#1D1D1F',
    textAlign: 'center',
    fontWeight: '700',
    letterSpacing: 0.5,
    lineHeight: 20,
  },
  progressContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 30,
  },
  progressStep: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  progressCircle: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#E5E5EA',
    justifyContent: 'center',
    alignItems: 'center',
  },
  progressCircleActive: {
    backgroundColor: '#007AFF',
  },
  progressText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#999',
  },
  progressTextActive: {
    color: '#FFF',
  },
  progressLine: {
    width: 40,
    height: 2,
    backgroundColor: '#E5E5EA',
    marginHorizontal: 5,
  },
  progressLineActive: {
    backgroundColor: '#007AFF',
  },
  form: {
    width: '100%',
  },
  stepTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#1D1D1F',
    marginBottom: 8,
  },
  stepSubtitle: {
    fontSize: 14,
    color: '#666',
    marginBottom: 20,
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
  textArea: {
    height: 80,
    paddingTop: 15,
  },
  eyeIcon: {
    padding: 5,
  },
  buttonContainer: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 20,
  },
  button: {
    flex: 1,
    borderRadius: 10,
    height: 50,
    justifyContent: 'center',
    alignItems: 'center',
  },
  buttonPrimary: {
    backgroundColor: '#007AFF',
  },
  buttonSecondary: {
    backgroundColor: '#F0F0F0',
    borderWidth: 1,
    borderColor: '#DDD',
  },
  buttonDisabled: {
    backgroundColor: '#A0C4FF',
  },
  buttonPrimaryText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: 'bold',
  },
  buttonSecondaryText: {
    color: '#666',
    fontSize: 16,
    fontWeight: '600',
  },
  linkButton: {
    alignItems: 'center',
    marginTop: 20,
  },
  linkText: {
    color: '#666',
    fontSize: 14,
  },
  linkTextBold: {
    color: '#007AFF',
    fontWeight: 'bold',
  },
  infoBox: {
    flexDirection: 'row',
    backgroundColor: '#E3F2FD',
    padding: 16,
    borderRadius: 12,
    gap: 12,
    marginTop: 12,
  },
  infoContent: {
    flex: 1,
  },
  infoText: {
    fontSize: 14,
    color: '#666',
    lineHeight: 20,
  },
});

export default RegisterSocietyScreen;

