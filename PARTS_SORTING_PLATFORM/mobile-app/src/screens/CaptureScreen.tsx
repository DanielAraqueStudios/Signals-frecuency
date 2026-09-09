import React, { useState } from "react";
import {
  View,
  Text,
  Image,
  Pressable,
  StyleSheet,
  ActivityIndicator,
  ScrollView,
} from "react-native";
import * as ImagePicker from "expo-image-picker";
import { uploadImage, ClassificationResult } from "../api/images";
import StubBadge from "../components/StubBadge";

// Design choice: expo-image-picker's launchCameraAsync (rather than a
// full expo-camera live-preview <CameraView>) — it handles the camera
// permission prompt and capture UI itself in one call, so there's no
// custom preview/shutter UI to get wrong without a device to test on.
// launchLibraryAsync is offered as a fallback for the simulator/no-camera
// case.
export default function CaptureScreen() {
  const [photoUri, setPhotoUri] = useState<string | null>(null);
  const [result, setResult] = useState<ClassificationResult | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function takePhoto() {
    setError(null);
    setResult(null);
    const permission = await ImagePicker.requestCameraPermissionsAsync();
    if (!permission.granted) {
      setError("Camera permission is required to capture a part.");
      return;
    }
    const capture = await ImagePicker.launchCameraAsync({
      quality: 0.7,
      allowsEditing: false,
    });
    if (!capture.canceled && capture.assets?.[0]) {
      setPhotoUri(capture.assets[0].uri);
    }
  }

  async function pickFromLibrary() {
    setError(null);
    setResult(null);
    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      setError("Photo library permission is required to pick a photo.");
      return;
    }
    const pick = await ImagePicker.launchImageLibraryAsync({
      quality: 0.7,
      allowsEditing: false,
    });
    if (!pick.canceled && pick.assets?.[0]) {
      setPhotoUri(pick.assets[0].uri);
    }
  }

  async function submitPhoto() {
    if (!photoUri) return;
    setIsUploading(true);
    setError(null);
    try {
      const classification = await uploadImage(photoUri);
      setResult(classification);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Upload failed — check your connection and try again."
      );
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Capture a Part</Text>

      <View style={styles.actionsRow}>
        <Pressable style={styles.button} onPress={takePhoto}>
          <Text style={styles.buttonText}>Take Photo</Text>
        </Pressable>
        <Pressable style={[styles.button, styles.secondaryButton]} onPress={pickFromLibrary}>
          <Text style={styles.buttonText}>Pick from Library</Text>
        </Pressable>
      </View>

      {photoUri && (
        <Image source={{ uri: photoUri }} style={styles.preview} resizeMode="cover" />
      )}

      {photoUri && (
        <Pressable
          style={[styles.button, styles.submitButton, isUploading && styles.buttonDisabled]}
          onPress={submitPhoto}
          disabled={isUploading}
        >
          {isUploading ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.buttonText}>Classify</Text>
          )}
        </Pressable>
      )}

      {error && <Text style={styles.error}>{error}</Text>}

      {result && (
        <View style={styles.resultCard}>
          <Text style={styles.resultLabel}>{result.label}</Text>
          <Text style={styles.resultConfidence}>
            Confidence:{" "}
            {result.confidence !== null
              ? `${(result.confidence * 100).toFixed(1)}%`
              : "n/a"}
          </Text>
          {result.reason && <Text style={styles.resultReason}>{result.reason}</Text>}
          <StubBadge stub={result.stub} />
        </View>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flexGrow: 1, padding: 24, backgroundColor: "#fff", alignItems: "center" },
  title: { fontSize: 24, fontWeight: "700", marginBottom: 20 },
  actionsRow: { flexDirection: "row", gap: 12, marginBottom: 20 },
  button: {
    backgroundColor: "#2563eb",
    borderRadius: 8,
    paddingVertical: 12,
    paddingHorizontal: 16,
    alignItems: "center",
  },
  secondaryButton: { backgroundColor: "#4b5563" },
  submitButton: { width: "100%", marginBottom: 16 },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { color: "#fff", fontSize: 15, fontWeight: "600" },
  preview: { width: "100%", height: 280, borderRadius: 12, marginBottom: 16 },
  error: { color: "#dc2626", marginBottom: 12, textAlign: "center" },
  resultCard: {
    width: "100%",
    borderWidth: 1,
    borderColor: "#e5e7eb",
    borderRadius: 12,
    padding: 16,
  },
  resultLabel: { fontSize: 20, fontWeight: "700" },
  resultConfidence: { fontSize: 14, color: "#374151", marginTop: 4 },
  resultReason: { fontSize: 13, color: "#6b7280", marginTop: 4, fontStyle: "italic" },
});
