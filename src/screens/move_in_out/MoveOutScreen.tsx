import React from 'react';
import {View, StyleSheet} from 'react-native';
import UnderDevelopment from '../../components/UnderDevelopment';

const MoveOutScreen = () => {
  return (
    <View style={styles.container}>
      <UnderDevelopment
        featureName="Move-Out Request"
        estimatedTime="Phase 3 (4-5 weeks)"
        message="The Move-Out workflow with dues verification, complaint checks, and NOC generation is currently under development."
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F7',
  },
});

export default MoveOutScreen;








