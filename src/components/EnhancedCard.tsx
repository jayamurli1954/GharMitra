/**
 * Enhanced Card Component
 * Reusable card with consistent styling:
 * - Rounded corners (12-16px)
 * - Subtle shadows (elevation on Android, shadow on iOS)
 * - Consistent spacing (4px grid system)
 * - Press animations
 */
import React, {useRef} from 'react';
import {
  View,
  StyleSheet,
  TouchableOpacity,
  Animated,
  ViewStyle,
  Platform,
} from 'react-native';
import {spacing} from '../constants/spacing';

interface EnhancedCardProps {
  children: React.ReactNode;
  onPress?: () => void;
  style?: ViewStyle;
  borderRadius?: number; // 12 or 16
  padding?: number; // spacing value
  shadowIntensity?: 'light' | 'medium' | 'strong';
  disabled?: boolean;
}

export const EnhancedCard: React.FC<EnhancedCardProps> = ({
  children,
  onPress,
  style,
  borderRadius = 16,
  padding = spacing.lg,
  shadowIntensity = 'medium',
  disabled = false,
}) => {
  const scaleAnim = useRef(new Animated.Value(1)).current;

  const shadowStyles = {
    light: {
      shadowOpacity: 0.06,
      shadowRadius: 6,
      elevation: 2,
    },
    medium: {
      shadowOpacity: 0.1,
      shadowRadius: 12,
      elevation: 4,
    },
    strong: {
      shadowOpacity: 0.15,
      shadowRadius: 16,
      elevation: 6,
    },
  };

  const handlePressIn = () => {
    if (onPress && !disabled) {
      Animated.spring(scaleAnim, {
        toValue: 0.97,
        useNativeDriver: true,
        tension: 300,
        friction: 10,
      }).start();
    }
  };

  const handlePressOut = () => {
    if (onPress && !disabled) {
      Animated.spring(scaleAnim, {
        toValue: 1,
        useNativeDriver: true,
        tension: 300,
        friction: 10,
      }).start();
    }
  };

  const cardStyle = [
    styles.card,
    {
      borderRadius,
      padding,
      ...shadowStyles[shadowIntensity],
    },
    style,
    onPress && !disabled && {transform: [{scale: scaleAnim}]},
  ];

  if (onPress) {
    return (
      <Animated.View style={cardStyle}>
        <TouchableOpacity
          onPress={onPress}
          onPressIn={handlePressIn}
          onPressOut={handlePressOut}
          disabled={disabled}
          activeOpacity={1}
          style={styles.touchable}>
          {children}
        </TouchableOpacity>
      </Animated.View>
    );
  }

  return <View style={cardStyle}>{children}</View>;
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#FFF',
    shadowColor: '#000',
    shadowOffset: {width: 0, height: 4},
  },
  touchable: {
    flex: 1,
  },
});







