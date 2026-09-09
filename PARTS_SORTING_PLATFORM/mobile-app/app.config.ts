import { ExpoConfig, ConfigContext } from "expo/config";

// Env vars read at build/start time. Defaults are obvious localhost
// placeholders so a misconfigured env fails loudly instead of silently
// pointing at a real service.
const API_GATEWAY_URL =
  process.env.API_GATEWAY_URL ?? "http://localhost:8000";
const AUTH_URL = process.env.AUTH_URL ?? "http://localhost:8001";

export default ({ config }: ConfigContext): ExpoConfig => ({
  ...config,
  name: "Parts Sorting",
  slug: "parts-sorting-mobile-app",
  version: "1.0.0",
  orientation: "portrait",
  userInterfaceStyle: "automatic",
  assetBundlePatterns: ["**/*"],
  ios: {
    supportsTablet: true,
    infoPlist: {
      NSCameraUsageDescription:
        "Camera access is used to photograph parts on the conveyor belt for classification.",
      NSPhotoLibraryUsageDescription:
        "Photo library access lets you pick an existing photo of a part to classify.",
    },
  },
  android: {
    permissions: ["CAMERA", "READ_EXTERNAL_STORAGE"],
  },
  plugins: [
    [
      "expo-camera",
      {
        cameraPermission:
          "Camera access is used to photograph parts on the conveyor belt for classification.",
      },
    ],
  ],
  extra: {
    apiGatewayUrl: API_GATEWAY_URL,
    authUrl: AUTH_URL,
  },
});
