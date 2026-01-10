import React from 'react';
import {View, StyleSheet} from 'react-native';
import UnderDevelopment from '../../components/UnderDevelopment';

const ComplaintsScreen = () => {
  return (
    <View style={styles.container}>
      <UnderDevelopment
        featureName="Complaint Management"
        estimatedTime="Phase 6 (2-3 weeks)"
        message="The complaint/helpdesk system with ticket tracking and photo attachments is currently under development."
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

export default ComplaintsScreen;








