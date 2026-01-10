import React from 'react';
import {View, StyleSheet} from 'react-native';
import UnderDevelopment from '../../components/UnderDevelopment';

const MoveInScreen = () => {
  return (
    <View style={styles.container}>
      <UnderDevelopment
        featureName="Move-In Request"
        estimatedTime="Phase 3 (4-5 weeks)"
        message="The Move-In workflow with document upload, Aadhaar verification, and NOC generation is currently under development."
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

export default MoveInScreen;








