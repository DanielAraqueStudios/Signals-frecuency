import React from "react";
import { View, Text, StyleSheet } from "react-native";

/**
 * Marks a classification result that came from the classification-service's
 * stub mode (no trained model deployed yet) so it is never mistaken for a
 * real prediction. See classification-service/README for the stub contract.
 */
export default function StubBadge({ stub }: { stub: boolean }) {
  if (!stub) {
    return (
      <View style={[styles.badge, styles.real]}>
        <Text style={styles.text}>MODEL RESULT</Text>
      </View>
    );
  }
  return (
    <View style={[styles.badge, styles.stub]}>
      <Text style={styles.text}>PREVIEW / NOT A REAL MODEL YET</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  badge: {
    alignSelf: "flex-start",
    borderRadius: 6,
    paddingVertical: 4,
    paddingHorizontal: 8,
    marginTop: 6,
  },
  real: { backgroundColor: "#16a34a" },
  stub: { backgroundColor: "#d97706" },
  text: { color: "#fff", fontSize: 11, fontWeight: "700" },
});
