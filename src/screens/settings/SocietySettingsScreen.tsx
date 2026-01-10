import React, {useEffect, useState} from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  Switch,
  Modal,
  Image,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import {settingsService, SocietySettings, SocietySettingsUpdate} from '../../services/settingsService';
import {societyService, SocietyUpdate} from '../../services/societyService';
import {launchImageLibrary, ImagePickerResponse} from 'react-native-image-picker';
import {authService} from '../../services/authService';
import {rolesService, CustomRole, RoleCreate} from '../../services/rolesService';

type SectionKey = 
  | 'society_info'
  | 'financial'
  | 'roles'
  | 'penalty'
  | 'tax'
  | 'payment'
  | 'bank'
  | 'vendor'
  | 'audit'
  | 'billing'
  | 'member';

const SocietySettingsScreen = ({navigation}: any) => {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [settings, setSettings] = useState<SocietySettings | null>(null);
  const [society, setSociety] = useState<any>(null);
  const [expandedSections, setExpandedSections] = useState<Set<SectionKey>>(new Set(['society_info', 'financial', 'roles']));
  const [roles, setRoles] = useState<CustomRole[]>([]);
  const [loadingRoles, setLoadingRoles] = useState(false);
  const [showRoleModal, setShowRoleModal] = useState(false);
  const [editingRole, setEditingRole] = useState<CustomRole | null>(null);
  const [newRoleName, setNewRoleName] = useState('');
  const [newRoleCode, setNewRoleCode] = useState('');
  const [newRoleDescription, setNewRoleDescription] = useState('');
  
  // Society Information
  const [addressLine, setAddressLine] = useState('');
  const [pinCode, setPinCode] = useState('');
  const [city, setCity] = useState('');
  const [state, setState] = useState('');
  const [societyEmail, setSocietyEmail] = useState('');
  const [landline, setLandline] = useState('');
  const [mobile, setMobile] = useState('');
  const [gstRegistrationApplicable, setGstRegistrationApplicable] = useState(false);
  const [statesList, setStatesList] = useState<string[]>([]);
  const [lookingUpPincode, setLookingUpPincode] = useState(false);
  
  // Financial Year & Accounting
  const [financialYearStart, setFinancialYearStart] = useState('');
  const [financialYearEnd, setFinancialYearEnd] = useState('');
  const [accountingType, setAccountingType] = useState<'cash' | 'accrual'>('cash');
  const [logoUrl, setLogoUrl] = useState('');
  
  // Penalty/Interest
  const [penaltyType, setPenaltyType] = useState<'percentage' | 'fixed' | ''>('');
  const [penaltyValue, setPenaltyValue] = useState('');
  const [graceDays, setGraceDays] = useState('');
  const [interestEnabled, setInterestEnabled] = useState(false);
  const [interestRate, setInterestRate] = useState('');
  
  // Tax
  const [gstEnabled, setGstEnabled] = useState(false);
  const [gstNumber, setGstNumber] = useState('');
  const [gstRate, setGstRate] = useState('');
  const [tdsEnabled, setTdsEnabled] = useState(false);
  const [tdsRate, setTdsRate] = useState('');
  const [tdsThreshold, setTdsThreshold] = useState('');
  
  // Payment Gateway
  const [paymentGatewayEnabled, setPaymentGatewayEnabled] = useState(false);
  const [paymentProvider, setPaymentProvider] = useState('');
  const [paymentKeyId, setPaymentKeyId] = useState('');
  const [paymentKeySecret, setPaymentKeySecret] = useState('');
  const [upiEnabled, setUpiEnabled] = useState(false);
  const [upiId, setUpiId] = useState('');
  
  // Bank Accounts
  const [bankAccounts, setBankAccounts] = useState<any[]>([]);
  const [showBankModal, setShowBankModal] = useState(false);
  const [editingBankIndex, setEditingBankIndex] = useState<number | null>(null);
  
  // Vendor
  const [vendorApprovalRequired, setVendorApprovalRequired] = useState(false);
  const [vendorWorkflow, setVendorWorkflow] = useState('');
  
  // Audit Trail
  const [auditTrailEnabled, setAuditTrailEnabled] = useState(true);
  const [auditRetentionDays, setAuditRetentionDays] = useState('');
  
  // Billing
  const [billingCycle, setBillingCycle] = useState('');
  const [autoGenerateBills, setAutoGenerateBills] = useState(false);
  const [billDueDays, setBillDueDays] = useState('');
  
  // Member
  const [billToBillTracking, setBillToBillTracking] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [settingsData, user] = await Promise.all([
        settingsService.getSocietySettings(),
        authService.getStoredUser(),
      ]);
      
      // Load roles
      await loadRoles();
      
      setSettings(settingsData);
      if (user?.society_id) {
        const societyData = await societyService.getSociety(user.society_id.toString());
        setSociety(societyData);
        setFinancialYearStart(societyData.financial_year_start || '');
        setFinancialYearEnd(societyData.financial_year_end || '');
        setAccountingType(societyData.accounting_type || 'cash');
        setLogoUrl(societyData.logo_url || '');
        // Society Information
        setAddressLine(societyData.address_line || '');
        setPinCode(societyData.pin_code || '');
        setCity(societyData.city || '');
        setState(societyData.state || '');
        setSocietyEmail(societyData.email || '');
        setLandline(societyData.landline || '');
        setMobile(societyData.mobile || '');
        setGstRegistrationApplicable(societyData.gst_registration_applicable || false);
      }
      
      // Load states list
      try {
        const statesData = await societyService.getStates();
        setStatesList(statesData.states);
      } catch (error) {
        console.error('Error loading states:', error);
      }
      
      // Load settings into state
      setPenaltyType(settingsData.late_payment_penalty_type || '');
      setPenaltyValue(settingsData.late_payment_penalty_value?.toString() || '');
      setGraceDays(settingsData.late_payment_grace_days?.toString() || '');
      setInterestEnabled(settingsData.interest_on_overdue);
      setInterestRate(settingsData.interest_rate?.toString() || '');
      
      setGstEnabled(settingsData.gst_enabled);
      setGstNumber(settingsData.gst_number || '');
      setGstRate(settingsData.gst_rate?.toString() || '');
      setTdsEnabled(settingsData.tds_enabled);
      setTdsRate(settingsData.tds_rate?.toString() || '');
      setTdsThreshold(settingsData.tds_threshold?.toString() || '');
      
      setPaymentGatewayEnabled(settingsData.payment_gateway_enabled);
      setPaymentProvider(settingsData.payment_gateway_provider || '');
      setPaymentKeyId(settingsData.payment_gateway_key_id || '');
      setUpiEnabled(settingsData.upi_enabled);
      setUpiId(settingsData.upi_id || '');
      
      setBankAccounts(settingsData.bank_accounts || []);
      
      setVendorApprovalRequired(settingsData.vendor_approval_required);
      setVendorWorkflow(settingsData.vendor_approval_workflow || '');
      
      setAuditTrailEnabled(settingsData.audit_trail_enabled);
      setAuditRetentionDays(settingsData.audit_retention_days?.toString() || '');
      
      setBillingCycle(settingsData.billing_cycle || '');
      setAutoGenerateBills(settingsData.auto_generate_bills);
      setBillDueDays(settingsData.bill_due_days?.toString() || '');
      
      setBillToBillTracking(settingsData.bill_to_bill_tracking);
    } catch (error: any) {
      console.error('Error loading settings:', error);
      Alert.alert('Error', 'Failed to load settings. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const loadRoles = async () => {
    setLoadingRoles(true);
    try {
      const rolesList = await rolesService.listRoles();
      setRoles(rolesList);
    } catch (error: any) {
      console.error('Error loading roles:', error);
      // If roles not initialized, that's okay - user can initialize them
      if (error?.response?.status !== 404) {
        Alert.alert('Error', 'Failed to load roles. Please try again.');
      }
    } finally {
      setLoadingRoles(false);
    }
  };

  const handleInitializeRoles = async () => {
    try {
      await rolesService.initializeDefaultRoles();
      Alert.alert('Success', 'Default roles initialized successfully');
      await loadRoles();
    } catch (error: any) {
      console.error('Error initializing roles:', error);
      Alert.alert('Error', error?.response?.data?.detail || 'Failed to initialize roles. Please try again.');
    }
  };

  const handleSaveRole = async () => {
    if (!newRoleName.trim() || !newRoleCode.trim()) {
      Alert.alert('Error', 'Please enter role name and code');
      return;
    }

    try {
      if (editingRole) {
        await rolesService.updateRole(editingRole.id, {
          role_name: newRoleName,
          role_code: newRoleCode,
          description: newRoleDescription,
        });
        Alert.alert('Success', 'Role updated successfully');
      } else {
        await rolesService.createRole({
          role_name: newRoleName,
          role_code: newRoleCode,
          description: newRoleDescription,
        });
        Alert.alert('Success', 'Role created successfully');
      }
      setShowRoleModal(false);
      setEditingRole(null);
      setNewRoleName('');
      setNewRoleCode('');
      setNewRoleDescription('');
      await loadRoles();
    } catch (error: any) {
      console.error('Error saving role:', error);
      Alert.alert('Error', error?.response?.data?.detail || 'Failed to save role. Please try again.');
    }
  };

  const handleDeleteRole = async (role: CustomRole) => {
    if (role.is_system_role) {
      Alert.alert('Error', 'Cannot delete system roles. You can deactivate them instead.');
      return;
    }

    Alert.alert(
      'Confirm Delete',
      `Are you sure you want to delete the role "${role.role_name}"?`,
      [
        {text: 'Cancel', style: 'cancel'},
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await rolesService.deleteRole(role.id);
              Alert.alert('Success', 'Role deleted successfully');
              await loadRoles();
            } catch (error: any) {
              console.error('Error deleting role:', error);
              Alert.alert('Error', error?.response?.data?.detail || 'Failed to delete role. Please try again.');
            }
          },
        },
      ]
    );
  };

  const toggleSection = (section: SectionKey) => {
    const newExpanded = new Set(expandedSections);
    if (newExpanded.has(section)) {
      newExpanded.delete(section);
    } else {
      newExpanded.add(section);
    }
    setExpandedSections(newExpanded);
  };

  const handlePincodeChange = async (pincode: string) => {
    setPinCode(pincode);
    if (pincode.length === 6 && /^\d{6}$/.test(pincode)) {
      setLookingUpPincode(true);
      try {
        const lookup = await societyService.lookupPincode(pincode);
        if (lookup.found) {
          setCity(lookup.city || '');
          setState(lookup.state || '');
        } else {
          // Keep existing values or clear if not found
          if (!lookup.city) setCity('');
          if (!lookup.state) setState('');
        }
      } catch (error) {
        console.error('Error looking up pincode:', error);
      } finally {
        setLookingUpPincode(false);
      }
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      // Save society settings (financial year, accounting type, address, contact)
      if (society) {
        const societyUpdate: SocietyUpdate = {
          financial_year_start: financialYearStart || undefined,
          financial_year_end: financialYearEnd || undefined,
          accounting_type: accountingType,
          logo_url: logoUrl || undefined,
          address_line: addressLine || undefined,
          pin_code: pinCode || undefined,
          city: city || undefined,
          state: state || undefined,
          email: societyEmail || undefined,
          landline: landline || undefined,
          mobile: mobile || undefined,
          gst_registration_applicable: gstRegistrationApplicable,
        };
        await societyService.updateSocietySettings(societyUpdate);
      }
      
      // Save other settings
      const settingsUpdate: SocietySettingsUpdate = {
        late_payment_penalty_type: penaltyType || undefined,
        late_payment_penalty_value: penaltyValue ? parseFloat(penaltyValue) : undefined,
        late_payment_grace_days: graceDays ? parseInt(graceDays) : undefined,
        interest_on_overdue: interestEnabled,
        interest_rate: interestRate ? parseFloat(interestRate) : undefined,
        
        gst_enabled: gstEnabled,
        gst_number: gstNumber || undefined,
        gst_rate: gstRate ? parseFloat(gstRate) : undefined,
        tds_enabled: tdsEnabled,
        tds_rate: tdsRate ? parseFloat(tdsRate) : undefined,
        tds_threshold: tdsThreshold ? parseFloat(tdsThreshold) : undefined,
        
        payment_gateway_enabled: paymentGatewayEnabled,
        payment_gateway_provider: paymentProvider || undefined,
        payment_gateway_key_id: paymentKeyId || undefined,
        payment_gateway_key_secret: paymentKeySecret || undefined,
        upi_enabled: upiEnabled,
        upi_id: upiId || undefined,
        
        bank_accounts: bankAccounts.length > 0 ? bankAccounts : undefined,
        
        vendor_approval_required: vendorApprovalRequired,
        vendor_approval_workflow: vendorWorkflow || undefined,
        
        audit_trail_enabled: auditTrailEnabled,
        audit_retention_days: auditRetentionDays ? parseInt(auditRetentionDays) : undefined,
        
        billing_cycle: billingCycle || undefined,
        auto_generate_bills: autoGenerateBills,
        bill_due_days: billDueDays ? parseInt(billDueDays) : undefined,
        
        bill_to_bill_tracking: billToBillTracking,
      };
      
      await settingsService.updateSocietySettings(settingsUpdate);
      Alert.alert('Success', 'Settings saved successfully');
      await loadData();
    } catch (error: any) {
      console.error('Error saving settings:', error);
      Alert.alert('Error', error?.response?.data?.detail || 'Failed to save settings. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const renderSection = (
    key: SectionKey,
    title: string,
    icon: string,
    children: React.ReactNode
  ) => {
    const isExpanded = expandedSections.has(key);
    return (
      <View style={styles.section}>
        <TouchableOpacity
          style={styles.sectionHeader}
          onPress={() => toggleSection(key)}
          activeOpacity={0.7}>
          <View style={styles.sectionHeaderLeft}>
            <Icon name={icon} size={24} color="#007AFF" />
            <Text style={styles.sectionTitle}>{title}</Text>
          </View>
          <Icon
            name={isExpanded ? 'chevron-up' : 'chevron-down'}
            size={24}
            color="#666"
          />
        </TouchableOpacity>
        {isExpanded && (
          <View style={styles.sectionContent}>
            {children}
          </View>
        )}
      </View>
    );
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
        <Text style={styles.loadingText}>Loading settings...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Society Information */}
        {renderSection(
          'society_info',
          'Society Information',
          'business-outline',
          <>
            <View style={styles.infoBox}>
              <Icon name="information-circle" size={20} color="#007AFF" />
              <Text style={styles.infoText}>
                Enter your society's complete address and contact information. This will be used in reports, bills, and official communications.
              </Text>
            </View>
            
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Address Line</Text>
              <TextInput
                style={styles.input}
                placeholder="Building name, street address"
                value={addressLine}
                onChangeText={setAddressLine}
                placeholderTextColor="#999"
              />
            </View>
            
            <View style={styles.inputGroup}>
              <Text style={styles.label}>PIN Code</Text>
              <View style={{flexDirection: 'row', alignItems: 'center', gap: 8}}>
                <TextInput
                  style={[styles.input, {flex: 1}]}
                  placeholder="6-digit PIN code"
                  value={pinCode}
                  onChangeText={handlePincodeChange}
                  keyboardType="number-pad"
                  maxLength={6}
                  placeholderTextColor="#999"
                />
                {lookingUpPincode && (
                  <ActivityIndicator size="small" color="#007AFF" />
                )}
              </View>
              <Text style={styles.hint}>City and state will be auto-filled when you enter a valid PIN code</Text>
            </View>
            
            <View style={styles.inputGroup}>
              <Text style={styles.label}>City</Text>
              <TextInput
                style={styles.input}
                placeholder="City name"
                value={city}
                onChangeText={setCity}
                placeholderTextColor="#999"
                editable={!lookingUpPincode}
              />
            </View>
            
            <View style={styles.inputGroup}>
              <Text style={styles.label}>State</Text>
              {statesList.length > 0 ? (
                <ScrollView style={{maxHeight: 200, borderWidth: 1, borderColor: '#E5E5EA', borderRadius: 12, backgroundColor: '#FAFAFA'}}>
                  {statesList.map((stateName) => (
                    <TouchableOpacity
                      key={stateName}
                      style={{
                        padding: 14,
                        borderBottomWidth: 1,
                        borderBottomColor: '#E5E5EA',
                        backgroundColor: state === stateName ? '#E3F2FD' : 'transparent',
                      }}
                      onPress={() => setState(stateName)}>
                      <Text style={{fontSize: 16, color: state === stateName ? '#007AFF' : '#1D1D1F'}}>
                        {stateName}
                      </Text>
                    </TouchableOpacity>
                  ))}
                </ScrollView>
              ) : (
                <TextInput
                  style={styles.input}
                  placeholder="State name"
                  value={state}
                  onChangeText={setState}
                  placeholderTextColor="#999"
                  editable={!lookingUpPincode}
                />
              )}
            </View>
            
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Email Address</Text>
              <TextInput
                style={styles.input}
                placeholder="society@example.com"
                value={societyEmail}
                onChangeText={setSocietyEmail}
                keyboardType="email-address"
                autoCapitalize="none"
                autoCorrect={false}
                placeholderTextColor="#999"
              />
            </View>
            
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Landline Number</Text>
              <TextInput
                style={styles.input}
                placeholder="e.g., 022-12345678"
                value={landline}
                onChangeText={setLandline}
                keyboardType="phone-pad"
                placeholderTextColor="#999"
              />
            </View>
            
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Mobile Number</Text>
              <TextInput
                style={styles.input}
                placeholder="e.g., 9876543210"
                value={mobile}
                onChangeText={setMobile}
                keyboardType="phone-pad"
                maxLength={10}
                placeholderTextColor="#999"
              />
            </View>
            
            <View style={styles.switchGroup}>
              <View style={styles.switchRow}>
                <View style={styles.switchLabelContainer}>
                  <Text style={styles.switchLabel}>GST Registration Applicable</Text>
                  <Text style={styles.switchHint}>Check if your society is registered under GST</Text>
                </View>
                <Switch
                  value={gstRegistrationApplicable}
                  onValueChange={setGstRegistrationApplicable}
                  trackColor={{false: '#D1D1D6', true: '#34C759'}}
                  thumbColor="#FFF"
                />
              </View>
            </View>
            
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Society Logo</Text>
              <Text style={styles.hint}>
                Upload your society logo to a hosting service (e.g., Imgur, Cloudinary) and paste the URL here.
                The logo will appear on reports and bills for branding purposes.
              </Text>
              <TextInput
                style={styles.input}
                placeholder="https://example.com/logo.png"
                value={logoUrl}
                onChangeText={setLogoUrl}
                keyboardType="url"
                autoCapitalize="none"
                autoCorrect={false}
              />
              {logoUrl ? (
                <View style={styles.logoPreview}>
                  <Text style={styles.previewLabel}>Preview:</Text>
                  <Image
                    source={{uri: logoUrl}}
                    style={styles.logoPreviewImage}
                    resizeMode="contain"
                  />
                </View>
              ) : null}
            </View>
          </>
        )}

        {/* Financial Year & Accounting Method */}
        {renderSection(
          'financial',
          'Financial Year & Accounting Method',
          'calendar-outline',
          <>
            <View style={styles.infoBox}>
              <Icon name="information-circle" size={20} color="#007AFF" />
              <Text style={styles.infoText}>
                Set your financial year dates and choose between Cash or Accrual accounting method.
                Accrual accounting provides a more accurate financial picture and is recommended for audits.
              </Text>
            </View>
            
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Financial Year Start Date</Text>
              <TextInput
                style={styles.input}
                placeholder="YYYY-MM-DD (e.g., 2024-04-01)"
                value={financialYearStart}
                onChangeText={setFinancialYearStart}
                placeholderTextColor="#999"
              />
              <Text style={styles.hint}>Typically April 1st for Indian societies</Text>
            </View>
            
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Financial Year End Date</Text>
              <TextInput
                style={styles.input}
                placeholder="YYYY-MM-DD (e.g., 2025-03-31)"
                value={financialYearEnd}
                onChangeText={setFinancialYearEnd}
                placeholderTextColor="#999"
              />
              <Text style={styles.hint}>Typically March 31st for Indian societies</Text>
            </View>
            
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Accounting Method *</Text>
              <View style={styles.optionContainer}>
                <TouchableOpacity
                  style={[
                    styles.optionCard,
                    accountingType === 'cash' && styles.optionCardActive,
                  ]}
                  onPress={() => setAccountingType('cash')}
                  activeOpacity={0.7}>
                  <Icon
                    name={accountingType === 'cash' ? 'radio-button-on' : 'radio-button-off'}
                    size={24}
                    color={accountingType === 'cash' ? '#007AFF' : '#999'}
                  />
                  <View style={styles.optionContent}>
                    <Text
                      style={[
                        styles.optionTitle,
                        accountingType === 'cash' && styles.optionTitleActive,
                      ]}>
                      Cash Accounting
                    </Text>
                    <Text style={styles.optionDescription}>
                      Records transactions when cash is exchanged. Simpler but less accurate.
                    </Text>
                  </View>
                </TouchableOpacity>
                
                <TouchableOpacity
                  style={[
                    styles.optionCard,
                    accountingType === 'accrual' && styles.optionCardActive,
                  ]}
                  onPress={() => setAccountingType('accrual')}
                  activeOpacity={0.7}>
                  <Icon
                    name={accountingType === 'accrual' ? 'radio-button-on' : 'radio-button-off'}
                    size={24}
                    color={accountingType === 'accrual' ? '#007AFF' : '#999'}
                  />
                  <View style={styles.optionContent}>
                    <Text
                      style={[
                        styles.optionTitle,
                        accountingType === 'accrual' && styles.optionTitleActive,
                      ]}>
                      Accrual Accounting
                    </Text>
                    <Text style={styles.optionDescription}>
                      Records transactions when earned/incurred. More accurate, recommended for audits.
                    </Text>
                  </View>
                </TouchableOpacity>
              </View>
            </View>
            
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Society Logo URL (Optional)</Text>
              <Text style={styles.hint}>
                Upload your society logo to a hosting service (e.g., Imgur, Cloudinary) and paste the URL here.
                The logo will appear on reports and bills for branding purposes.
              </Text>
              <TextInput
                style={styles.input}
                placeholder="https://example.com/logo.png"
                value={logoUrl}
                onChangeText={setLogoUrl}
                keyboardType="url"
                autoCapitalize="none"
                autoCorrect={false}
              />
              {logoUrl ? (
                <View style={styles.logoPreview}>
                  <Text style={styles.previewLabel}>Preview:</Text>
                  <Image
                    source={{uri: logoUrl}}
                    style={styles.logoPreviewImage}
                    resizeMode="contain"
                  />
                </View>
              ) : null}
            </View>
          </>
        )}

        {/* Role Management */}
        {renderSection(
          'roles',
          'Role Management',
          'people-outline',
          <>
            <View style={styles.infoBox}>
              <Icon name="information-circle" size={20} color="#007AFF" />
              <Text style={styles.infoText}>
                Configure roles for your society. Default roles include Chairman/President, Secretary, Treasurer, and Auditor.
                You can customize role names and add custom roles. Role assignment is done by admin during initial setup.
              </Text>
            </View>

            <View style={styles.warningBox}>
              <Icon name="warning" size={20} color="#FF9800" />
              <View style={styles.warningContent}>
                <Text style={styles.warningTitle}>⚠️ IMPORTANT: Auditor Role Assignment</Text>
                <Text style={styles.warningText}>
                  Only assign the <Text style={styles.warningBold}>Auditor role to external auditor user IDs</Text>.
                  Auditors can only <Text style={styles.warningBold}>view transactions and generate reports</Text>.
                  They <Text style={styles.warningBold}>CANNOT add, edit, or delete</Text> any records or transactions.
                  Be very careful when assigning this role - verify the user ID before assignment.
                </Text>
              </View>
            </View>

            {roles.length === 0 ? (
              <View style={styles.emptyStateBox}>
                <Icon name="people-outline" size={48} color="#C7C7CC" />
                <Text style={styles.emptyStateText}>No roles configured</Text>
                <Text style={styles.emptyStateSubtext}>
                  Initialize default roles to get started
                </Text>
                <TouchableOpacity
                  style={styles.initButton}
                  onPress={handleInitializeRoles}
                  disabled={loadingRoles}>
                  {loadingRoles ? (
                    <ActivityIndicator size="small" color="#FFF" />
                  ) : (
                    <>
                      <Icon name="add-circle" size={20} color="#FFF" />
                      <Text style={styles.initButtonText}>Initialize Default Roles</Text>
                    </>
                  )}
                </TouchableOpacity>
              </View>
            ) : (
              <>
                {roles.map((role) => (
                  <View key={role.id} style={styles.roleCard}>
                    <View style={styles.roleHeader}>
                      <View style={styles.roleHeaderLeft}>
                        <View style={styles.roleBadge}>
                          <Text style={styles.roleBadgeText}>
                            {role.is_system_role ? 'System' : 'Custom'}
                          </Text>
                        </View>
                        <View style={styles.roleInfo}>
                          <Text style={styles.roleName}>{role.role_name}</Text>
                          <Text style={styles.roleCode}>Code: {role.role_code}</Text>
                          {role.description && (
                            <Text style={styles.roleDescription}>{role.description}</Text>
                          )}
                          <Text style={styles.roleUserCount}>
                            Assigned to {role.user_count || 0} user(s)
                          </Text>
                        </View>
                      </View>
                      <View style={styles.roleActions}>
                        <TouchableOpacity
                          onPress={() => {
                            setEditingRole(role);
                            setNewRoleName(role.role_name);
                            setNewRoleCode(role.role_code);
                            setNewRoleDescription(role.description || '');
                            setShowRoleModal(true);
                          }}
                          style={styles.roleActionButton}>
                          <Icon name="create-outline" size={18} color="#007AFF" />
                        </TouchableOpacity>
                        {!role.is_system_role && (
                          <TouchableOpacity
                            onPress={() => handleDeleteRole(role)}
                            style={styles.roleActionButton}>
                            <Icon name="trash-outline" size={18} color="#F44336" />
                          </TouchableOpacity>
                        )}
                      </View>
                    </View>
                    <View style={styles.roleStatusRow}>
                      <View style={styles.switchRow}>
                        <Text style={styles.switchLabel}>Active</Text>
                        <Switch
                          value={role.is_active}
                          onValueChange={async () => {
                            try {
                              await rolesService.toggleRoleStatus(role.id);
                              await loadRoles();
                            } catch (error: any) {
                              Alert.alert('Error', 'Failed to toggle role status');
                            }
                          }}
                          trackColor={{false: '#D1D1D6', true: '#34C759'}}
                          thumbColor="#FFF"
                        />
                      </View>
                    </View>
                  </View>
                ))}

                <TouchableOpacity
                  style={styles.addButton}
                  onPress={() => {
                    setEditingRole(null);
                    setNewRoleName('');
                    setNewRoleCode('');
                    setNewRoleDescription('');
                    setShowRoleModal(true);
                  }}
                  activeOpacity={0.7}>
                  <Icon name="add-circle-outline" size={20} color="#007AFF" />
                  <Text style={styles.addButtonText}>Add Custom Role</Text>
                </TouchableOpacity>
              </>
            )}
          </>
        )}

        {/* Penalty/Interest Rules */}
        {renderSection(
          'penalty',
          'Penalty & Interest Rules',
          'alert-circle-outline',
          <>
            <View style={styles.infoBox}>
              <Icon name="information-circle" size={20} color="#007AFF" />
              <Text style={styles.infoText}>
                Configure late payment penalties and interest on overdue amounts as per your society bye-laws.
              </Text>
            </View>
            
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Penalty Type</Text>
              <View style={styles.radioGroup}>
                <TouchableOpacity
                  style={styles.radioOption}
                  onPress={() => setPenaltyType('percentage')}
                  activeOpacity={0.7}>
                  <Icon
                    name={penaltyType === 'percentage' ? 'radio-button-on' : 'radio-button-off'}
                    size={20}
                    color={penaltyType === 'percentage' ? '#007AFF' : '#999'}
                  />
                  <Text style={styles.radioLabel}>Percentage</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.radioOption}
                  onPress={() => setPenaltyType('fixed')}
                  activeOpacity={0.7}>
                  <Icon
                    name={penaltyType === 'fixed' ? 'radio-button-on' : 'radio-button-off'}
                    size={20}
                    color={penaltyType === 'fixed' ? '#007AFF' : '#999'}
                  />
                  <Text style={styles.radioLabel}>Fixed Amount</Text>
                </TouchableOpacity>
              </View>
            </View>
            
            {penaltyType && (
              <>
                <View style={styles.inputGroup}>
                  <Text style={styles.label}>
                    Penalty Value ({penaltyType === 'percentage' ? '%' : '₹'})
                  </Text>
                  <TextInput
                    style={styles.input}
                    placeholder={penaltyType === 'percentage' ? 'e.g., 2.5' : 'e.g., 100'}
                    value={penaltyValue}
                    onChangeText={setPenaltyValue}
                    keyboardType="decimal-pad"
                    placeholderTextColor="#999"
                  />
                </View>
                
                <View style={styles.inputGroup}>
                  <Text style={styles.label}>Grace Period (Days)</Text>
                  <TextInput
                    style={styles.input}
                    placeholder="e.g., 7"
                    value={graceDays}
                    onChangeText={setGraceDays}
                    keyboardType="number-pad"
                    placeholderTextColor="#999"
                  />
                  <Text style={styles.hint}>Days before penalty applies</Text>
                </View>
              </>
            )}
            
            <View style={styles.switchGroup}>
              <View style={styles.switchRow}>
                <View style={styles.switchLabelContainer}>
                  <Text style={styles.switchLabel}>Interest on Overdue</Text>
                  <Text style={styles.switchHint}>Charge interest on overdue amounts</Text>
                </View>
                <Switch
                  value={interestEnabled}
                  onValueChange={setInterestEnabled}
                  trackColor={{false: '#D1D1D6', true: '#34C759'}}
                  thumbColor="#FFF"
                />
              </View>
            </View>
            
            {interestEnabled && (
              <View style={styles.inputGroup}>
                <Text style={styles.label}>Annual Interest Rate (%)</Text>
                <TextInput
                  style={styles.input}
                  placeholder="e.g., 12"
                  value={interestRate}
                  onChangeText={setInterestRate}
                  keyboardType="decimal-pad"
                  placeholderTextColor="#999"
                />
              </View>
            )}
          </>
        )}

        {/* Tax Configuration */}
        {renderSection(
          'tax',
          'Tax Configuration (GST & TDS)',
          'receipt-outline',
          <>
            <View style={styles.infoBox}>
              <Icon name="information-circle" size={20} color="#007AFF" />
              <Text style={styles.infoText}>
                Configure GST and TDS settings for compliance and reporting.
              </Text>
            </View>
            
            <View style={styles.switchGroup}>
              <View style={styles.switchRow}>
                <View style={styles.switchLabelContainer}>
                  <Text style={styles.switchLabel}>Enable GST</Text>
                  <Text style={styles.switchHint}>Enable GST for transactions</Text>
                </View>
                <Switch
                  value={gstEnabled}
                  onValueChange={setGstEnabled}
                  trackColor={{false: '#D1D1D6', true: '#34C759'}}
                  thumbColor="#FFF"
                />
              </View>
            </View>
            
            {gstEnabled && (
              <>
                <View style={styles.inputGroup}>
                  <Text style={styles.label}>GST Number (GSTIN)</Text>
                  <TextInput
                    style={styles.input}
                    placeholder="e.g., 27AAAAA0000A1Z5"
                    value={gstNumber}
                    onChangeText={setGstNumber}
                    placeholderTextColor="#999"
                    maxLength={15}
                  />
                </View>
                
                <View style={styles.inputGroup}>
                  <Text style={styles.label}>Default GST Rate (%)</Text>
                  <TextInput
                    style={styles.input}
                    placeholder="e.g., 18"
                    value={gstRate}
                    onChangeText={setGstRate}
                    keyboardType="decimal-pad"
                    placeholderTextColor="#999"
                  />
                </View>
              </>
            )}
            
            <View style={styles.switchGroup}>
              <View style={styles.switchRow}>
                <View style={styles.switchLabelContainer}>
                  <Text style={styles.switchLabel}>Enable TDS</Text>
                  <Text style={styles.switchHint}>Enable TDS on vendor payments</Text>
                </View>
                <Switch
                  value={tdsEnabled}
                  onValueChange={setTdsEnabled}
                  trackColor={{false: '#D1D1D6', true: '#34C759'}}
                  thumbColor="#FFF"
                />
              </View>
            </View>
            
            {tdsEnabled && (
              <>
                <View style={styles.inputGroup}>
                  <Text style={styles.label}>TDS Rate (%)</Text>
                  <TextInput
                    style={styles.input}
                    placeholder="e.g., 10"
                    value={tdsRate}
                    onChangeText={setTdsRate}
                    keyboardType="decimal-pad"
                    placeholderTextColor="#999"
                  />
                </View>
                
                <View style={styles.inputGroup}>
                  <Text style={styles.label}>TDS Threshold (₹)</Text>
                  <TextInput
                    style={styles.input}
                    placeholder="e.g., 30000"
                    value={tdsThreshold}
                    onChangeText={setTdsThreshold}
                    keyboardType="number-pad"
                    placeholderTextColor="#999"
                  />
                  <Text style={styles.hint}>Amount threshold for TDS deduction</Text>
                </View>
              </>
            )}
          </>
        )}

        {/* Payment Gateway */}
        {renderSection(
          'payment',
          'Payment Gateway & UPI',
          'card-outline',
          <>
            <View style={styles.infoBox}>
              <Icon name="information-circle" size={20} color="#007AFF" />
              <Text style={styles.infoText}>
                Configure payment gateways and UPI for digital collections. All fields are optional.
              </Text>
            </View>
            
            <View style={styles.switchGroup}>
              <View style={styles.switchRow}>
                <View style={styles.switchLabelContainer}>
                  <Text style={styles.switchLabel}>Enable Payment Gateway</Text>
                  <Text style={styles.switchHint}>Enable online payment collection</Text>
                </View>
                <Switch
                  value={paymentGatewayEnabled}
                  onValueChange={setPaymentGatewayEnabled}
                  trackColor={{false: '#D1D1D6', true: '#34C759'}}
                  thumbColor="#FFF"
                />
              </View>
            </View>
            
            {paymentGatewayEnabled && (
              <>
                <View style={styles.inputGroup}>
                  <Text style={styles.label}>Payment Provider</Text>
                  <TextInput
                    style={styles.input}
                    placeholder="e.g., razorpay, payu, stripe"
                    value={paymentProvider}
                    onChangeText={setPaymentProvider}
                    placeholderTextColor="#999"
                  />
                </View>
                
                <View style={styles.inputGroup}>
                  <Text style={styles.label}>Key ID</Text>
                  <TextInput
                    style={styles.input}
                    placeholder="Payment gateway key ID"
                    value={paymentKeyId}
                    onChangeText={setPaymentKeyId}
                    placeholderTextColor="#999"
                    secureTextEntry
                  />
                </View>
                
                <View style={styles.inputGroup}>
                  <Text style={styles.label}>Key Secret</Text>
                  <TextInput
                    style={styles.input}
                    placeholder="Payment gateway key secret"
                    value={paymentKeySecret}
                    onChangeText={setPaymentKeySecret}
                    placeholderTextColor="#999"
                    secureTextEntry
                  />
                </View>
              </>
            )}
            
            <View style={styles.switchGroup}>
              <View style={styles.switchRow}>
                <View style={styles.switchLabelContainer}>
                  <Text style={styles.switchLabel}>Enable UPI</Text>
                  <Text style={styles.switchHint}>Enable UPI payment collection</Text>
                </View>
                <Switch
                  value={upiEnabled}
                  onValueChange={setUpiEnabled}
                  trackColor={{false: '#D1D1D6', true: '#34C759'}}
                  thumbColor="#FFF"
                />
              </View>
            </View>
            
            {upiEnabled && (
              <View style={styles.inputGroup}>
                <Text style={styles.label}>UPI ID</Text>
                <TextInput
                  style={styles.input}
                  placeholder="e.g., society@paytm"
                  value={upiId}
                  onChangeText={setUpiId}
                  placeholderTextColor="#999"
                />
              </View>
            )}
          </>
        )}

        {/* Bank Accounts */}
        {renderSection(
          'bank',
          'Bank Accounts',
          'wallet-outline',
          <>
            <View style={styles.infoBox}>
              <Icon name="information-circle" size={20} color="#007AFF" />
              <Text style={styles.infoText}>
                Add bank accounts for reconciliation and transaction tracking. All fields are optional.
              </Text>
            </View>
            
            {bankAccounts.map((account, index) => (
              <View key={index} style={styles.bankAccountCard}>
                <View style={styles.bankAccountHeader}>
                  <Text style={styles.bankAccountName}>{account.account_name}</Text>
                  <View style={styles.bankAccountActions}>
                    <TouchableOpacity
                      onPress={() => {
                        setEditingBankIndex(index);
                        setShowBankModal(true);
                      }}
                      style={styles.editButton}>
                      <Icon name="create-outline" size={18} color="#007AFF" />
                    </TouchableOpacity>
                    <TouchableOpacity
                      onPress={() => {
                        const newAccounts = bankAccounts.filter((_, i) => i !== index);
                        setBankAccounts(newAccounts);
                      }}
                      style={styles.deleteButton}>
                      <Icon name="trash-outline" size={18} color="#F44336" />
                    </TouchableOpacity>
                  </View>
                </View>
                <Text style={styles.bankAccountDetails}>
                  {account.bank_name} • {account.account_number} • {account.ifsc_code}
                </Text>
                {account.is_primary && (
                  <View style={styles.primaryBadge}>
                    <Text style={styles.primaryBadgeText}>Primary</Text>
                  </View>
                )}
              </View>
            ))}
            
            <TouchableOpacity
              style={styles.addButton}
              onPress={() => {
                setEditingBankIndex(null);
                setShowBankModal(true);
              }}
              activeOpacity={0.7}>
              <Icon name="add-circle-outline" size={20} color="#007AFF" />
              <Text style={styles.addButtonText}>Add Bank Account</Text>
            </TouchableOpacity>
          </>
        )}

        {/* Vendor Management */}
        {renderSection(
          'vendor',
          'Vendor Management',
          'business-outline',
          <>
            <View style={styles.infoBox}>
              <Icon name="information-circle" size={20} color="#007AFF" />
              <Text style={styles.infoText}>
                Configure vendor bill approval workflows. All fields are optional.
              </Text>
            </View>
            
            <View style={styles.switchGroup}>
              <View style={styles.switchRow}>
                <View style={styles.switchLabelContainer}>
                  <Text style={styles.switchLabel}>Require Vendor Approval</Text>
                  <Text style={styles.switchHint}>Require approval before processing vendor bills</Text>
                </View>
                <Switch
                  value={vendorApprovalRequired}
                  onValueChange={setVendorApprovalRequired}
                  trackColor={{false: '#D1D1D6', true: '#34C759'}}
                  thumbColor="#FFF"
                />
              </View>
            </View>
            
            {vendorApprovalRequired && (
              <View style={styles.inputGroup}>
                <Text style={styles.label}>Approval Workflow</Text>
                <View style={styles.radioGroup}>
                  <TouchableOpacity
                    style={styles.radioOption}
                    onPress={() => setVendorWorkflow('single')}
                    activeOpacity={0.7}>
                    <Icon
                      name={vendorWorkflow === 'single' ? 'radio-button-on' : 'radio-button-off'}
                      size={20}
                      color={vendorWorkflow === 'single' ? '#007AFF' : '#999'}
                    />
                    <Text style={styles.radioLabel}>Single Level</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={styles.radioOption}
                    onPress={() => setVendorWorkflow('multi_level')}
                    activeOpacity={0.7}>
                    <Icon
                      name={vendorWorkflow === 'multi_level' ? 'radio-button-on' : 'radio-button-off'}
                      size={20}
                      color={vendorWorkflow === 'multi_level' ? '#007AFF' : '#999'}
                    />
                    <Text style={styles.radioLabel}>Multi-Level</Text>
                  </TouchableOpacity>
                </View>
              </View>
            )}
          </>
        )}

        {/* Audit Trail */}
        {renderSection(
          'audit',
          'Audit Trail',
          'document-text-outline',
          <>
            <View style={styles.infoBox}>
              <Icon name="information-circle" size={20} color="#007AFF" />
              <Text style={styles.infoText}>
                Audit trail logs all actions for transparency and accountability. Recommended to keep enabled.
              </Text>
            </View>
            
            <View style={styles.switchGroup}>
              <View style={styles.switchRow}>
                <View style={styles.switchLabelContainer}>
                  <Text style={styles.switchLabel}>Enable Audit Trail</Text>
                  <Text style={styles.switchHint}>Log all actions and transactions</Text>
                </View>
                <Switch
                  value={auditTrailEnabled}
                  onValueChange={setAuditTrailEnabled}
                  trackColor={{false: '#D1D1D6', true: '#34C759'}}
                  thumbColor="#FFF"
                />
              </View>
            </View>
            
            {auditTrailEnabled && (
              <View style={styles.inputGroup}>
                <Text style={styles.label}>Retention Period (Days)</Text>
                <TextInput
                  style={styles.input}
                  placeholder="e.g., 2555 (7 years)"
                  value={auditRetentionDays}
                  onChangeText={setAuditRetentionDays}
                  keyboardType="number-pad"
                  placeholderTextColor="#999"
                />
                <Text style={styles.hint}>How long to retain audit logs</Text>
              </View>
            )}
          </>
        )}

        {/* Billing Settings */}
        {renderSection(
          'billing',
          'Billing Configuration',
          'receipt-outline',
          <>
            <View style={styles.infoBox}>
              <Icon name="information-circle" size={20} color="#007AFF" />
              <Text style={styles.infoText}>
                Configure billing cycles and automation. All fields are optional.
              </Text>
            </View>
            
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Billing Cycle</Text>
              <View style={styles.radioGroup}>
                {['monthly', 'quarterly', 'annual'].map(cycle => (
                  <TouchableOpacity
                    key={cycle}
                    style={styles.radioOption}
                    onPress={() => setBillingCycle(cycle)}
                    activeOpacity={0.7}>
                    <Icon
                      name={billingCycle === cycle ? 'radio-button-on' : 'radio-button-off'}
                      size={20}
                      color={billingCycle === cycle ? '#007AFF' : '#999'}
                    />
                    <Text style={styles.radioLabel}>
                      {cycle.charAt(0).toUpperCase() + cycle.slice(1)}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>
            
            <View style={styles.switchGroup}>
              <View style={styles.switchRow}>
                <View style={styles.switchLabelContainer}>
                  <Text style={styles.switchLabel}>Auto-Generate Bills</Text>
                  <Text style={styles.switchHint}>Automatically generate bills on cycle</Text>
                </View>
                <Switch
                  value={autoGenerateBills}
                  onValueChange={setAutoGenerateBills}
                  trackColor={{false: '#D1D1D6', true: '#34C759'}}
                  thumbColor="#FFF"
                />
              </View>
            </View>
            
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Bill Due Days</Text>
              <TextInput
                style={styles.input}
                placeholder="e.g., 7"
                value={billDueDays}
                onChangeText={setBillDueDays}
                keyboardType="number-pad"
                placeholderTextColor="#999"
              />
              <Text style={styles.hint}>Days after bill generation until due</Text>
            </View>
          </>
        )}

        {/* Member Settings */}
        {renderSection(
          'member',
          'Member Settings',
          'people-outline',
          <>
            <View style={styles.infoBox}>
              <Icon name="information-circle" size={20} color="#007AFF" />
              <Text style={styles.infoText}>
                Configure member ledger and tracking settings.
              </Text>
            </View>
            
            <View style={styles.switchGroup}>
              <View style={styles.switchRow}>
                <View style={styles.switchLabelContainer}>
                  <Text style={styles.switchLabel}>Bill-to-Bill Tracking</Text>
                  <Text style={styles.switchHint}>
                    Track individual bills and payments for each member
                  </Text>
                </View>
                <Switch
                  value={billToBillTracking}
                  onValueChange={setBillToBillTracking}
                  trackColor={{false: '#D1D1D6', true: '#34C759'}}
                  thumbColor="#FFF"
                />
              </View>
            </View>
          </>
        )}

        {/* Save Button */}
        <TouchableOpacity
          style={[styles.saveButton, saving && styles.saveButtonDisabled]}
          onPress={handleSave}
          disabled={saving}
          activeOpacity={0.8}>
          {saving ? (
            <ActivityIndicator size="small" color="#FFF" />
          ) : (
            <>
              <Icon name="checkmark-circle" size={24} color="#FFF" />
              <Text style={styles.saveButtonText}>Save All Settings</Text>
            </>
          )}
        </TouchableOpacity>
      </ScrollView>

      {/* Role Modal */}
      <Modal
        visible={showRoleModal}
        animationType="slide"
        transparent={true}
        onRequestClose={() => {
          setShowRoleModal(false);
          setEditingRole(null);
          setNewRoleName('');
          setNewRoleCode('');
          setNewRoleDescription('');
        }}>
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>
                {editingRole ? 'Edit Role' : 'Add Custom Role'}
              </Text>
              <TouchableOpacity
                onPress={() => {
                  setShowRoleModal(false);
                  setEditingRole(null);
                  setNewRoleName('');
                  setNewRoleCode('');
                  setNewRoleDescription('');
                }}
                style={styles.closeButton}>
                <Icon name="close" size={24} color="#666" />
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.modalBody}>
              <View style={styles.inputGroup}>
                <Text style={styles.label}>Role Name *</Text>
                <TextInput
                  style={styles.input}
                  placeholder="e.g., Chairman/President, Secretary"
                  value={newRoleName}
                  onChangeText={setNewRoleName}
                  placeholderTextColor="#999"
                />
                <Text style={styles.hint}>
                  Use flexible naming like "Chairman/President" if your society uses different terms
                </Text>
              </View>

              <View style={styles.inputGroup}>
                <Text style={styles.label}>Role Code *</Text>
                <TextInput
                  style={styles.input}
                  placeholder="e.g., chairman, secretary"
                  value={newRoleCode}
                  onChangeText={(text) => setNewRoleCode(text.toLowerCase().replace(/\s+/g, '_'))}
                  placeholderTextColor="#999"
                  editable={!editingRole?.is_system_role}
                />
                <Text style={styles.hint}>
                  Internal code (lowercase, no spaces). Cannot be changed for system roles.
                </Text>
              </View>

              <View style={styles.inputGroup}>
                <Text style={styles.label}>Description</Text>
                <TextInput
                  style={[styles.input, {height: 80, textAlignVertical: 'top'}]}
                  placeholder="Role description and responsibilities"
                  value={newRoleDescription}
                  onChangeText={setNewRoleDescription}
                  placeholderTextColor="#999"
                  multiline
                  numberOfLines={4}
                />
              </View>

              <TouchableOpacity
                style={styles.saveButton}
                onPress={handleSaveRole}
                activeOpacity={0.8}>
                <Icon name="checkmark-circle" size={24} color="#FFF" />
                <Text style={styles.saveButtonText}>
                  {editingRole ? 'Update Role' : 'Create Role'}
                </Text>
              </TouchableOpacity>
            </ScrollView>
          </View>
        </View>
      </Modal>

      {/* Bank Account Modal */}
      <BankAccountModal
        visible={showBankModal}
        account={editingBankIndex !== null ? bankAccounts[editingBankIndex] : null}
        onClose={() => {
          setShowBankModal(false);
          setEditingBankIndex(null);
        }}
        onSave={(accountData) => {
          if (editingBankIndex !== null) {
            const newAccounts = [...bankAccounts];
            newAccounts[editingBankIndex] = accountData;
            setBankAccounts(newAccounts);
          } else {
            setBankAccounts([...bankAccounts, accountData]);
          }
          setShowBankModal(false);
          setEditingBankIndex(null);
        }}
      />
    </View>
  );
};

// Bank Account Modal Component
const BankAccountModal = ({
  visible,
  account,
  onClose,
  onSave,
}: {
  visible: boolean;
  account: any;
  onClose: () => void;
  onSave: (data: any) => void;
}) => {
  const [accountName, setAccountName] = useState('');
  const [accountNumber, setAccountNumber] = useState('');
  const [bankName, setBankName] = useState('');
  const [ifscCode, setIfscCode] = useState('');
  const [branch, setBranch] = useState('');
  const [accountType, setAccountType] = useState('savings');
  const [isPrimary, setIsPrimary] = useState(false);

  React.useEffect(() => {
    if (account) {
      setAccountName(account.account_name || '');
      setAccountNumber(account.account_number || '');
      setBankName(account.bank_name || '');
      setIfscCode(account.ifsc_code || '');
      setBranch(account.branch || '');
      setAccountType(account.account_type || 'savings');
      setIsPrimary(account.is_primary || false);
    } else {
      setAccountName('');
      setAccountNumber('');
      setBankName('');
      setIfscCode('');
      setBranch('');
      setAccountType('savings');
      setIsPrimary(false);
    }
  }, [account, visible]);

  const handleSave = () => {
    if (!accountName || !accountNumber || !bankName || !ifscCode) {
      Alert.alert('Error', 'Please fill all required fields');
      return;
    }
    onSave({
      account_name: accountName,
      account_number: accountNumber,
      bank_name: bankName,
      ifsc_code: ifscCode,
      branch: branch || undefined,
      account_type: accountType,
      is_primary: isPrimary,
    });
  };

  return (
    <Modal visible={visible} animationType="slide" transparent={true} onRequestClose={onClose}>
      <View style={styles.modalOverlay}>
        <View style={styles.modalContent}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>
              {account ? 'Edit Bank Account' : 'Add Bank Account'}
            </Text>
            <TouchableOpacity onPress={onClose} style={styles.closeButton}>
              <Icon name="close" size={24} color="#666" />
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.modalBody}>
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Account Name *</Text>
              <TextInput
                style={styles.input}
                placeholder="e.g., Main Current Account"
                value={accountName}
                onChangeText={setAccountName}
                placeholderTextColor="#999"
              />
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.label}>Account Number *</Text>
              <TextInput
                style={styles.input}
                placeholder="Account number"
                value={accountNumber}
                onChangeText={setAccountNumber}
                keyboardType="number-pad"
                placeholderTextColor="#999"
              />
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.label}>Bank Name *</Text>
              <TextInput
                style={styles.input}
                placeholder="e.g., State Bank of India"
                value={bankName}
                onChangeText={setBankName}
                placeholderTextColor="#999"
              />
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.label}>IFSC Code *</Text>
              <TextInput
                style={styles.input}
                placeholder="e.g., SBIN0001234"
                value={ifscCode}
                onChangeText={setIfscCode}
                placeholderTextColor="#999"
                autoCapitalize="characters"
                maxLength={11}
              />
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.label}>Branch</Text>
              <TextInput
                style={styles.input}
                placeholder="Branch name"
                value={branch}
                onChangeText={setBranch}
                placeholderTextColor="#999"
              />
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.label}>Account Type</Text>
              <View style={styles.radioGroup}>
                {['savings', 'current', 'fd'].map(type => (
                  <TouchableOpacity
                    key={type}
                    style={styles.radioOption}
                    onPress={() => setAccountType(type)}
                    activeOpacity={0.7}>
                    <Icon
                      name={accountType === type ? 'radio-button-on' : 'radio-button-off'}
                      size={20}
                      color={accountType === type ? '#007AFF' : '#999'}
                    />
                    <Text style={styles.radioLabel}>
                      {type === 'fd' ? 'Fixed Deposit' : type.charAt(0).toUpperCase() + type.slice(1)}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            <View style={styles.switchGroup}>
              <View style={styles.switchRow}>
                <View style={styles.switchLabelContainer}>
                  <Text style={styles.switchLabel}>Primary Account</Text>
                  <Text style={styles.switchHint}>Use as default for transactions</Text>
                </View>
                <Switch
                  value={isPrimary}
                  onValueChange={setIsPrimary}
                  trackColor={{false: '#D1D1D6', true: '#34C759'}}
                  thumbColor="#FFF"
                />
              </View>
            </View>

            <TouchableOpacity style={styles.saveButton} onPress={handleSave} activeOpacity={0.8}>
              <Icon name="checkmark-circle" size={24} color="#FFF" />
              <Text style={styles.saveButtonText}>Save Bank Account</Text>
            </TouchableOpacity>
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F7',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F5F5F7',
  },
  loadingText: {
    marginTop: 12,
    fontSize: 16,
    color: '#666',
  },
  scrollView: {
    flex: 1,
  },
  section: {
    margin: 16,
    marginBottom: 12,
    backgroundColor: '#FFF',
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 2},
    shadowOpacity: 0.06,
    shadowRadius: 8,
    elevation: 2,
    overflow: 'hidden',
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
  },
  sectionHeaderLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1D1D1F',
  },
  sectionContent: {
    padding: 20,
    paddingTop: 0,
  },
  infoBox: {
    flexDirection: 'row',
    backgroundColor: '#E3F2FD',
    padding: 12,
    borderRadius: 8,
    marginBottom: 20,
    gap: 8,
  },
  infoText: {
    flex: 1,
    fontSize: 13,
    color: '#1D1D1F',
    lineHeight: 18,
  },
  inputGroup: {
    marginBottom: 20,
  },
  label: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1D1D1F',
    marginBottom: 8,
  },
  input: {
    borderWidth: 1.5,
    borderColor: '#E5E5EA',
    borderRadius: 12,
    padding: 14,
    fontSize: 16,
    backgroundColor: '#FAFAFA',
    color: '#1D1D1F',
  },
  hint: {
    fontSize: 12,
    color: '#8E8E93',
    marginTop: 6,
    fontStyle: 'italic',
  },
  optionContainer: {
    gap: 12,
  },
  optionCard: {
    flexDirection: 'row',
    borderWidth: 2,
    borderColor: '#E5E5EA',
    borderRadius: 12,
    padding: 16,
    gap: 12,
  },
  optionCardActive: {
    borderColor: '#007AFF',
    backgroundColor: '#E3F2FD',
  },
  optionContent: {
    flex: 1,
  },
  optionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1D1D1F',
    marginBottom: 4,
  },
  optionTitleActive: {
    color: '#007AFF',
  },
  optionDescription: {
    fontSize: 13,
    color: '#8E8E93',
    lineHeight: 18,
  },
  radioGroup: {
    flexDirection: 'row',
    gap: 20,
  },
  radioOption: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  radioLabel: {
    fontSize: 15,
    color: '#1D1D1F',
  },
  switchGroup: {
    marginBottom: 20,
  },
  switchRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  switchLabelContainer: {
    flex: 1,
    marginRight: 12,
  },
  switchLabel: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1D1D1F',
    marginBottom: 4,
  },
  switchHint: {
    fontSize: 13,
    color: '#8E8E93',
  },
  bankAccountCard: {
    backgroundColor: '#F5F5F7',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  bankAccountHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  bankAccountName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1D1D1F',
  },
  bankAccountActions: {
    flexDirection: 'row',
    gap: 12,
  },
  editButton: {
    padding: 4,
  },
  deleteButton: {
    padding: 4,
  },
  bankAccountDetails: {
    fontSize: 13,
    color: '#8E8E93',
  },
  primaryBadge: {
    alignSelf: 'flex-start',
    backgroundColor: '#007AFF',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    marginTop: 8,
  },
  primaryBadgeText: {
    fontSize: 11,
    fontWeight: '600',
    color: '#FFF',
  },
  addButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 2,
    borderColor: '#007AFF',
    borderStyle: 'dashed',
    borderRadius: 12,
    padding: 16,
    gap: 8,
  },
  addButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#007AFF',
  },
  emptyStateBox: {
    alignItems: 'center',
    padding: 40,
    backgroundColor: '#F5F5F7',
    borderRadius: 12,
    marginBottom: 20,
  },
  emptyStateText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#1D1D1F',
    marginTop: 16,
    marginBottom: 8,
  },
  emptyStateSubtext: {
    fontSize: 14,
    color: '#8E8E93',
    textAlign: 'center',
    marginBottom: 24,
  },
  initButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#007AFF',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 12,
    gap: 8,
  },
  initButtonText: {
    color: '#FFF',
    fontSize: 15,
    fontWeight: '600',
  },
  roleCard: {
    backgroundColor: '#F5F5F7',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  roleHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  roleHeaderLeft: {
    flex: 1,
    flexDirection: 'row',
    gap: 12,
  },
  roleBadge: {
    backgroundColor: '#007AFF',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    alignSelf: 'flex-start',
  },
  roleBadgeText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#FFF',
    textTransform: 'uppercase',
  },
  roleInfo: {
    flex: 1,
  },
  roleName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1D1D1F',
    marginBottom: 4,
  },
  roleCode: {
    fontSize: 12,
    color: '#8E8E93',
    fontFamily: 'monospace',
    marginBottom: 4,
  },
  roleDescription: {
    fontSize: 13,
    color: '#666',
    marginBottom: 8,
    lineHeight: 18,
  },
  roleUserCount: {
    fontSize: 12,
    color: '#8E8E93',
    fontStyle: 'italic',
  },
  roleActions: {
    flexDirection: 'row',
    gap: 8,
  },
  roleActionButton: {
    padding: 8,
  },
  roleStatusRow: {
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
  },
  warningBox: {
    flexDirection: 'row',
    backgroundColor: '#FFF3E0',
    padding: 16,
    borderRadius: 12,
    marginBottom: 20,
    borderWidth: 2,
    borderColor: '#FF9800',
    gap: 12,
  },
  warningContent: {
    flex: 1,
  },
  warningTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#FF9800',
    marginBottom: 8,
  },
  warningText: {
    fontSize: 13,
    color: '#1D1D1F',
    lineHeight: 20,
  },
  warningBold: {
    fontWeight: '700',
    color: '#F44336',
  },
  saveButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#007AFF',
    margin: 16,
    marginTop: 8,
    padding: 16,
    borderRadius: 16,
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 4},
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 4,
    gap: 8,
  },
  saveButtonDisabled: {
    backgroundColor: '#A0C4FF',
  },
  saveButtonText: {
    color: '#FFF',
    fontSize: 17,
    fontWeight: '700',
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#FFF',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '90%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E5EA',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1D1D1F',
  },
  closeButton: {
    padding: 4,
  },
  modalBody: {
    padding: 20,
  },
  logoPreview: {
    marginTop: 12,
    padding: 12,
    backgroundColor: '#F5F5F7',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#E5E5EA',
  },
  previewLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#666',
    marginBottom: 8,
  },
  logoPreviewImage: {
    width: '100%',
    height: 100,
    borderRadius: 8,
  },
});

export default SocietySettingsScreen;

