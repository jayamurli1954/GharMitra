import React, {useRef} from 'react';
import {TouchableOpacity, View, Text, StyleSheet, Animated} from 'react-native';
import MaterialIcon from 'react-native-vector-icons/MaterialCommunityIcons';
import {spacing} from '../constants/spacing';

interface AnimatedIconButtonProps {
  icon: string;
  label: string;
  iconColor: string;
  backgroundColor: string;
  onPress: () => void;
  badgeText?: string;
  disabled?: boolean;
  size?: number;
}

export const AnimatedIconButton: React.FC<AnimatedIconButtonProps> = ({
  icon,
  label,
  iconColor,
  backgroundColor,
  onPress,
  badgeText,
  disabled = false,
  size = 26,
}) => {
  const scaleAnim = useRef(new Animated.Value(1)).current;
  const opacityAnim = useRef(new Animated.Value(1)).current;

  const handlePressIn = () => {
    Animated.parallel([
      Animated.spring(scaleAnim, {
        toValue: 0.9,
        useNativeDriver: true,
        tension: 300,
        friction: 10,
      }),
      Animated.timing(opacityAnim, {
        toValue: 0.7,
        duration: 100,
        useNativeDriver: true,
      }),
    ]).start();
  };

  const handlePressOut = () => {
    Animated.parallel([
      Animated.spring(scaleAnim, {
        toValue: 1,
        useNativeDriver: true,
        tension: 300,
        friction: 10,
      }),
      Animated.timing(opacityAnim, {
        toValue: 1,
        duration: 100,
        useNativeDriver: true,
      }),
    ]).start();
  };

  return (
    <Animated.View
      style={[
        styles.container,
        {
          transform: [{scale: scaleAnim}],
          opacity: opacityAnim,
        },
        disabled && styles.disabled,
      ]}>
      <TouchableOpacity
        style={styles.button}
        onPress={onPress}
        onPressIn={handlePressIn}
        onPressOut={handlePressOut}
        disabled={disabled}
        activeOpacity={1}>
        <View style={[styles.iconWrapper, {backgroundColor}]}>
          <MaterialIcon name={icon} size={size} color={iconColor} />
        </View>
        <Text style={styles.label}>{label}</Text>
        {badgeText && (
          <View style={styles.badge}>
            <Text style={styles.badgeText}>{badgeText}</Text>
          </View>
        )}
      </TouchableOpacity>
    </Animated.View>
  );
};

const styles = StyleSheet.create({
  container: {
    alignItems: 'center',
    width: '30%',
    minWidth: 100,
  },
  button: {
    alignItems: 'center',
    backgroundColor: '#FFF',
    borderRadius: 16, // 16px rounded corners for modern look
    padding: spacing.lg, // Consistent spacing
    width: '100%',
    // Enhanced shadows: subtle on iOS, elevation on Android
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 4}, // Increased for better depth
    shadowOpacity: 0.1, // Slightly more visible
    shadowRadius: 12, // Softer shadow
    elevation: 4, // Android elevation
    position: 'relative',
  },
  iconWrapper: {
    width: 56,
    height: 56,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.sm,
  },
  label: {
    fontSize: 12,
    color: '#1D1D1F',
    textAlign: 'center',
    fontWeight: '500',
  },
  badge: {
    position: 'absolute',
    top: spacing.sm,
    right: spacing.sm,
    backgroundColor: '#FF9800',
    paddingHorizontal: spacing.xs + 2,
    paddingVertical: 2,
    borderRadius: 8,
  },
  badgeText: {
    color: '#FFF',
    fontSize: 9,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  disabled: {
    opacity: 0.6,
  },
});

