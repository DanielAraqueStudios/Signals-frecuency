import React from "react";
import { StatusBar } from "expo-status-bar";
import { NavigationContainer } from "@react-navigation/native";
import {
  createNativeStackNavigator,
  NativeStackScreenProps,
} from "@react-navigation/native-stack";
import { Pressable, Text, View, StyleSheet } from "react-native";

import { AuthProvider, useAuth } from "./src/context/AuthContext";
import LoginScreen from "./src/screens/LoginScreen";
import RegisterScreen from "./src/screens/RegisterScreen";
import CaptureScreen from "./src/screens/CaptureScreen";
import HistoryScreen from "./src/screens/HistoryScreen";

export type RootStackParamList = {
  Login: undefined;
  Register: undefined;
  Capture: undefined;
  History: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();

function LogoutButton() {
  const { logout } = useAuth();
  return (
    <Pressable onPress={logout} hitSlop={8}>
      <Text style={styles.logout}>Log out</Text>
    </Pressable>
  );
}

/** Minimal top-level tab switcher between Capture and History — kept as
 * a single stack screen rather than pulling in @react-navigation/bottom-tabs
 * to keep dependencies lean for this MVP. */
function LoggedInHome() {
  const [tab, setTab] = React.useState<"capture" | "history">("capture");
  return (
    <View style={styles.flex}>
      <View style={styles.tabBar}>
        <Pressable onPress={() => setTab("capture")} style={styles.tabButton}>
          <Text style={[styles.tabLabel, tab === "capture" && styles.tabLabelActive]}>
            Capture
          </Text>
        </Pressable>
        <Pressable onPress={() => setTab("history")} style={styles.tabButton}>
          <Text style={[styles.tabLabel, tab === "history" && styles.tabLabelActive]}>
            History
          </Text>
        </Pressable>
        <View style={styles.tabSpacer} />
        <LogoutButton />
      </View>
      {tab === "capture" ? <CaptureScreen /> : <HistoryScreen />}
    </View>
  );
}

function RootNavigator() {
  const { isLoggedIn, isLoading } = useAuth();

  if (isLoading) return null;

  if (isLoggedIn) {
    // A single "Home" entry hosting the Capture/History switcher — Capture
    // and History are gated behind isLoggedIn by never being reachable
    // from the logged-out stack below.
    return (
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        <Stack.Screen name="Capture" component={LoggedInHome} />
      </Stack.Navigator>
    );
  }

  return (
    <Stack.Navigator screenOptions={{ headerShown: false }}>
      <Stack.Screen name="Login" component={LoginScreen} />
      <Stack.Screen name="Register" component={RegisterScreen} />
    </Stack.Navigator>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <NavigationContainer>
        <StatusBar style="auto" />
        <RootNavigator />
      </NavigationContainer>
    </AuthProvider>
  );
}

export type { NativeStackScreenProps };

const styles = StyleSheet.create({
  flex: { flex: 1 },
  tabBar: {
    flexDirection: "row",
    alignItems: "center",
    paddingTop: 50,
    paddingBottom: 12,
    paddingHorizontal: 16,
    borderBottomWidth: 1,
    borderBottomColor: "#e5e7eb",
    gap: 20,
  },
  tabButton: { paddingVertical: 4 },
  tabLabel: { fontSize: 15, color: "#9ca3af", fontWeight: "600" },
  tabLabelActive: { color: "#2563eb" },
  tabSpacer: { flex: 1 },
  logout: { color: "#dc2626", fontSize: 14 },
});
