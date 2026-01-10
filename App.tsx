import React, {useEffect, useState, useRef, useCallback} from 'react';
import {NavigationContainer, NavigationContainerRef} from '@react-navigation/native';
import {createStackNavigator} from '@react-navigation/stack';
import {ActivityIndicator, View, StyleSheet, AppState} from 'react-native';

// Auth Service
import {authService, User} from './src/services/authService';

// Screens
import LoginScreen from './src/screens/auth/LoginScreen';
import RegisterScreen from './src/screens/auth/RegisterScreen';
import RegisterSocietyScreen from './src/screens/auth/RegisterSocietyScreen';
import MainTabNavigator from './src/navigation/MainTabNavigator';
import ResourceNavigator from './src/navigation/ResourceNavigator';
import PaymentScreen from './src/screens/payments/PaymentScreen';
import ComplaintsScreen from './src/screens/complaints/ComplaintsScreen';
import MoveInScreen from './src/screens/move_in_out/MoveInScreen';
import MoveOutScreen from './src/screens/move_in_out/MoveOutScreen';
import AdminGuidelinesScreen from './src/screens/admin/AdminGuidelinesScreen';
import FinancialYearScreen from './src/screens/settings/FinancialYearScreen';
import TermsScreen from './src/screens/legal/TermsScreen';
import PrivacyScreen from './src/screens/legal/PrivacyScreen';

const Stack = createStackNavigator();

const App = () => {
  const [initializing, setInitializing] = useState(true);
  const [user, setUser] = useState<User | null>(null);
  const navigationRef = useRef<NavigationContainerRef<any>>(null);
  const checkingAuthRef = useRef(false);
  const lastAppStateRef = useRef<string>(AppState.currentState);
  const lastCheckTimeRef = useRef<number>(0);

  // Memoized auth check function with guard to prevent concurrent calls
  const checkAuthStatus = useCallback(async () => {
    // Prevent concurrent auth checks
    if (checkingAuthRef.current) {
      return;
    }
    
    // Debounce: Don't check if last check was less than 1 second ago
    const now = Date.now();
    if (now - lastCheckTimeRef.current < 1000) {
      return;
    }
    lastCheckTimeRef.current = now;
    
    checkingAuthRef.current = true;
    setInitializing(true);
    
    try {
      const isAuthenticated = await authService.isAuthenticated();
      if (isAuthenticated) {
        // Try to get current user from backend
        try {
          const currentUser = await authService.getCurrentUser();
          setUser(currentUser);
        } catch (error) {
          // Token might be expired, clear it
          console.error('Failed to get current user:', error);
          await authService.logout();
          setUser(null);
        }
      } else {
        setUser(null);
      }
    } catch (error) {
      console.error('Auth check failed:', error);
      setUser(null);
    } finally {
      setInitializing(false);
      checkingAuthRef.current = false;
    }
  }, []);

  // Check authentication status on app load
  useEffect(() => {
    checkAuthStatus();
  }, [checkAuthStatus]);

  // Listen for app state changes to re-check auth (only when coming from background)
  useEffect(() => {
    const subscription = AppState.addEventListener('change', (nextAppState) => {
      // Only check auth when app becomes active from background (not on initial mount)
      if (nextAppState === 'active' && lastAppStateRef.current !== 'active') {
        checkAuthStatus();
      }
      lastAppStateRef.current = nextAppState;
    });
    return () => subscription?.remove();
  }, [checkAuthStatus]);

  if (initializing) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#007AFF" />
      </View>
    );
  }

  return (
    <NavigationContainer ref={navigationRef}>
      <Stack.Navigator screenOptions={{headerShown: false}}>
        {user ? (
          <>
            <Stack.Screen name="MainApp" component={MainTabNavigator} />
            <Stack.Screen
              name="ResourceCenter"
              component={ResourceNavigator}
              options={{headerShown: true}}
            />
            <Stack.Screen
              name="Payments"
              component={PaymentScreen}
              options={{headerShown: true, title: 'Payments'}}
            />
            <Stack.Screen
              name="Complaints"
              component={ComplaintsScreen}
              options={{headerShown: true, title: 'Complaints'}}
            />
            <Stack.Screen
              name="MoveIn"
              component={MoveInScreen}
              options={{headerShown: true, title: 'Move-In Request'}}
            />
            <Stack.Screen
              name="MoveOut"
              component={MoveOutScreen}
              options={{headerShown: true, title: 'Move-Out Request'}}
            />
            <Stack.Screen
              name="AdminGuidelines"
              component={AdminGuidelinesScreen}
              options={{headerShown: false}}
            />
            <Stack.Screen
              name="FinancialYear"
              component={FinancialYearScreen}
              options={{headerShown: true, title: 'Financial Years'}}
            />
            <Stack.Screen
              name="TermsOfService"
              component={TermsScreen}
              options={{headerShown: false}}
            />
            <Stack.Screen
              name="PrivacyPolicy"
              component={PrivacyScreen}
              options={{headerShown: false}}
            />
          </>
        ) : (
          <>
            <Stack.Screen name="Login">
              {(props) => <LoginScreen {...props} onLoginSuccess={checkAuthStatus} />}
            </Stack.Screen>
            <Stack.Screen name="Register" component={RegisterScreen} />
            <Stack.Screen name="RegisterSociety">
              {(props) => <RegisterSocietyScreen {...props} onRegistrationSuccess={checkAuthStatus} />}
            </Stack.Screen>
            <Stack.Screen
              name="TermsOfService"
              component={TermsScreen}
              options={{headerShown: false}}
            />
            <Stack.Screen
              name="PrivacyPolicy"
              component={PrivacyScreen}
              options={{headerShown: false}}
            />
          </>
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
};

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
  },
});

export default App;
